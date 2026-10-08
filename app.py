"""GGF FireRed Edit: general image editing with an app-local inference core."""
import base64
import os
import uuid
from pathlib import Path

import gradio as gr

from config import ROOT, model_status, require_models
from network_settings import (install_upload_disconnect_handling, launch_access_servers,
                              read_settings, save_settings, verify_login)
from server_controls import ServerControls, add_server_controls, register_servers
import runtime
import workspace

VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
CSS = (ROOT / 'style.css').read_text(encoding='utf-8')
LOGO = base64.b64encode((ROOT / 'assets' / 'ggf-brain-logo.png').read_bytes()).decode()
HEADER = f'''<div class="ggf-hero"><div><div class="ggf-eyebrow">GET GOING FAST · LOCAL AI</div>
<h1>GGF FireRed Edit</h1><p>Change what you want. Keep the rest of the image.</p>
<div class="ggf-links"><a href="https://getgoingfast.pro/tools/firered/" target="_blank">GetGoingFast.pro ↗</a>
<a href="https://youtube.com/@TheAIHobbyGuy" target="_blank">The AI Hobby Guy ↗</a></div></div>
<img src="data:image/png;base64,{LOGO}" alt="Get Going Fast"></div>'''
THEME = gr.themes.Base(primary_hue='amber', neutral_hue='slate').set(
    body_background_fill='#07101f', body_background_fill_dark='#07101f',
    body_text_color='#e8eef9', body_text_color_dark='#e8eef9',
    block_background_fill='#111c2f', block_background_fill_dark='#111c2f',
    block_label_background_fill='#111c2f', block_label_background_fill_dark='#111c2f',
    block_label_text_color='#e8eef9', block_label_text_color_dark='#e8eef9',
    input_background_fill='#091425', input_background_fill_dark='#091425')
CONTROLS = ServerControls(lambda: [runtime.LOCK], runtime.release_models)
ACTIVE_URLS = {}
KEYS = ('image', 'reference2', 'reference3', 'prompt', 'edge', 'steps', 'cfg', 'seed', 'restore_dimensions')
DEFAULTS = (None, None, None, '', 1024, 40, 4, -1, False)


def restore(token):
    owner = token if workspace.valid_owner(token) else uuid.uuid4().hex
    saved = workspace.load(owner)
    form = saved.get('form', {})
    values = [form.get(key, default) for key, default in zip(KEYS, DEFAULTS)]
    for index in (0, 1, 2):
        if values[index] and not Path(values[index]).is_file():
            values[index] = None
    output = saved.get('output')
    if output and not Path(output).is_file():
        output = None
    return [owner, {'owner': owner}, *values, output, saved.get('status', 'Upload an image and describe an edit.')]


def remember(state, *values):
    if not state:
        return
    form = dict(zip(KEYS, values))
    for key in ('image', 'reference2', 'reference3'):
        form[key] = workspace.keep_file(state['owner'], form[key])
    workspace.save(state['owner'], form=form)


def edit(state, *values, preview=False, progress=gr.Progress()):
    if not state:
        raise gr.Error('The app is still loading. Try again in a moment.')
    form = dict(zip(KEYS, values))
    if not form['image']:
        raise gr.Error('Upload an image and wait for its preview before generating.')
    if not str(form['prompt']).strip():
        raise gr.Error('Describe what should change.')
    try:
        require_models()
        remember(state, *values)
        form = workspace.load(state['owner'])['form']
        edge = max(384, round(int(form['edge']) / 2 / 32) * 32) if preview else int(form['edge'])
        request = {**form, 'edge': edge, 'output_dir': str(ROOT / 'jobs' / state['owner'] / 'outputs')}
    except (OSError, ValueError, RuntimeError) as error:
        raise gr.Error(str(error)) from None
    yield None, 'Starting image edit…'
    try:
        result = runtime.generate(request, progress)
    except Exception as error:
        workspace.save(state['owner'], status=str(error))
        raise gr.Error(str(error)) from None
    message = (f"Finished in {result['seconds']:.1f}s · {result['saved_size'][0]} × "
               f"{result['saved_size'][1]} · seed {result['seed']} · peak GPU "
               f"{result['peak_vram_gib']:.1f} GB. Saved: {Path(result['output']).name}")
    workspace.save(state['owner'], output=result['output'], status=message)
    yield result['output'], message


def preview_edit(state, *values, progress=gr.Progress()):
    yield from edit(state, *values, preview=True, progress=progress)


def save_access(mode, username, password):
    labels = {'This computer only': 'local', 'Local network': 'lan',
              'Temporary public link': 'public'}
    saved = save_settings(labels[mode], username, password)
    return ('Saved. Restart RUN.bat to apply. Local access stays login-free. ' +
            ('Remote login enabled.' if saved['digest'] else 'Remote login off. Anyone with the link can use the app.'))


