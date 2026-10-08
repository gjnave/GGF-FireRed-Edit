"""App-owned FireRed 1.1 editor using bundled Comfy inference modules."""
import argparse
import json
import os
import random
import sys
import time
import traceback
import uuid
from pathlib import Path


def image_tensor(path):
    import numpy as np
    import torch
    from PIL import Image, ImageOps
    with Image.open(path) as opened:
        if opened.width * opened.height > 32_000_000 or max(opened.size) > 8192:
            raise ValueError('Input image exceeds 32 megapixels or 8192 pixels on one side.')
        opened.load()
        image = ImageOps.exif_transpose(opened).convert('RGB')
        return torch.from_numpy(np.asarray(image, dtype=np.float32).copy() / 255).unsqueeze(0), image.size


def patch_sampling(model):
    """Match the official 1.1 workflow's AuraFlow shift 3.1 and CFGNorm 1."""
    import comfy.model_sampling
    import torch
    shifted = model.clone()
    class Sampling(comfy.model_sampling.ModelSamplingDiscreteFlow, comfy.model_sampling.CONST):
        pass
    method = Sampling(model.model.model_config)
    method.set_parameters(shift=3.1, multiplier=1.0)
    shifted.add_object_patch('model_sampling', method)
    normalized = shifted.clone()
    def cfg_norm(args):
        cond = args['cond_denoised']
        proposed = args['denoised']
        scale = (torch.norm(cond, dim=1, keepdim=True) /
                 (torch.norm(proposed, dim=1, keepdim=True) + 1e-8)).clamp(0.0, 1.0)
        return proposed * scale
    normalized.set_model_sampler_post_cfg_function(cfg_norm)
    return normalized


class Engine:
    def __init__(self, core_root: Path, model_root: Path):
        os.chdir(core_root)
        sys.path.insert(0, str(core_root))
        import torch
        import nodes
        import folder_paths
        from comfy_extras.nodes_qwen import TextEncodeQwenImageEditPlus
        if not torch.cuda.is_available():
            raise RuntimeError('An NVIDIA CUDA GPU is required.')
        for kind in ('diffusion_models', 'text_encoders', 'vae'):
            folder_paths.add_model_folder_path(kind, str(model_root / kind), is_default=True)
        self.torch = torch
        self.nodes = nodes
        self.text_node = TextEncodeQwenImageEditPlus
        self.model = self.clip = self.vae = None

    def load(self):
        if self.model is not None:
            return
        from config import WEIGHTS
        nodes = self.nodes
        self.model = patch_sampling(nodes.UNETLoader().load_unet(WEIGHTS['diffusion_models'][0], 'default')[0])
        self.clip = nodes.CLIPLoader().load_clip(WEIGHTS['text_encoders'][0], 'qwen_image', 'default')[0]
        self.vae = nodes.VAELoader().load_vae(WEIGHTS['vae'][0])[0]

    def edit(self, request, protocol):
        import numpy as np
        from PIL import Image, PngImagePlugin
        started = time.perf_counter()
        image_path = request['image']
        prompt = str(request['prompt']).strip()
        if not prompt:
            raise ValueError('Describe the change you want to make.')
        steps = int(request['steps'])
        cfg = float(request['cfg'])
        edge = int(request['edge'])
        if not 1 <= steps <= 80 or not 1 <= cfg <= 10 or not 384 <= edge <= 1536:
            raise ValueError('Steps, guidance, or output size is outside the supported range.')
        seed = int(request.get('seed', -1))
        if seed < 0:
            seed = random.randrange(2**63)
        protocol({'stage': 'Loading FireRed and its text encoder'})
        self.load()
        torch = self.torch
        nodes = self.nodes
        primary, source_size = image_tensor(image_path)
        references = [image_tensor(path)[0] if path else None for path in (request.get('reference2'), request.get('reference3'))]
        width, height = source_size
        factor = edge / max(width, height)
        working_width = max(64, round(width * factor / 32) * 32)
        working_height = max(64, round(height * factor / 32) * 32)
        base = primary.movedim(-1, 1)
        import comfy.utils
        base = comfy.utils.common_upscale(base, working_width, working_height, 'lanczos', 'center').movedim(1, -1)
        protocol({'stage': 'Encoding image and instructions'})
        with torch.no_grad():
            latent = nodes.VAEEncode().encode(self.vae, base)[0]
            positive = self.text_node.execute(self.clip, prompt, vae=self.vae,
                                              image1=base, image2=references[0], image3=references[1])[0]
            negative = self.text_node.execute(self.clip, '', vae=self.vae,
                                              image1=base, image2=references[0], image3=references[1])[0]
            protocol({'stage': f'Generating image · {steps} steps'})
            sampled = nodes.KSampler().sample(self.model, seed, steps, cfg, 'euler', 'simple',
                                              positive, negative, latent, denoise=1.0)[0]
            pixels = nodes.VAEDecode().decode(self.vae, sampled)[0][0]
        torch.cuda.synchronize()
        output_dir = Path(request['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        image = Image.fromarray((pixels.detach().cpu().numpy().clip(0, 1) * 255).astype(np.uint8))
        if request.get('restore_dimensions', False):
            image = image.resize(source_size, Image.Resampling.LANCZOS)
        path = output_dir / f'ggf-firered-{time.strftime("%Y%m%d-%H%M%S")}-{uuid.uuid4().hex[:8]}-seed-{seed}.png'
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('app', 'GGF FireRed Edit')
        metadata.add_text('prompt', prompt)
        metadata.add_text('seed', str(seed))
        image.save(path, pnginfo=metadata)
        return {'output': str(path), 'seed': seed, 'seconds': round(time.perf_counter() - started, 1),
                'working_size': [working_width, working_height], 'saved_size': list(image.size),
                'peak_vram_gib': round(torch.cuda.max_memory_allocated() / 1024**3, 2)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--core-root', type=Path, required=True)
    parser.add_argument('--model-root', type=Path, required=True)
    args = parser.parse_args()
    protocol_out = sys.stdout
    sys.stdout = sys.stderr
    sys.argv = [sys.argv[0], '--models-directory', str(args.model_root.resolve())]
    def send(message):
        protocol_out.write(json.dumps(message) + '\n')
        protocol_out.flush()
    try:
        engine = Engine(args.core_root.resolve(), args.model_root.resolve())
        send({'ready': True})
    except Exception as error:
        send({'ready': False, 'error': str(error)})
        traceback.print_exc()
        return 1
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if request.get('command') == 'stop':
                return 0
            send({'result': engine.edit(request, send)})
        except Exception as error:
            traceback.print_exc()
            send({'error': str(error)})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
