# GGF FireRed Edit

- Follow `D:\apps2review\GGF-APP-BUILD-GUIDE.md` and this app's HANDOFF.md.
- Never delete a file or folder without explicit user permission.
- Keep the product focused on general image editing, not head swapping.
- The supplied FireRed workflows do not contain native mask conditioning.
  Do not advertise masking until the specific FireRed path is tested end to end.
- The app owns its bundled inference modules and model worker. No ComfyUI
  installation, service, frontend, or custom-node manager is a dependency.
- Keep .venv, downloaded models, jobs, outputs, and network settings out of Git.
- Customer installer BAT sits beside GGF-FireRed/. Use CMD, not PowerShell.
- Preserve upstream ComfyUI GPLv3 and FireRed model attribution.
- Do a real GPU generation before shipping changes to the existing product page.
- Keep local access login-free. Remote access is separate and optional.
- Release models and Stop server refuse while generation is active.
