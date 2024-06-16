import logging

import hydra
import lightning as L
import torch
from omegaconf import DictConfig
from tqdm import tqdm

from lib.data.datamodule import DPHMDataModule
from lib.data.scheduler import CoarseToFineScheduler, FinetuneScheduler
from lib.model.flame import FLAME
from lib.model.logger import FlameLogger
from lib.model.loss import calculate_point2plane
from lib.optimizer.gauss_newton import GaussNewton

log = logging.getLogger()


@hydra.main(version_base=None, config_path="../conf", config_name="optimize")
def optimize(cfg: DictConfig) -> None:
    log.info("==> loading config ...")
    L.seed_everything(cfg.seed)
    torch.set_float32_matmul_precision("medium")  # using CUDA device RTX A400
    device = "cuda" if torch.cuda.is_available() else "cpu"
    assert device == "cuda"

    log.info(f"==> initializing datamodule <{cfg.data._target_}>")
    datamodule: DPHMDataModule = hydra.utils.instantiate(cfg.data, devie=device)
    datamodule.setup()  # this now contains the intrinsics, camera and rasterizer

    log.info(f"==> initializing model <{cfg.model._target_}>")
    model: FLAME = hydra.utils.instantiate(cfg.model)
    model.init_renderer(camera=datamodule.camera, rasterizer=datamodule.rasterizer)
    model = model.to(device)

    log.info("==> initializing scheduler ...")
    fts: FinetuneScheduler = hydra.utils.instantiate(cfg.scheduler.finetune)
    c2fs: CoarseToFineScheduler = hydra.utils.instantiate(cfg.scheduler.coarse2fine)

    log.info("==> initializing logger ...")
    logger: FlameLogger = hydra.utils.instantiate(cfg.logger)
    logger.init_logger(model=model, cfg=cfg)

    fts.freeze(model)
    for iter_step in tqdm(range(cfg.trainer.max_iters)):  # outer loop
        # prepare iteration
        logger.iter_step = iter_step

        # fetch single batch
        c2fs.schedule_dataset(datamodule=datamodule, iter_step=iter_step)
        dataloader = datamodule.train_dataloader()
        batch = next(iter(dataloader))

        # create optimizer
        optimizer = fts.configure_adam(
            model=model,
            batch=batch,
            iter_step=iter_step,
            copy_state=True,
        )
        optimizer.zero_grad()

        # find correspondences
        with torch.no_grad():
            correspondences = model.correspondence_step(batch)

            def jacobian_closure():
                return model.jacobian(batch=batch, correspondences=correspondences)

        # optimization
        for optim_step in range(cfg.trainer.max_optims):
            logger.optim_step = optim_step
            logger.global_step = iter_step * cfg.trainer.max_optims + optim_step + 1

            optimizer.zero_grad()
            loss = model.loss_step(batch=batch, correspondences=correspondences)
            loss.backward()
            logger.log("loss/point2plane", loss)
            logger.log(f"loss/{iter_step:03}/point2plane", loss)
            logger.log_gradients(optimizer)

            if fts.requires_jacobian(optimizer):
                optimizer.step(closure=jacobian_closure)
            else:
                optimizer.step()

        # debug and logging
        logger.log_metrics(batch=batch, model=correspondences)
        if (iter_step % cfg.trainer.save_interval) == 0:
            logger.log_3d_points(batch=batch, model=correspondences)
            logger.log_render(batch=batch, model=correspondences)
            logger.log_input_batch(batch=batch, model=correspondences)
            logger.log_loss(batch=batch, model=correspondences)
            if model.init_mode == "flame":
                model.debug_params(batch=batch)

    # final full screen image
    log.info("==> log final result ...")
    logger.log_full_screen(datamodule=datamodule, model=model)
    logger.log_video("render_normal", framerate=20)
    logger.log_video("render_merged", framerate=20)
    logger.log_video("error_point_to_plane", framerate=20)
    logger.log_video("batch_color", framerate=20)


if __name__ == "__main__":
    optimize()
