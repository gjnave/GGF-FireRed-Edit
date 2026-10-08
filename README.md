# GGF FireRed Edit

Edit an image with a written instruction and up to two optional reference images.
FireRed Image Edit 1.1 runs in an app-owned worker. The UI is Gradio; no separate
ComfyUI installation or server is required. The PC does the generation. The
optional phone view controls the PC through a browser.

## Windows setup

1. Extract the full customer ZIP. Keep `INSTALL.bat` beside `GGF-FireRed/`.
2. Install 64-bit Python 3.11 and a recent NVIDIA driver.
3. Run `INSTALL.bat`. It creates `GGF-FireRed/.venv`, installs CUDA PyTorch,
   and downloads the three pinned model files into `GGF-FireRed/models/`.
   Downloads resume if interrupted; the installer checks exact sizes and SHA-256 hashes.
4. Run `RUN.bat`. Local access starts on port 7866 or the next open port.

To update later, use Settings → Check for updates → Update and restart, or
close the app and run `UPDATE.bat`. Codeberg is the primary source with GitHub
as fallback. The host-generated repository archive contains code only; model
files, settings, and saved results stay on the PC.

The default FP8 diffusion model, BF16 Qwen 2.5 VL text encoder, and VAE total
about 38.3 GB on disk. Leave extra space for the Python environment and outputs.
Other quantizations from the supplied ComfyUI model manager are not automatic
downloads or selectable in this first standalone preview.

## Editing

Upload an image, describe the intended change, optionally add Picture 2 or 3
as references, and generate. Turbo previews use half the selected long edge.
Full-size results use the selected working edge. The optional resize control
scales the result back to input dimensions but does not add detail. Outputs use
unique filenames and are saved under `jobs/`.

This uses the FireRed 1.1 workflow's Qwen Edit Plus conditioning, AuraFlow
shift 3.1, CFGNorm strength 1, Euler/simple sampler, and default 40 steps/CFG 4.
There is no native mask input in the supplied workflow, so this first version
uses instruction-guided full-image editing. Editing may alter unrelated details.

## Phone access

Under Settings, choose local network or temporary public link, optionally set
a username/password, save, and restart RUN.bat. The local PC link has no login.
Blank remote password disables remote authentication. Public URLs are temporary.
The PC must stay on and running.

## Provenance

The FP8 model is published by [cocorang](https://huggingface.co/cocorang/FireRed-Image-Edit-1.1-FP8_And_BF16).
The text encoder and VAE come from [FireRedTeam](https://huggingface.co/FireRedTeam/FireRed-Image-Edit-1.1-ComfyUI).
The selected inference modules come from ComfyUI commit
`b0f4b7b294ce482a2e071d9d762c133d38c7aa07`, under GPLv3. See `NOTICE`,
`LICENSE`, and `vendor/comfy_core/SOURCE.md`. No model weights are bundled.

Validation status (2026-10-07): the extracted customer ZIP built the UI, loaded
the bundled core, loaded the model files, encoded an image and prompt, and
reached sampling. A full image output and speed measurement remain unverified
because the GPU was shared with another running app; do not infer speed or
edit quality from the package/startup checks alone.
