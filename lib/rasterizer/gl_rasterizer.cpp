#include "gl_rasterizer.h"
#include "gl_utils.h"
#include "gl_context.h"
#include "gl_shader.h"
#include "torch_utils.h"

#include <GLES3/gl3.h>
#include <ATen/cuda/CUDAContext.h>
#include <ATen/cuda/CUDAUtils.h>
#include <c10/cuda/CUDAGuard.h>
#include <cuda_gl_interop.h>
#include <iostream>

Shader initShader()
{
    const char *vShaderCode = "#version 460 core\n" STRINGIFY_SHADER_SOURCE(
        layout(location = 0) in vec4 aPos;

        out VS_OUT {
            vec3 bary;
        } vs_out;

        void main() {
            gl_Position = aPos;
            vs_out.bary = vec3(0.0, 0.0, 0.0);
        });

    const char *gShaderCode = "#version 460 core\n" STRINGIFY_SHADER_SOURCE(
        layout(triangles) in;
        layout(triangle_strip, max_vertices = 3) out;

        in VS_OUT {
            vec3 bary;
        } gs_in[];

        out VS_OUT {
            vec3 bary;
        } gs_out;

        void main() {
            gs_out.bary = vec3(1.0, 0.0, 0.0);
            gl_Position = gl_in[0].gl_Position;
            EmitVertex();
            gs_out.bary = vec3(0.0, 1.0, 0.0);
            gl_Position = gl_in[1].gl_Position;
            EmitVertex();
            gs_out.bary = vec3(0.0, 0.0, 1.0);
            gl_Position = gl_in[2].gl_Position;
            EmitVertex();
            EndPrimitive();
        });

    const char *fShaderCode = "#version 460 core\n" STRINGIFY_SHADER_SOURCE(
        layout(location = 0) out vec4 gBary;
        // layout(location = 1) out int gPrimitiveID;

        in VS_OUT {
            vec3 bary;
        } fs_in;

        void main() {
            gBary = vec4(fs_in.bary, 1.0);
            // gPrimitiveID = gl_PrimitiveID;
        });
    Shader shader(vShaderCode, gShaderCode, fShaderCode);
    return shader;
}

