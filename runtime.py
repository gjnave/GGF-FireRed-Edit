"""Single GPU worker shared by local and phone views."""
import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

from config import CORE_ROOT, MODEL_ROOT, ROOT, require_models

LOCK = threading.Lock()
_PROCESS_GUARD = threading.Lock()
_PROCESS = None
_LOG = None


def _line(stream, timeout):
    result = queue.Queue(maxsize=1)
    threading.Thread(target=lambda: result.put(stream.readline()), daemon=True).start()
    try:
        return result.get(timeout=timeout)
    except queue.Empty as error:
        raise TimeoutError('The model worker did not respond. Check jobs/firered-worker.log.') from error


def release_models():
    global _PROCESS, _LOG
    with _PROCESS_GUARD:
        process, log = _PROCESS, _LOG
        _PROCESS, _LOG = None, None
    if process and process.poll() is None:
        try:
            process.stdin.write('{"command":"stop"}\n')
            process.stdin.flush()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                process.terminate()
                process.wait(timeout=5)
    if log:
        log.close()


def _worker():
    global _PROCESS, _LOG
    with _PROCESS_GUARD:
        if _PROCESS and _PROCESS.poll() is None:
            return _PROCESS
        require_models()
        (ROOT / 'jobs').mkdir(exist_ok=True)
        log = (ROOT / 'jobs' / 'firered-worker.log').open('a', encoding='utf-8')
        process = subprocess.Popen(
            [sys.executable, '-u', str(ROOT / 'worker.py'), '--core-root', str(CORE_ROOT),
             '--model-root', str(MODEL_ROOT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=log, text=True, encoding='utf-8', bufsize=1,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        _PROCESS, _LOG = process, log
    try:
        line = _line(process.stdout, 180)
        answer = json.loads(line) if line else {}
        if not answer.get('ready'):
            raise RuntimeError(answer.get('error', 'The FireRed worker stopped during startup.'))
    except Exception:
        release_models()
        raise
    return process


def generate(request, progress=None):
    from server_controls import ensure_running
    ensure_running()
    if not LOCK.acquire(blocking=False):
        raise RuntimeError('Another image is generating. Wait for it to finish or stop it first.')
    try:
        process = _worker()
        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        while True:
            line = _line(process.stdout, 1800)
            if not line:
                raise RuntimeError('The worker stopped. Check jobs/firered-worker.log.')
            answer = json.loads(line)
            if 'stage' in answer:
                if progress:
                    progress(0, desc=answer['stage'])
                continue
            if 'error' in answer:
                raise RuntimeError(answer['error'])
            if 'result' in answer:
                return answer['result']
            raise RuntimeError('Unexpected reply from the model worker.')
    finally:
        LOCK.release()


def cancel():
    if not LOCK.locked():
        return 'No generation is running.'
    release_models()
    return 'Generation stopped. The input and any earlier saved results remain available.'
