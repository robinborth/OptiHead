import torch
from torch.utils.data import Dataset
from torchvision.transforms import v2

from lib.model.flame import FLAME
from lib.rasterizer import Rasterizer
from lib.renderer.camera import Camera
from lib.renderer.renderer import Renderer
from lib.utils.loader import (
    load_color,
    load_depth,
    load_mediapipe_landmark_3d,
    load_normal,
    load_points_3d,
)


class DPHMDataset(Dataset):
    def __init__(
        self,
        # rasterizer settings
        camera: Camera,
        # dataset settings
        data_dir: str = "/data",
        optimize_frames: int = 1,
        start_frame_idx: int = 0,
        **kwargs,
    ):
        self.optimize_frames = optimize_frames
        self.start_frame_idx = start_frame_idx
        self.camera = camera
        self.data_dir = data_dir

    def iter_frame_idx(self):
        yield from range(
            self.start_frame_idx, self.start_frame_idx + self.optimize_frames
        )

    def load_landmarks(self):
        self.landmarks = []
        for frame_idx in self.iter_frame_idx():
            landmarks = load_mediapipe_landmark_3d(self.data_dir, idx=frame_idx)
            self.landmarks.append(landmarks)

    def load_color(self):
        self.color = []
        for frame_idx in self.iter_frame_idx():
            image = load_color(
                data_dir=self.data_dir,
                idx=frame_idx,
                return_tensor="pt",
            )  # (H, W, 3)
            image = v2.functional.resize(
                inpt=image.permute(2, 0, 1),
                size=(self.camera.height, self.camera.width),
            ).permute(1, 2, 0)
            self.color.append(image.to(torch.uint8))  # (H',W',3)

    def load_point(self):
        self.point = []
        self.mask = []
        for frame_idx in self.iter_frame_idx():
            depth = load_depth(
                data_dir=self.data_dir,
                idx=frame_idx,
                return_tensor="pt",
                smooth=True,
            )
            point, mask = self.camera.depth_map_transform(depth)
            self.point.append(point)
            self.mask.append(mask)

    def load_normal(self):
        self.normal = []
        for frame_idx in self.iter_frame_idx():
            normal = load_normal(
                data_dir=self.data_dir,
                idx=frame_idx,
                return_tensor="pt",
                smooth=True,
            )
            normal = v2.functional.resize(
                inpt=normal.permute(2, 0, 1),
                size=(self.camera.height, self.camera.width),
            ).permute(1, 2, 0)
            # to make them right-hand and follow camera space convention +X right +Y up
            # +Z towards the camera
            normal[:, :, 1] = -normal[:, :, 1]
            normal[:, :, 2] = -normal[:, :, 2]
            self.normal.append(normal)

    def __len__(self) -> int:
        return self.optimize_frames

    def __getitem__(self, idx: int):
        raise NotImplementedError()


class DPHMPointDataset(DPHMDataset):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_point()
        self.load_normal()
        self.load_landmarks()
        self.load_color()

    def __getitem__(self, idx: int):
        # (H', W', 3) this is scaled
        mask = self.mask[idx]
        point = self.point[idx]
        normal = self.normal[idx]
        color = self.color[idx]
        landmarks = self.landmarks[idx]
        return {
            "shape_idx": 0,
            "frame_idx": idx,
            "mask": mask,
            "point": point,
            "normal": normal,
            "color": color,
            "landmarks": landmarks,
        }


class FLAMEDataset(DPHMDataset):
    def __init__(
        self,
        flame_dir: str = "/flame",
        num_shape_params: int = 100,
        num_expression_params: int = 50,
        optimize_frames: int = 1,
        optimize_shapes: int = 1,
        vertices_mask: str = "face",
        rasterizer: Rasterizer | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs, optimize_frames=optimize_frames)

        flame = FLAME(
            flame_dir=flame_dir,
            num_shape_params=num_shape_params,
            num_expression_params=num_expression_params,
            optimize_frames=optimize_frames,
            optimize_shapes=optimize_shapes,
            vertices_mask=vertices_mask,
        ).to("cuda")
        flame.init_params_flame(0.0)
        vertices, landmarks = flame()

        renderer = Renderer(
            camera=self.camera,
            rasterizer=rasterizer,
            diffuse=[0.6, 0.0, 0.0],
            specular=[0.5, 0.0, 0.0],
        )
        render = renderer.render_full(vertices, flame.masked_faces(vertices))
        self.mask = render["mask"][0].detach().cpu().numpy()
        self.point = render["point"][0].detach().cpu().numpy()
        self.normal = render["normal"][0].detach().cpu().numpy()
        self.color = render["shading_image"][0].detach().cpu().numpy()
        self.color[~self.mask, :] = 255
        self.landmarks = landmarks[0].detach().cpu().numpy()

    def __getitem__(self, idx: int):
        return {
            "shape_idx": 0,
            "frame_idx": 0,
            "mask": self.mask,
            "point": self.point,
            "normal": self.normal,
            "color": self.color,
            "landmarks": self.landmarks,
        }
