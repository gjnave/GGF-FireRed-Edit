# GGF FireRed Edit handoff

- Product source: `D:\apps2review\FireRed\GGF-FireRed`
- Customer launchers: `D:\apps2review\FireRed\INSTALL.bat` and `RUN.bat`
- Source asset: user-supplied `FireRed1.1-Image-Edit-Model-Manager (1).zip`
- GGF style reference: `D:\apps2review\GGF-APP-BUILD-GUIDE.md`
- Live product page to update after real inference: `https://getgoingfast.pro/tools/firered/`
- This is the general image editor; do not turn it into a head swap product.
- The supplied Comfy workflow has no native mask editing path. Keep masks out of
  the customer flow until a tested FireRed conditioning path is available.
- Default models: one cocorang FP8 checkpoint, official Qwen 2.5 VL BF16 text
  encoder, official Qwen image VAE; pinned sources in `model_sources.json`.
- No ComfyUI server/full install. `worker.py` imports bundled core modules.
- Settings include phone access, release models, and stop server.
- `models/`, `.venv/`, `jobs/`, and `network_settings.json` are private.
- Before a customer release: complete an actual GPU edit, inspect visual quality,
  verify installer from a clean extracted ZIP, then update site catalog and
  protected download. Do not claim a benchmark from UI/worker startup alone.
