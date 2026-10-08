"""Resumable, size-checked model downloads for INSTALL.bat."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from config import MODEL_ROOT, ROOT


def download(root: Path):
    sources = json.loads((ROOT / 'model_sources.json').read_text(encoding='utf-8'))
    outstanding = sum(item['bytes'] for folder, item in sources.items()
                      if not (root / folder / item['name']).is_file())
    if shutil.disk_usage(root.anchor).free < outstanding + 2_000_000_000:
        raise RuntimeError(f'At least {outstanding / 1e9:.1f} GB plus 2 GB working space is needed on {root.anchor}.')
    for folder, item in sources.items():
        destination = root / folder / item['name']
        destination.parent.mkdir(parents=True, exist_ok=True)
        expected = int(item['bytes'])
        if destination.is_file() and destination.stat().st_size == expected:
            with destination.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest != item['sha256']:
                raise RuntimeError(f'Existing model hash does not match publisher: {destination}')
            print(f'Already installed and verified: {item["name"]}', flush=True)
            continue
        if destination.exists():
            raise RuntimeError(f'Existing model has the wrong size; inspect it before continuing: {destination}')
        partial = destination.with_name(destination.name + '.partial')
        if partial.exists() and partial.stat().st_size > expected:
            raise RuntimeError(f'Partial download is larger than expected: {partial}')
        print(f'Downloading {item["name"]} ({expected / 1e9:.1f} GB)...', flush=True)
        command = ['curl.exe', '--location', '--fail', '--retry', '4', '--retry-delay', '5',
                   '--continue-at', '-', '--output', str(partial), item['url']]
        subprocess.run(command, check=True)
        actual = partial.stat().st_size
        if actual != expected:
            raise RuntimeError(f'Incomplete {item["name"]}: {actual:,} of {expected:,} bytes. Rerun INSTALL.bat to resume.')
        print(f'Verifying SHA-256 for {item["name"]}...', flush=True)
        with partial.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != item['sha256']:
            raise RuntimeError(f'Hash mismatch for {partial}; publisher SHA-256 did not match.')
        partial.replace(destination)
        print(f'Ready: {destination}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--models-dir', type=Path, default=MODEL_ROOT)
    args = parser.parse_args()
    download(args.models_dir.resolve())
