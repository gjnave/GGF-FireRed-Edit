"""Private paths and the exact files required by FireRed editing."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_ROOT = Path(os.environ.get('GGF_FIRERED_MODELS', ROOT / 'models')).resolve()
CORE_ROOT = ROOT / 'vendor' / 'comfy_core'
WEIGHTS = {
    'diffusion_models': ('FireRed-Image-Edit-1.1_fp8mixed_comfy.safetensors', 21439550735),
    'text_encoders': ('qwen2.5vl-7b-bf16.safetensors', 16584415576),
    'vae': ('qwen_image_vae.safetensors', 253806246),
}


def model_status():
    lines = []
    for folder, (name, size) in WEIGHTS.items():
        path = MODEL_ROOT / folder / name
        actual = path.stat().st_size if path.is_file() else 0
        lines.append(f'{name}: ' + ('ready' if actual == size else f'missing/incomplete ({actual:,} / {size:,} bytes)'))
    return '\n'.join(lines)


def require_models():
    missing = []
    for folder, (name, size) in WEIGHTS.items():
        path = MODEL_ROOT / folder / name
        if not path.is_file() or path.stat().st_size != size:
            missing.append(str(path))
    if missing:
        raise RuntimeError('Run INSTALL.bat to get the required model files. Missing or incomplete:\n' + '\n'.join(missing))
