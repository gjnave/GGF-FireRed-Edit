# GGF FireRed Edit handoff

- Product source: `D:\apps2review\FireRed\GGF-FireRed`
- Customer launchers: `D:\apps2review\FireRed\INSTALL.bat`, `RUN.bat`, and `UPDATE.bat`
- Customer ZIP: `D:\apps2review\FireRed\GGF-FireRed-Edit.zip`; build with
  `D:\apps2review\FireRed\build_release.py` and preserve any prior ZIP.
- Source asset: user-supplied `FireRed1.1-Image-Edit-Model-Manager (1).zip`
- GGF style reference: `D:\apps2review\GGF-APP-BUILD-GUIDE.md`
- Live product page: `https://getgoingfast.pro/tools/firered/`; its page,
  catalog entry, and member ZIP were updated on 2026-10-07 and read back.
- The previous manager ZIP remains on the server as a `.zip.previous` file and
  is backed up under `D:\apps2review\FireRed\site-backup\`.
- This is the general image editor; do not turn it into a head swap product.
- The supplied Comfy workflow has no native mask editing path. Keep masks out of
  the customer flow until a tested FireRed conditioning path is available.
- Default models: one cocorang FP8 checkpoint, official Qwen 2.5 VL BF16 text
  encoder, official Qwen image VAE; pinned sources in `model_sources.json`.
- No ComfyUI server/full install. `worker.py` imports bundled core modules.
- Settings include updates, phone access, release models, and stop server.
- `models/`, `.venv/`, `jobs/`, and `network_settings.json` are private.
- Code is on GitHub: `https://github.com/gjnave/GGF-FireRed-Edit`.
  Codeberg repo `https://codeberg.org/Cognibuild/GGF-FireRed-Edit` exists but
  its Git credential needs refresh before it can receive source. Updater falls
  back to GitHub while Codeberg is empty.
- An extracted customer ZIP built the UI and started the worker after fixing
  an initial packaging exclusion of `comfy.ldm.models` and `comfy_api.input`.
  The GitHub-generated source archive update was tested in the extraction.
  Model files were size/SHA-256 verified in `E:\GGF-Models\FireRed`.
- Actual generation loaded the model and reached sampler step 1/6; it was
  stopped at the user's request while Grizzly Max uses the GPU. Output quality
  and speed remain unverified. Do not claim benchmarks until a full edit runs.
- A clean fresh venv INSTALL.bat run has not been performed; the available
  Bernini Python runtime passed `pip check` and imported all required modules.