torch::Tensor rasterize(torch::Tensor vertices, torch::Tensor indices, int width, int height, int cudaDeviceIdx)
{
    // set the current opengl context
    GLContext glctx;
    glctx.width = width;
    glctx.height = height;
    glctx.cudaDeviceIdx = cudaDeviceIdx;
    initContext(glctx);

    // define the rasterization state
    RasterizeGLState s;
    s.vertexCount = vertices.numel();
    s.vertexPtr = vertices.data_ptr<float>();
    s.elementCount = indices.numel();
    s.elementPtr = indices.data_ptr<uint32_t>();
    GL_CHECK_ERROR(glGenFramebuffers(1, &s.glFBO));
    GL_CHECK_ERROR(glGenVertexArrays(1, &s.glVAO));
    GL_CHECK_ERROR(glGenBuffers(1, &s.glVBO));
    GL_CHECK_ERROR(glGenBuffers(1, &s.glEBO));
    GL_CHECK_ERROR(glGenTextures(1, &s.glOutBary));

    // access the current cuda stream that is used in pytorch
    const at::cuda::OptionalCUDAGuard device_guard(device_of(vertices));
    cudaStream_t stream = at::cuda::getCurrentCUDAStream();

    // initilize the shader
    Shader shader = initShader();

    // enable the vertex attribute object
    GL_CHECK_ERROR(glBindVertexArray(s.glVAO));
    // // vertex data is on CPU -> allocate memory on the GPU
    // GL_CHECK_ERROR(glBindBuffer(GL_ARRAY_BUFFER, s.glVBO));
    // GL_CHECK_ERROR(glBufferData(GL_ARRAY_BUFFER, s.vertexCount * sizeof(float), s.vertexPtr, GL_STATIC_DRAW));
    // GL_CHECK_ERROR(glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void *)0));
    // vertex data is on GPU -> copy data to the GPU
    GL_CHECK_ERROR(glBindBuffer(GL_ARRAY_BUFFER, s.glVBO));
    void *glVertexPtr = nullptr;
    size_t vertexBytes = 0;
    GL_CHECK_ERROR(glBufferData(GL_ARRAY_BUFFER, s.vertexCount * sizeof(float), nullptr, GL_DYNAMIC_DRAW));
    GL_CHECK_ERROR(glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 4 * sizeof(float), 0));
    CUDA_CHECK_ERROR(cudaGraphicsGLRegisterBuffer(&s.cudaVBO, s.glVBO, cudaGraphicsRegisterFlagsWriteDiscard));
    CUDA_CHECK_ERROR(cudaGraphicsMapResources(1, &s.cudaVBO, stream));
    CUDA_CHECK_ERROR(cudaGraphicsResourceGetMappedPointer(&glVertexPtr, &vertexBytes, s.cudaVBO));
    CUDA_CHECK_ERROR(cudaMemcpyAsync(glVertexPtr, s.vertexPtr, s.vertexCount * sizeof(float), cudaMemcpyDeviceToDevice, stream));
    CUDA_CHECK_ERROR(cudaGraphicsUnmapResources(1, &s.cudaVBO, stream));
    GL_CHECK_ERROR(glEnableVertexAttribArray(0));
    // // element data is on CPU -> allocate memory on the GPU
    // GL_CHECK_ERROR(glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, s.glEBO));
    // GL_CHECK_ERROR(glBufferData(GL_ELEMENT_ARRAY_BUFFER, s.elementCount * sizeof(uint32_t), s.elementPtr, GL_STATIC_DRAW));
    // element data is on CPU -> allocate memory on the GPU
    GL_CHECK_ERROR(glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, s.glEBO));
    void *glElementPtr = nullptr;
    size_t elementBytes = 0;
    GL_CHECK_ERROR(glBufferData(GL_ELEMENT_ARRAY_BUFFER, s.elementCount * sizeof(uint32_t), nullptr, GL_DYNAMIC_DRAW));
    CUDA_CHECK_ERROR(cudaGraphicsGLRegisterBuffer(&s.cudaEBO, s.glEBO, cudaGraphicsRegisterFlagsWriteDiscard));
    CUDA_CHECK_ERROR(cudaGraphicsMapResources(1, &s.cudaEBO, stream));
    CUDA_CHECK_ERROR(cudaGraphicsResourceGetMappedPointer(&glElementPtr, &elementBytes, s.cudaEBO));
    CUDA_CHECK_ERROR(cudaMemcpyAsync(glElementPtr, s.elementPtr, s.elementCount * sizeof(uint32_t), cudaMemcpyDeviceToDevice, stream));
    CUDA_CHECK_ERROR(cudaGraphicsUnmapResources(1, &s.cudaEBO, stream));
    // unbind the vertex array
    GL_CHECK_ERROR(glBindVertexArray(0));

    // bind the framebuffer
    GL_CHECK_ERROR(glBindFramebuffer(GL_FRAMEBUFFER, s.glFBO));
    GL_CHECK_ERROR(glBindTexture(GL_TEXTURE_2D, s.glOutBary));
    GL_CHECK_ERROR(glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, glctx.width, glctx.height, 0, GL_RGBA, GL_FLOAT, nullptr));
    GL_CHECK_ERROR(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST));
    GL_CHECK_ERROR(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST));
    GL_CHECK_ERROR(glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, s.glOutBary, 0));
    // add attachments to the framebuffer
    unsigned int attachments[1] = {GL_COLOR_ATTACHMENT0};
    GL_CHECK_ERROR(glDrawBuffers(1, attachments));
    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE)
        std::cout << "ERROR FRAMEBUFFER NOT COMPLETE" << std::endl;
    // unbind the framebuffer
    GL_CHECK_ERROR(glBindTexture(GL_TEXTURE_2D, 0));
    GL_CHECK_ERROR(glBindFramebuffer(GL_FRAMEBUFFER, 0));

    // rasterizes the vertices using opengl
    shader.use();
    GL_CHECK_ERROR(glBindFramebuffer(GL_FRAMEBUFFER, s.glFBO));
    GL_CHECK_ERROR(glClearColor(1.0f, 1.0f, 0.0f, 1.0f));
    GL_CHECK_ERROR(glClear(GL_COLOR_BUFFER_BIT));
    GL_CHECK_ERROR(glBindVertexArray(s.glVAO));
    GL_CHECK_ERROR(glDrawElements(GL_TRIANGLES, s.elementCount, GL_UNSIGNED_INT, 0));
    // GL_CHECK_ERROR(glDrawArrays(GL_TRIANGLES, 0, 3));

    // allocate output tensors.
    torch::TensorOptions opts = torch::TensorOptions().dtype(torch::kFloat32).device(torch::kCUDA);
    torch::Tensor out = torch::empty({glctx.height, glctx.width, 4}, opts);
    float *outputPtr = out.data_ptr<float>();
    // register to cuda
    cudaArray_t cudaOut = 0;
    CUDA_CHECK_ERROR(cudaGraphicsGLRegisterImage(&s.cudaOutBary, s.glOutBary, GL_TEXTURE_2D, cudaGraphicsRegisterFlagsReadOnly));
    CUDA_CHECK_ERROR(cudaGraphicsMapResources(1, &s.cudaOutBary, stream));
    CUDA_CHECK_ERROR(cudaGraphicsSubResourceGetMappedArray(&cudaOut, s.cudaOutBary, 0, 0));
    // perform the asynchronous copy
    CUDA_CHECK_ERROR(cudaMemcpy2DFromArrayAsync(
        outputPtr,                       // Destination pointer
        glctx.width * 4 * sizeof(float), // Destination pitch
        cudaOut,                         // Source array
        0, 0,                            // Offset in the source array
        glctx.width * 4 * sizeof(float), // Width of the 2D region to copy in bytes
        glctx.height,                    // Height of the 2D region to copy in rows
        cudaMemcpyDeviceToDevice,        // Copy kind
        stream));
    CUDA_CHECK_ERROR(cudaGraphicsUnmapResources(1, &s.cudaOutBary, stream));
    CUDA_CHECK_ERROR(cudaGraphicsUnregisterResource(s.cudaOutBary));

    // destroy the context
    destroyContext(glctx);
    // return the tensor
    return out;
}

// void rasterizeCopyResults(cudaGraphicsResource_t *cudaColorBuffer, cudaStream_t stream, float *outputPtr, int width, int height)
// {
//     // Copy color buffers to output tensors.
//     cudaArray_t array = 0;
//     cudaGraphicsMapResources(1, cudaColorBuffer, stream);
//     cudaGraphicsSubResourceGetMappedArray(&array, *cudaColorBuffer, 0, 0);
//     cudaMemcpy3DParms p = {0};
//     p.srcArray = array;
//     p.dstPtr.ptr = outputPtr;
//     p.dstPtr.pitch = width * 4 * sizeof(float);
//     p.dstPtr.xsize = width;
//     p.dstPtr.ysize = height;
//     p.extent.width = width;
//     p.extent.height = height;
//     p.kind = cudaMemcpyDeviceToDevice;
//     cudaMemcpy3DAsync(&p, stream);
//     cudaGraphicsUnmapResources(1, cudaColorBuffer, stream);
// }