"""«LA CUENTA» v2: muñecos tipo juguete con animaciones de Quaternius + utilería KayKit + postproceso.
Uso: python3 documental2.py <voces.mp3> <salida.mp4> [--muestras]   (con --muestras, <salida> es la hoja .jpg)
Necesita la carpeta web3d (toy.js, doc2.js, enlaces a three, ubc, ual, rest) servida por http.
"""
import sys, json, pathlib, subprocess, shutil, argparse, time, socket
import numpy as np
from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(AQUI.parent))
import documental as d1   # tramos de voz, plan de tiempos, envolventes, sonido
from reel2 import SCR, SR

WEB = pathlib.Path('/tmp/claude-0/-home-claude/db2b04ec-3c3e-5337-8176-7bac23935aed/scratchpad/web3d')
PORT = 8765
FPS = 30

def servidor():
    s = socket.socket()
    try:
        s.connect(('127.0.0.1', PORT)); s.close(); return None
    except OSError:
        pass
    p = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=WEB, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0); return p

def pagina(voz):
    T, SHOTS, CHIPS, LT, SUBS = d1.plan()
    data = dict(T=T, SHOTS=SHOTS, CHIPS=CHIPS, LT=LT, SUBS=SUBS, ENV=d1.envolventes(voz), QR=d1.qr_matrix('https://menuo.com.co'))
    h = d1.HTML
    estilo = h[h.index('<style>'):h.index('</style>') + 8]
    capas = h[h.index('<div id="vig"'):h.index('<script src="__THREE__">')]
    logo = (WEB / 'logo-blanco.svg')
    shutil.copy(d1.KIT / 'menuo-logo-blanco.svg', logo)
    capas = capas.replace('__LOGO_B__', 'logo-blanco.svg')
    html = f'''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Azeret+Mono:wght@500;700&display=swap">
{estilo}
<script type="importmap">{{"imports":{{"three":"./three/build/three.module.js","three/addons/":"./three/examples/jsm/"}}}}</script></head>
<body><div id="c"><canvas id="cv" width="1080" height="1920"></canvas>
{capas}
<script>window.DATA={json.dumps(data, ensure_ascii=False)};</script>
<script type="module" src="./doc2.js?v={int(time.time())}"></script></body></html>'''
    (WEB / 'documental2.html').write_text(html, encoding='utf-8')
    return T

def abrir(pw):
    b = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(f'http://127.0.0.1:{PORT}/documental2.html', wait_until='networkidle')
    try: pg.wait_for_function('window.__ok===true', timeout=180000)
    except Exception: print('ERRORES', errs); raise
    errs2 = [e for e in errs if '404' not in e]
    if errs2: print('avisos:', errs2[:5])
    return b, pg

def render(voz, out, hoja=False):
    srv = servidor()
    try:
        T = pagina(voz)
        tmp = SCR / 'documental2'; tmp.mkdir(parents=True, exist_ok=True)
        if hoja:
            from PIL import Image, ImageDraw
            ts = [0.3, 3.0, 5.5, 8.9, 10.9, 12.6, 16.5, 18.6, 19.6, 21.4, 22.8, 23.9, 26.0, 29.5, 31.4, 32.9, 34.0, 36.0, 38.5, 41.0]
            with sync_playwright() as pw:
                b, pg = abrir(pw); ims = []; t0 = time.time()
                for t in ts:
                    pg.evaluate(f'window.render({t})'); f = tmp / f'm{t:05.2f}.jpg'; pg.screenshot(path=str(f), type='jpeg', quality=80); ims.append((t, f))
                print(f'{(time.time() - t0) / len(ts):.2f} s por cuadro'); b.close()
            W, H, cols = 240, 427, 7; rows = (len(ims) + cols - 1) // cols
            sh = Image.new('RGB', (W * cols, (H + 22) * rows), 'white'); d = ImageDraw.Draw(sh)
            for k, (t, f) in enumerate(ims):
                x, y = (k % cols) * W, (k // cols) * (H + 22); sh.paste(Image.open(f).resize((W, H)), (x, y)); d.text((x + 5, y + H + 4), f'{t:.1f}s', fill='black')
            sh.save(out, quality=82); print('hoja', out); return
        frames = tmp / 'f'; shutil.rmtree(frames, ignore_errors=True); frames.mkdir()
        n = int(d1.DUR * FPS)
        with sync_playwright() as pw:
            b, pg = abrir(pw)
            for i in range(n):
                pg.evaluate(f'window.render({i / FPS:.4f})'); pg.screenshot(path=str(frames / f'f{i:04d}.jpg'), type='jpeg', quality=90)
                if i % 150 == 0: print('cuadro', i, '/', n, flush=True)
            b.close()
        wav = tmp / 'audio.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', str(wav)], input=d1.sonido(voz, T).tobytes(), check=True)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', str(frames / 'f%04d.jpg'), '-i', str(wav), '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-shortest', '-movflags', '+faststart', out], check=True)
        print('ok', out, n, 'cuadros')
    finally:
        if srv: srv.terminate()

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('voz'); ap.add_argument('out'); ap.add_argument('--muestras', action='store_true')
    a = ap.parse_args()
    render(a.voz, a.out, hoja=a.muestras)
