import importlib
from dataclasses import dataclass

import torch
from torch.utils.cpp_extension import load

# # loads the rasterizer module in cpp
plugin_name = "rasterizer_plugin"
rasterizer = load(
    name=plugin_name,
    sources=[
        "lib/rasterizer/gl_context.cpp",
        "lib/rasterizer/gl_rasterizer.cpp",
        "lib/rasterizer/gl_shader.cpp",
        "lib/rasterizer/gl_utils.cpp",
        "lib/rasterizer/torch_bindings.cpp",
        "lib/rasterizer/torch_utils.cpp",
    ],
    extra_cflags=["-g"],
    extra_ldflags=["-lEGL", "-lGL"],
    verbose=True,
)
plugin = importlib.import_module(plugin_name)


@dataclass
class Fragments:
    pix_to_face: torch.Tensor
    bary_coords: torch.Tensor


class Rasterizer:
    def __init__(self, width: int, height: int):
        cudaDeviceIdx = torch.cuda.current_device()
        self.glctx = plugin.GLContext(width, height, cudaDeviceIdx)

    def rasterize(self, vertices: torch.Tensor, indices: torch.Tensor) -> Fragments:
        """Rendering of the attributes with mesh rasterization.

        The interface of the python function.

        Args:
            faces (torch.Tensor): The indexes of the vertices, e.g. the faces (F, 3)
            vertices (torch.Tensor): The vertices in camera coordinate system (B, V, 3)

        Returns:
            (Fragments) A fragments object of pix_to_face cordinates of dim
            (B, H, W) and the coresponding bary coordinates of dim (B, H, W, 3).
        """
        assert len(vertices.shape) == 3  # (B, V, 3)
        assert len(indices.shape) == 2  # (F, 3)
        assert vertices.is_cuda
        assert vertices.device == indices.device

        # cast the dtypes to the ones that are needed as input
        vertices = vertices.to(torch.float32)
        indices = indices.to(torch.uint32)

        # loop over the batch this needs to be changed
        _bary_coords: list[torch.Tensor] = []
        _pix_to_face: list[torch.Tensor] = []
        for _vertices in vertices:
            f = plugin.rasterize(self.glctx, _vertices, indices)
            assert len(f.bary_coords.shape) == 3  # (H, W, 3)
            assert len(f.pix_to_face.shape) == 2  # (H, W)
            _bary_coords.append(f.bary_coords)
            _pix_to_face.append(f.pix_to_face)
        bary_coords = torch.stack(_bary_coords, dim=0)
        pix_to_face = torch.stack(_pix_to_face, dim=0)
        assert len(bary_coords.shape) == 4  # (B, H, W, 3)
        assert len(pix_to_face.shape) == 3  # (B, H, W)

        return Fragments(pix_to_face=pix_to_face, bary_coords=bary_coords)