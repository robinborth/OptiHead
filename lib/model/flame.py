from pathlib import Path

import lightning as L
import numpy as np
import torch
import torch.nn as nn
from lightning.pytorch.utilities import grad_norm
from PIL import Image

from lib.model.lbs import lbs
from lib.model.loss import point_to_point
from lib.model.utils import load_flame
from lib.renderer.renderer import Renderer
from lib.utils.logger import create_logger

log = create_logger("flame")


class FLAME(L.LightningModule):
    def __init__(
        self,
        # model settings
        flame_dir: str = "/flame",
        num_shape_params: int = 100,
        num_expression_params: int = 50,
        # optimization settings
        # TODO optimize_frames: int = 1,
        lr: float = 1e-03,
        scheduler=None,
        renderer=None,
    ):

        super().__init__()
        self.save_hyperparameters(logger=False, ignore=["renderer"])

        # load the face model
        flame_model = load_flame(flame_dir=flame_dir, return_tensors="pt")

        # load the faces, mean vertices and pca bases
        self.faces = nn.Parameter(flame_model["f"], requires_grad=False)  # (9976, 3)
        self.v_template = nn.Parameter(flame_model["v_template"])  # (5023, 3)
        self.shapedirs = nn.Parameter(flame_model["shapedirs"])  # (5023, 3, 400)

        # shape parameters
        zero_shape = torch.zeros(300 - num_shape_params)
        self.zero_shape = nn.Parameter(zero_shape)
        shape_params = torch.zeros(num_shape_params)
        self.shape_params = nn.Parameter(shape_params)

        # expression parameters
        zero_expression = torch.zeros(100 - num_expression_params)
        self.zero_expression = nn.Parameter(zero_expression)
        expression_params = torch.zeros(num_expression_params)
        self.expression_params = nn.Parameter(expression_params)

        # pose parameters
        self.global_pose = nn.Parameter(torch.tensor([torch.pi, 0.0, 0.0]))
        self.neck_pose = nn.Parameter(torch.zeros(3))
        self.jaw_pose = nn.Parameter(torch.zeros(3))
        self.eye_pose = nn.Parameter(torch.zeros(6))

        # translation and scale pose
        self.transl = nn.Parameter(torch.zeros(3))
        self.scale = nn.Parameter(torch.ones(3))

        # linear blend skinning
        self.J_regressor = nn.Parameter(flame_model["J_regressor"])  # (5, 5023)
        self.lbs_weights = nn.Parameter(flame_model["weights"])  # (5023, 5)
        num_pose_basis = flame_model["posedirs"].shape[-1]  # (5023, 3, 36)
        posedirs = flame_model["posedirs"].reshape(-1, num_pose_basis).T
        self.posedirs = nn.Parameter(posedirs)  # (36, 5023 * 3)
        # indices of parents for each joints
        parents = flame_model["kintree_table"]  # (2, 5)
        parents[0, 0] = -1  # [-1, 0, 1, 1, 1]
        self.parents = nn.Parameter(parents[0], requires_grad=False)  # (5,)

        # visualization/debugging
        if renderer is None:
            log.info("FLAME model does not have a renderer specified!")
        self.renderer = renderer

    def forward(
        self,
        shape_params=None,
        expression_params=None,
        global_pose=None,
        neck_pose=None,
        jaw_pose=None,
        eye_pose=None,
        transl=None,
        scale=None,
    ):
        """The forward pass the FLAME model.

        The vertices of the FLAME model are in world space. Hence the translation and
        the scaling are in world space.

        TODO: Output 3D facial landmarks

        Args:
            shape_params (torch.tensor): self.hparams["shape_params"]
            expression_params (torch.tensor): self.hparams["expression_params"]
            global_pose (torch.tensor): number of global pose parameters (3,)
            neck_pose (torch.tensor): number of neck pose parameters (3,)
            jaw_pose (torch.tensor): number of jaw pose parameters (3,)
            eye_pose (torch.tensor): number of eye pose parameters (6,)
            transl_pose (torch.tensor): number of eye pose parameters (3,)

        Return:
            (torch.Tensor): The mesh vertices of dim (V, 3)
        """
        # create the shape parameters
        shape_params = shape_params if shape_params is not None else self.shape_params
        shape = torch.cat([shape_params, self.zero_shape])  # (300, )
        # create the expression parameters
        expression_params = (
            expression_params
            if expression_params is not None
            else self.expression_params
        )
        expression = torch.cat([expression_params, self.zero_expression])  # (100, )
        # create the betas merged with shape and expression
        betas = torch.cat([shape, expression])

        # create the pose merged with global, jaw, neck and left/right eye
        global_pose = global_pose if global_pose is not None else self.global_pose
        jaw_pose = jaw_pose if jaw_pose is not None else self.jaw_pose
        neck_pose = neck_pose if neck_pose is not None else self.neck_pose
        eye_pose = eye_pose if eye_pose is not None else self.eye_pose
        pose = torch.cat([global_pose, neck_pose, jaw_pose, eye_pose], dim=-1)  # (15,)

        # the translation and scaling of the vertices in world space
        transl = transl if transl is not None else self.transl
        scale = scale if scale is not None else self.scale

        # apply the linear blend skinning model
        vertices, _ = lbs(
            betas.unsqueeze(0),
            pose.unsqueeze(0),
            self.v_template.unsqueeze(0),
            # weights/settings of the lbs model
            self.shapedirs,
            self.posedirs,
            self.J_regressor,
            self.parents,
            self.lbs_weights,
        )
        vertices = vertices[0]

        # apply the translation and the scaling
        vertices += transl
        # vertices *= scale

        return vertices

    def training_step(self, batch, batch_idx):
        points = batch["points"]  # (B, P, 3)
        vertices = self.forward()  # (V, 3)
        p2p_loss = point_to_point(vertices=vertices.unsqueeze(0), points=points).mean()
        self.log("train/p2p_loss", p2p_loss, on_step=True, on_epoch=True, prog_bar=True)

        # visualize the image that is optimized and save to disk
        save_interval = 50
        batch_idx = 0
        if self.current_epoch % save_interval == 0:
            # extract the image
            image = batch["image"][batch_idx].detach().cpu()  # (H, W, 3)
            frame_idx = batch["frame_idx"][batch_idx].detach().cpu()
            # render the mesh in the image space
            flame_image = self.renderer.render_color_image(
                vertices=vertices.detach().cpu(),
                faces=self.faces.detach().cpu(),
                image=image,
            )
            # save the image
            file_name = f"image/{frame_idx:03}_{self.current_epoch:05}.png"
            path = Path(self.logger.save_dir) / file_name
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(flame_image.detach().cpu().numpy()).save(path)

            file_name = f"pcd_vertices/{frame_idx:03}_{self.current_epoch:05}.npz"
            path = Path(self.logger.save_dir) / file_name
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                np.save(f, vertices.detach().cpu().numpy())

            file_name = f"pcd_points/{frame_idx:03}_{self.current_epoch:05}.npz"
            path = Path(self.logger.save_dir) / file_name
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                np.save(f, points[0].detach().cpu().numpy())

        return p2p_loss

    def configure_optimizers(self):
        # TODO callback for finetuning
        pose_params = [self.global_pose, self.transl]
        optimizer = torch.optim.Adam(pose_params, lr=self.hparams["lr"])
        if self.hparams["scheduler"] is not None:
            scheduler = self.hparams["scheduler"](optimizer=optimizer)
            return {
                "optimizer": optimizer,
                "lr_scheduler": {"scheduler": scheduler, "monitor": "train/loss"},
            }
        return {"optimizer": optimizer}

    # def on_before_optimizer_step(self, optimizer):
    #     print("global_pose", torch.norm(self.global_pose.grad))
    #     print("transl", torch.norm(self.transl.grad), self.transl.data)
