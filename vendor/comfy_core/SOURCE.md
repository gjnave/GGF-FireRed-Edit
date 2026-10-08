# Embedded inference modules

These third-party Python modules were copied from
[ComfyUI](https://github.com/Comfy-Org/ComfyUI) commit
`b0f4b7b294ce482a2e071d9d762c133d38c7aa07`.

Included: `comfy/`, `comfy_api/`, `comfy_execution/`, `utils/`,
`comfy_extras/nodes_qwen.py`, `nodes.py`, `folder_paths.py`,
`latent_preview.py`, `node_helpers.py`, `protocol.py`, and
`comfyui_version.py`. The ComfyUI web interface, server, custom-node manager,
and other application files are not included. GGF FireRed Edit starts only its
private inference worker process; it does not start a ComfyUI server.

This embedded third-party code retains ComfyUI's GPLv3 license in `LICENSE`.
GGF FireRed Edit includes these modules for its app-owned inference worker.
Its app license does not replace the upstream license.