def build_demo():
    with gr.Blocks(title='GGF FireRed Edit') as demo:
        state = gr.State(None)
        token = gr.Textbox('', visible=False)
        gr.HTML(HEADER)
        with gr.Tabs():
            with gr.Tab('Edit', id='edit'):
                gr.Markdown('Upload a photo and say what to change. Optional reference images can supply an outfit, object, or style. The model may still change details outside the requested area.')
                with gr.Row(equal_height=True, elem_id='input-images'):
                    image = gr.Image(label='Image to edit', sources=['upload', 'clipboard'], type='filepath', height=430)
                    output = gr.Image(label='Edited image', type='filepath', interactive=False,
                                      height=430, buttons=['fullscreen', 'download'], elem_id='result-image')
                prompt = gr.Textbox(label='What should change?', lines=3,
                                    placeholder='For example: remove the hat and restore the hair naturally. Keep everything else the same.')
                with gr.Accordion('Add reference images · optional', open=False):
                    with gr.Row():
                        reference2 = gr.Image(label='Reference 2 · look or object', sources=['upload', 'clipboard'], type='filepath', height=260)
                        reference3 = gr.Image(label='Reference 3 · another look or object', sources=['upload', 'clipboard'], type='filepath', height=260)
                    gr.Markdown('Refer to these as “Picture 2” and “Picture 3” in your instruction.')
                preview = gr.Button('Turbo preview · half size · Ctrl+Enter', variant='primary', elem_id='turbo-edit')
                generate = gr.Button('Generate edit · full size', variant='primary')
                stop = gr.Button('Stop current generation', variant='secondary')
                status = gr.Markdown('Upload an image and describe an edit.', elem_id='job-status')
            with gr.Tab('Settings', id='settings'):
                add_server_controls(CONTROLS)
                gr.Markdown(f'### GGF FireRed Edit · {VERSION}')
                installed = gr.Textbox(label='Model files', value=model_status, interactive=False, lines=4)
                gr.Button('Check model files', variant='secondary').click(model_status, outputs=installed, queue=False)
                gr.Markdown('### Image generation')
                with gr.Row():
                    edge = gr.Slider(384, 1536, value=1024, step=32, label='Working long edge · pixels')
                    steps = gr.Slider(1, 80, value=40, step=1, label='Sampling steps')
                with gr.Row():
                    cfg = gr.Slider(1, 10, value=4, step=.5, label='Instruction strength')
                    seed = gr.Number(value=-1, precision=0, label='Seed · -1 = random')
                restore_dimensions = gr.Checkbox(False, label='Resize result back to the input dimensions')
                gr.Markdown('### Updates')
                check_updates = gr.Button('Check for updates', variant='secondary')
                install_update = gr.Button('Update and restart', variant='primary')
                update_notice = gr.Markdown('Models, settings, and saved results are kept when updating.')
                def check_update_status():
                    from update_app import check_update
                    return check_update()
                check_updates.click(check_update_status, outputs=update_notice, queue=False)
                def update_and_restart():
                    import threading
                    from update_app import start_restart
                    if not runtime.LOCK.acquire(blocking=False):
                        return 'Finish or stop the current generation before updating.'
                    try:
                        start_restart()
                    except Exception as error:
                        runtime.LOCK.release()
                        return f'Update could not start: {error}'
                    timer = threading.Timer(3, lambda: os._exit(0))
                    timer.daemon = True
                    timer.start()
                    return 'Updating and restarting. A temporary public phone link may change.'
                install_update.click(update_and_restart, outputs=update_notice, queue=False)
                gr.Markdown('### Use on your phone')
                saved = read_settings()
                mode_labels = {'local': 'This computer only', 'lan': 'Local network',
                               'public': 'Temporary public link'}
                access = gr.Dropdown(list(mode_labels.values()), value=mode_labels[saved['mode']], label='Access mode')
                with gr.Row():
                    username = gr.Textbox(label='Username', value=saved['username'], placeholder='ggf')
                    password = gr.Textbox(label='Password · blank turns login off', type='password')
                notice = gr.Markdown('Save and restart to apply. Local access remains login-free. Public links change after restart.')
                gr.Button('Save access settings', variant='secondary').click(save_access, [access, username, password], notice, queue=False)
                gr.Button('Show current app links', variant='secondary').click(
                    lambda: '\n\n'.join(f'{key}: {url}' for key, url in ACTIVE_URLS.items() if url),
                    outputs=notice, queue=False)
        gr.HTML(f'<div class="ggf-footer">Powered by FireRed Image Edit 1.1 · app-local Comfy core · {VERSION}<br>Your Time Is Limited. Get Going Fast.</div>')
        fields = [image, reference2, reference3, prompt, edge, steps, cfg, seed, restore_dimensions]
        for control in fields:
            control.input(remember, [state, *fields], [], queue=False, show_progress='hidden')
        preview.click(preview_edit, [state, *fields], [output, status], concurrency_id='gpu', concurrency_limit=1)
        generate.click(edit, [state, *fields], [output, status], concurrency_id='gpu', concurrency_limit=1)
        stop.click(lambda: runtime.cancel(), outputs=status, queue=False)
        demo.load(restore, [token], [token, state, *fields, output, status], queue=False,
                  show_progress='hidden', js="()=>{const k='ggf-firered-workspace-v1';let t=localStorage.getItem(k);if(!/^[a-f0-9]{32}$/.test(t||'')){t=crypto.randomUUID().replaceAll('-','');localStorage.setItem(k,t);}return [t];}")
        demo.load(None, [], [], js="()=>{if(!window.ggfFireRedKeys){window.ggfFireRedKeys=true;document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='Enter'){e.preventDefault();document.querySelector('#turbo-edit')?.click();}})}return [];}")
    demo.queue(max_size=4, default_concurrency_limit=1)
    return demo


if __name__ == '__main__':
    (ROOT / 'jobs').mkdir(exist_ok=True)
    (ROOT / 'app.lock').write_text(str(os.getpid()), encoding='utf-8')
    install_upload_disconnect_handling()
    saved = read_settings()
    auth = (lambda username, password: verify_login(username, password, saved)) if saved['digest'] else None
    local, remote, local_url, remote_url = launch_access_servers(
        build_demo, mode=saved['mode'], preferred_port=int(os.environ.get('GGF_FIRERED_PORT', '7866')),
        auth=auth, inbrowser='--no-browser' not in os.sys.argv, css=CSS, theme=THEME,
        allowed_paths=[str(ROOT / 'jobs')], show_error=True, footer_links=[])
    ACTIVE_URLS.update(Local=local_url, Remote=remote_url)
    register_servers(local, remote)
    local.block_thread()
