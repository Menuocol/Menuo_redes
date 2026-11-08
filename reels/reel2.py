"""Generador de Reels de Menuo v2 (1080x1920, 30 fps), pensado para retención:
gancho armado desde el cuadro 1, escenas que cambian con cada frase, subtítulos palabra por palabra y pausas recortadas.

Uso:
  python3 reel2.py <reel> <audio.mp3|-> <salida.mp4> [--portada portada.jpg]
  <reel> es una clave de guiones.REELS. Con '-' como audio arma una versión de prueba muda con tiempos estimados.
"""
import os, sys, re, json, html, pathlib, subprocess, shutil, argparse
import numpy as np
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from guiones import REELS

AQUI = pathlib.Path(__file__).resolve().parent
KIT = AQUI / 'kit'                      # fotos (ID de Pexels), logos y pantalla de la app
SCR = pathlib.Path(os.environ.get('REEL_TMP', '/tmp/menuo-reels'))  # cuadros temporales
PEX = KIT / 'fotos'
APP = KIT / 'app-menu-rojo.png'
LOGO_B = KIT / 'menuo-logo-blanco.svg'
FPS, SR = 30, 44100
ROJO, LIMA, TINTA, BLANCO = '#F42902', '#C9FB00', '#1A1B1F', '#FDFDFF'
CAP_BORDE, CAP_DENTRO = 0.34, 0.22   # pausa máxima entre frases y dentro de una frase (s)
COLA = 0.9                           # segundos después de la última palabra
e = html.escape

# ---------------------------------------------------------------- tiempos
ESPECIALES = {'qr': 2, 'pse': 3, 'dm': 2, 'nequi': 2, 'demo': 2, '14': 3}

def silabas(w):
    k = re.sub(r'[^\wáéíóúüñ]', '', w.lower())
    if k in ESPECIALES: return ESPECIALES[k]
    return max(1, len(re.findall(r'[aeiouáéíóúü]+', k)))

def palabras(t):
    return [w for w in t.split() if re.search(r'\w', w)]

def grupos(t):
    """Palabras partidas por puntuación interna (donde la voz suele hacer pausa)."""
    out, cur = [], []
    for w in palabras(t):
        cur.append(w)
        if re.search(r'[,:;.…?!]["»]?$', w): out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def repartir(ws, a, b):
    """Reparte las palabras ws entre a y b según sus sílabas."""
    pes = np.array([silabas(w) + 0.6 for w in ws], float); pes /= pes.sum()
    bordes = a + np.concatenate([[0], np.cumsum(pes)]) * (b - a)
    return [(w, float(bordes[i]), float(bordes[i + 1])) for i, w in enumerate(ws)]

def decodificar(mp3):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def silencios(x):
    hop = SR // 100
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    umbral = max(-48.0, np.percentile(db, 95) - 32)
    voz = db > umbral
    idx = np.flatnonzero(voz)
    ini, fin = idx[0] / 100, (idx[-1] + 1) / 100
    gaps, i = [], idx[0]
    while i <= idx[-1]:
        if not voz[i]:
            j = i
            while j <= idx[-1] and not voz[j]: j += 1
            if (j - i) >= 9: gaps.append((i / 100, j / 100))
            i = j
        else: i += 1
    return ini, fin, gaps

def elegir_bordes(frases, ini, fin, gaps):
    """Programación dinámica: elige P-1 silencios como límites de frase, favoreciendo silencios largos
    y duraciones parecidas a las esperadas por sílabas."""
    P, m = len(frases), len(gaps)
    if m < P - 1: raise SystemExit(f'Solo hay {m} silencios para {P} frases; revisa el audio.')
    S = np.array([sum(silabas(w) for w in palabras(f.get('tts', f['t']))) for f in frases], float)
    total = (fin - ini) - sum(b - a for a, b in gaps) * 0.6
    esp = S / S.sum() * total
    L = np.array([b - a for a, b in gaps]); med = np.median(L)
    def costo(i, a, b): d = max(b - a, 0.05); return np.log(d / esp[i]) ** 2
    INF = 1e18
    dp = np.full((P, m), INF); prv = np.zeros((P, m), int)
    for k in range(m):
        dp[0, k] = costo(0, ini, gaps[k][0]) - 0.6 * np.log(L[k] / med)
    for i in range(1, P - 1):
        for k in range(i, m):
            for j in range(i - 1, k):
                c = dp[i - 1, j] + costo(i, gaps[j][1], gaps[k][0]) - 0.6 * np.log(L[k] / med)
                if c < dp[i, k]: dp[i, k] = c; prv[i, k] = j
    best, bk = INF, -1
    for k in range(P - 2, m):
        c = dp[P - 2, k] + costo(P - 1, gaps[k][1], fin)
        if c < best: best, bk = c, k
    sel = [bk]
    for i in range(P - 2, 0, -1): sel.append(prv[i, sel[-1]])
    return sorted(sel)

def preparar_audio(mp3, frases, wav_out):
    x = decodificar(mp3)
    ini, fin, gaps = silencios(x)
    sel = set(elegir_bordes(frases, ini, fin, gaps)) if len(frases) > 1 else set()
    # reconstruye con pausas recortadas; mapa de tiempos original -> nuevo
    piezas, mapa, t_nuevo = [], [], 0.0
    def tomar(a, b):
        nonlocal t_nuevo
        seg = x[int(a * SR):int(b * SR)].copy()
        f = min(len(seg) // 2, int(0.004 * SR))
        if f: seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        mapa.append((a, b, t_nuevo)); piezas.append(seg); t_nuevo += len(seg) / SR
    pre = 0.04
    cur = max(0.0, ini - pre)
    for k, (a, b) in enumerate(gaps):
        tomar(cur, a)
        cap = CAP_BORDE if k in sel else CAP_DENTRO
        if b - a <= cap: tomar(a, b)
        else:
            tomar(a, a + cap / 2); tomar(b - cap / 2, b)
        cur = b
    tomar(cur, min(len(x) / SR, fin + 0.12))
    y = np.concatenate(piezas)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', wav_out], input=y.astype(np.float32).tobytes(), check=True)
    def m(t):
        for a, b, n in mapa:
            if a - 1e-6 <= t <= b + 1e-6: return n + (t - a)
        for a, b, n in mapa:  # t cae en un tramo recortado
            if t < a: return n
        return t_nuevo
    # frases y palabras en el tiempo nuevo
    orden = sorted(sel)
    lims = [ini] + [g for k in orden for g in gaps[k]] + [fin]
    out = []
    for i, f in enumerate(frases):
        a, b = lims[2 * i], lims[2 * i + 1]
        internos = [(ga, gb) for ga, gb in gaps if ga > a + 1e-6 and gb < b - 1e-6]
        tramos, c = [], a
        for ga, gb in internos: tramos.append((c, ga)); c = gb
        tramos.append((c, b))
        gr = grupos(f['t'])
        ws = []
        if len(tramos) == len(gr):
            for g, (ta, tb) in zip(gr, tramos): ws += repartir(g, m(ta), m(tb))
        else:
            ws = repartir(palabras(f['t']), m(a), m(b))
        out.append(dict(s=m(a), e=m(b), words=ws))
    return out, t_nuevo

def estimar(frases):
    t, out = 0.05, []
    for f in frases:
        ws = palabras(f['t'])
        d = sum(silabas(w) for w in ws) * 0.155 + 0.1
        out.append(dict(s=t, e=t + d, words=repartir(ws, t, t + d))); t += d + 0.3
    return out, t - 0.3

# ---------------------------------------------------------------- HTML
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000}
#c{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:Archivo,Arial,sans-serif;color:#FDFDFF;background:#F42902}
.grid{background-image:linear-gradient(rgba(253,253,255,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(253,253,255,.10) 1px,transparent 1px);background-size:72px 72px}
.sc{position:absolute;inset:0;visibility:hidden;overflow:hidden}
.ph{position:absolute;left:-3%;top:-3%;width:106%;height:106%;object-fit:cover}
.abs{position:absolute}
.hl{font-weight:900;font-stretch:104%;text-transform:uppercase;line-height:.9;letter-spacing:-.035em}
.hl.fit{white-space:nowrap;text-shadow:0 6px 34px rgba(0,0,0,.28)}
.hl.fit .mark{text-shadow:none}
.mono{font-family:'Azeret Mono',monospace}
.mark{display:inline-block;padding:.02em .14em .06em;border-radius:.12em}
.chip{position:absolute;left:64px;top:300px;font-family:'Azeret Mono',monospace;font-weight:700;font-size:34px;letter-spacing:.04em;text-transform:uppercase;padding:14px 28px;border-radius:999px}
.stk{position:absolute;left:64px;font-weight:900;font-stretch:104%;text-transform:uppercase;letter-spacing:-.03em;line-height:1;padding:.12em .3em .14em;border-radius:.14em;box-shadow:0 26px 50px -20px rgba(0,0,0,.55)}
.phone{position:absolute;left:316px;top:280px;width:448px;height:937px;border:14px solid #1A1B1F;border-radius:70px;overflow:hidden;background:#1A1B1F;box-shadow:0 60px 110px -40px rgba(40,0,0,.8)}
.scr{position:absolute;inset:0;border-radius:56px;overflow:hidden}
.notch{position:absolute;left:50%;top:14px;width:120px;height:32px;margin-left:-60px;border-radius:20px;background:#1A1B1F}
.num{position:absolute;left:34px;top:270px;font-weight:900;font-stretch:104%;font-size:200px;line-height:1;letter-spacing:-.05em;color:#C9FB00}
@keyframes kb{from{transform:scale(1.16) translate(var(--kx),var(--ky))}to{transform:scale(1.01) translate(0,0)}}
@keyframes punch{from{transform:scale(1.06)}to{transform:scale(1)}}
@keyframes pop{0%{transform:scale(.4) rotate(var(--r,0deg));opacity:0}65%{transform:scale(1.07) rotate(var(--r,0deg));opacity:1}100%{transform:scale(1) rotate(var(--r,0deg));opacity:1}}
@keyframes slam{0%{transform:scale(2.3) rotate(var(--r,0deg));opacity:0}100%{transform:scale(1) rotate(var(--r,0deg));opacity:1}}
@keyframes rise{from{transform:translateY(80px) rotate(var(--r,0deg));opacity:0}to{transform:translateY(0) rotate(var(--r,0deg));opacity:1}}
@keyframes settle{from{transform:scale(1.05) rotate(var(--r,0deg))}to{transform:scale(1) rotate(var(--r,0deg))}}
@keyframes scan{0%{top:6%}50%{top:88%}100%{top:6%}}
@keyframes dim{to{opacity:.32}}
@keyframes strike{from{transform:scaleX(0) rotate(-3deg)}to{transform:scaleX(1) rotate(-3deg)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes slidein{from{transform:translateX(115%)}to{transform:translateX(0)}}
@keyframes shake{0%,100%{transform:translateX(0) rotate(var(--r,0deg))}25%{transform:translateX(-16px) rotate(var(--r,0deg))}75%{transform:translateX(16px) rotate(var(--r,0deg))}}
@keyframes ripple{0%{transform:scale(.2);opacity:.9}100%{transform:scale(2.4);opacity:0}}
@keyframes fadein{from{opacity:0}to{opacity:1}}
.qs{background:linear-gradient(#F42902,#F42902) no-repeat 0 60%/0% 14px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
@keyframes strikebg{to{background-size:100% 14px}}
@keyframes dimtxt{to{color:rgba(253,253,255,.36)}}
#logo{position:absolute;left:64px;top:150px;height:46px;z-index:50}
#tag{position:absolute;right:64px;top:160px;z-index:50;font-family:'Azeret Mono',monospace;font-weight:700;font-size:24px;letter-spacing:.06em;color:#C9FB00;text-transform:uppercase;text-shadow:0 2px 12px rgba(0,0,0,.35)}
#pasos{position:absolute;left:64px;right:64px;top:226px;height:10px;display:flex;gap:12px;z-index:50;opacity:0}
#pasos i{flex:1;border-radius:9px;background:rgba(253,253,255,.32);overflow:hidden;position:relative}
#pasos i b{position:absolute;inset:0;background:#C9FB00;transform-origin:left;transform:scaleX(0)}
#cap{position:absolute;left:56px;right:56px;top:1236px;height:196px;display:flex;align-items:center;justify-content:center;text-align:center;z-index:60}
#capin{font-weight:800;font-size:56px;line-height:1.32;letter-spacing:-.012em;text-wrap:balance;max-width:900px}
#capin .box{background:#FDFDFF;color:#1A1B1F;padding:.04em .22em .08em;border-radius:16px;-webkit-box-decoration-break:clone;box-decoration-break:clone;box-shadow:0 18px 40px -18px rgba(0,0,0,.5)}
#capin .w{padding:0 .06em;border-radius:10px}
#capin .w.f{color:rgba(26,27,31,.34)}
#capin .w.a{background:#C9FB00}
"""

def anim(nombre, dur, delay, ease='cubic-bezier(.2,.8,.2,1)', extra='both'):
    return f'{nombre} {dur:.3f}s {ease} {delay:.3f}s {extra}'

def foto_uri(i): return (PEX / f'{i}.jpg').as_uri()

def t_palabra(fr, k):
    ws = fr['words']; k = min(k, len(ws) - 1)
    return ws[k][1]

def qr_svg(url, size=300, fg=TINTA):
    import qrcode
    q = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_M); q.add_data(url); q.make()
    mtx = q.get_matrix(); n = len(mtx); s = size / n
    rects = ''.join(f'<rect x="{x*s:.2f}" y="{y*s:.2f}" width="{s+.4:.2f}" height="{s+.4:.2f}"/>' for y, row in enumerate(mtx) for x, v in enumerate(row) if v)
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" fill="{fg}">{rects}</svg>'

def lineas_hl(lineas, resalta, fondo_mark, color_mark):
    out = []
    for i, l in enumerate(lineas):
        if i == resalta: out.append(f'<div><span class="mark" style="background:{fondo_mark};color:{color_mark}">{e(l)}</span></div>')
        else: out.append(f'<div>{e(l)}</div>')
    return ''.join(out)

def kb(i, s, d):
    dirs = [('-2%', '-1%'), ('2%', '1%'), ('-1%', '2%'), ('1%', '-2%')]
    kx, ky = dirs[i % 4]
    return f'--kx:{kx};--ky:{ky};animation:{anim("kb", d + .4, s, "linear")}'

SOMBRA = 'linear-gradient(180deg,rgba(26,27,31,.72) 0%,rgba(26,27,31,.18) 28%,rgba(26,27,31,0) 50%,rgba(26,27,31,.5) 100%)'

def telefono(contenido, s, st=''):
    return f'<div class="phone" style="animation:{anim("rise", .38, s)};{st}"><div class="scr">{contenido}</div><div class="notch"></div></div>'

def pantalla_pago(fr, s, metodos, rel):
    filas = [('1', 'Tacos al pastor', '$20.000'), ('1', 'Dip de queso', '$18.000'), ('1', 'Nachos', '$24.000')]
    items = ''.join(f'<div style="display:flex;justify-content:space-between;margin-top:14px"><span>{q}&nbsp;&nbsp;{e(n)}</span><span>{p}</span></div>' for q, n, p in filas)
    nombres = ['Tarjeta', 'PSE', 'Nequi', 'Bancolombia']
    botones = ''
    for k, n in enumerate(nombres):
        if metodos:
            idx = next((j for j, w in enumerate(fr['words']) if n.lower() in w[0].lower()), None)
            t0 = fr['words'][idx][1] - 0.05 if idx is not None else s + 0.3 + k * 0.2
        else:
            t0 = s + 0.25 + k * 0.08
        sel = (n == 'Nequi')
        botones += (f'<div style="height:104px;border-radius:24px;background:{BLANCO};color:{TINTA};display:flex;align-items:center;justify-content:center;'
                    f'font-weight:800;font-size:{28 if n != "Bancolombia" else 24}px;animation:{anim("pop", .3, t0)}">{e(n)}</div>')
    t_ok = (fr['words'][-1][2] + 0.12) if metodos else (s + (fr['e'] - fr['s']) * 0.62)
    nequi_t = t_ok - 0.25
    return f'''<div class="grid" style="position:absolute;inset:0;background-color:{ROJO}"></div>
<div class="abs mono" style="right:28px;top:62px;font-weight:700;font-size:22px;padding:10px 18px;border-radius:999px;border:2px solid rgba(253,253,255,.6)">MESA 4</div>
<div class="abs hl" style="left:30px;top:120px;font-size:66px">Pagar</div>
<div class="abs mono" style="left:30px;right:30px;top:200px;font-size:21px;font-weight:500">{items}
<div style="display:flex;justify-content:space-between;margin-top:26px;padding-top:20px;border-top:2px dashed rgba(253,253,255,.5);font-weight:700;font-size:30px"><span>TOTAL</span><span>$62.000</span></div></div>
<div class="abs" style="left:30px;right:30px;top:470px;display:grid;grid-template-columns:1fr 1fr;gap:16px">{botones}</div>
<div class="abs" style="left:30px;top:590px;height:104px;width:172px;border-radius:24px;border:6px solid {LIMA};opacity:0;animation:{anim("fadein", .15, nequi_t)}"></div>
<div class="abs" style="left:30px;right:30px;bottom:40px;height:96px;border-radius:999px;background:{TINTA};color:{BLANCO};display:flex;align-items:center;justify-content:center;font-weight:800;font-size:32px">Pagar $62.000</div>
<div class="abs" style="inset:0;background:{LIMA};color:{TINTA};display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;animation:{anim("pop", .34, t_ok)}">
<div style="width:170px;height:170px;border-radius:50%;background:{TINTA};display:flex;align-items:center;justify-content:center"><svg width="96" height="96" viewBox="0 0 24 24" fill="none" stroke="{LIMA}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div>
<div class="hl" style="font-size:84px;margin-top:34px">Pagado</div><div class="mono" style="font-size:24px;font-weight:700;margin-top:14px">NEQUI · $62.000</div></div>'''

def ticket(s, sello_t, top, rot=-3, hook=False):
    filas = ['1&nbsp;&nbsp;Tacos al pastor', '1&nbsp;&nbsp;Dip de queso', '1&nbsp;&nbsp;Nachos de la casa']
    ent = anim('settle', .5, s) if hook else anim('rise', .38, s)
    return f'''<div class="abs mono" style="--r:{rot}deg;left:190px;width:700px;top:{top}px;background:{BLANCO};color:{TINTA};padding:44px 48px 52px;border-radius:10px;font-size:31px;font-weight:500;line-height:1.55;box-shadow:0 50px 90px -30px rgba(0,0,0,.7);transform:rotate({rot}deg);animation:{ent}">
<div style="display:flex;justify-content:space-between;font-weight:700;letter-spacing:.04em"><span>MESA 4</span><span>#014</span></div>
<div style="border-top:3px dashed rgba(26,27,31,.35);margin:18px 0"></div>{''.join(f'<div>{f}</div>' for f in filas)}
<div style="border-top:3px dashed rgba(26,27,31,.35);margin:18px 0"></div>
<div style="display:flex;justify-content:space-between;font-weight:700"><span>TOTAL $62.000</span><span>8:14 P. M.</span></div>
<div class="abs" style="--r:-13deg;left:160px;top:150px;padding:6px 30px 12px;border:10px solid {ROJO};border-radius:22px;color:{ROJO};font-family:Archivo;font-weight:900;font-stretch:104%;font-size:118px;letter-spacing:-.03em;line-height:1;background:rgba(253,253,255,.82);opacity:0;animation:{anim("slam", .2, sello_t, "cubic-bezier(.5,0,.75,0)")}">PAGADO</div></div>'''

def escena_html(idx, esc, fr, s, d, reel):
    t = esc['tipo']
    fondo_tinta = reel.get('fondo') == 'tinta'
    if t == 'hook':
        if esc.get('foto'):
            bg = (f'<img class="ph" src="{foto_uri(esc["foto"])}" style="object-position:{esc.get("pos", "50% 50%")};{kb(idx, s, d)}">'
                  f'<div class="abs" style="inset:0;background:linear-gradient(180deg,rgba(26,27,31,.88) 0%,rgba(26,27,31,.66) 30%,rgba(26,27,31,0) 56%,rgba(26,27,31,.35) 100%)"></div>')
            mark_bg, mark_fg = LIMA, TINTA
            extra = ''
        else:
            bg = f'<div class="grid abs" style="inset:0;background-color:{TINTA}"></div>'
            mark_bg, mark_fg = ROJO, BLANCO
            extra = (f'<div class="abs" style="--r:-6deg;left:300px;top:820px;width:480px;height:480px;border-radius:40px;background:{BLANCO};display:flex;align-items:center;justify-content:center;'
                     f'transform:rotate(-6deg);box-shadow:0 50px 90px -30px rgba(0,0,0,.8);animation:{anim("settle", .5, s)}">{qr_svg("https://menuo.com.co", 380)}</div>'
                     f'<div class="abs" style="--r:8deg;left:680px;top:760px;width:190px;height:190px;border-radius:50%;background:{ROJO};display:flex;align-items:center;justify-content:center;opacity:0;animation:{anim("slam", .2, s + .32)}">'
                     f'<svg width="110" height="110" viewBox="0 0 24 24" stroke="{BLANCO}" stroke-width="3.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></div>')
        txt = f'<div class="abs hl fit" data-w="952" data-max="168" style="left:64px;top:300px;width:952px;transform-origin:left top;animation:{anim("settle", .45, s)}">{lineas_hl(esc["lineas"], esc.get("resalta", -1), mark_bg, mark_fg)}</div>'
        return bg + extra + txt
    if t == 'foto':
        z = esc.get('zoom', 1)
        out = (f'<div class="abs" style="inset:0;transform:scale({z});transform-origin:50% 6%"><img class="ph" src="{foto_uri(esc["foto"])}" style="object-position:{esc.get("pos", "50% 50%")};{kb(idx, s, d)}"></div>'
               f'<div class="abs" style="inset:0;background:{SOMBRA}"></div>')
        if esc.get('label'):
            out += f'<div class="chip" style="background:{TINTA};color:{LIMA};animation:{anim("pop", .3, s + .05)}">{e(esc["label"])}</div>'
        return out
    if t == 'ticket':
        bg = f'<img class="ph" src="{foto_uri("17318176")}" style="object-position:50% 50%;{kb(idx, s, d)}"><div class="abs" style="inset:0;background:rgba(26,27,31,.55)"></div>'
        if esc.get('hook'):
            txt = f'<div class="abs hl fit" data-w="952" data-max="150" style="left:64px;top:300px;width:952px;transform-origin:left top;animation:{anim("settle", .45, s)}">{lineas_hl(esc["lineas"], esc.get("resalta", -1), LIMA, TINTA)}</div>'
            return bg + txt + ticket(s, s + .42, 760, hook=True)
        st = t_palabra(fr, esc.get('sello_palabra', 0))
        return bg + ticket(s, st, 420)
    if t == 'qr':
        cam = (f'<img class="ph" src="{foto_uri("39910759")}" style="object-position:50% 50%;filter:blur(5px) brightness(.62)">'
               f'<div class="abs" style="left:60px;top:240px;width:300px;height:300px;border-radius:24px;background:{BLANCO};padding:22px">{qr_svg("https://menuo.com.co", 256)}</div>'
               f'<div class="abs" style="left:40px;top:220px;width:340px;height:340px;border:7px solid {LIMA};border-radius:30px"></div>'
               f'<div class="abs" style="left:52px;width:316px;height:6px;border-radius:6px;background:{LIMA};box-shadow:0 0 22px 6px rgba(201,251,0,.6);top:240px;animation:{anim("scan", 1.3, s, "ease-in-out", "infinite both")}"></div>')
        t_ok = fr['words'][min(5, len(fr['words']) - 1)][2] + .05
        cam += (f'<div class="abs" style="left:34px;right:34px;top:620px;padding:22px 26px;border-radius:26px;background:{BLANCO};color:{TINTA};opacity:0;animation:{anim("rise", .3, t_ok)}">'
                f'<div class="mono" style="font-size:18px;font-weight:700;letter-spacing:.06em;color:{ROJO}">MENUO · MESA 4</div><div style="font-weight:800;font-size:30px;margin-top:6px">Abrir el menú →</div></div>')
        return (f'<div class="grid abs" style="inset:0;background-color:{ROJO}"></div><div class="num" style="animation:{anim("pop", .3, s)}">0{esc["paso"]}</div>'
                + telefono(cam, s))
    if t == 'app':
        t_fotos = t_palabra(fr, 5)
        t_en = fr['words'][min(esc.get('ingles', 10), len(fr['words']) - 1)][1]
        scr = (f'<img src="{APP.as_uri()}" style="position:absolute;left:0;top:0;width:100%">'
               f'<div class="abs" style="left:322px;top:299px;width:88px;height:88px;border-radius:50%;background:rgba(201,251,0,.85);opacity:0;animation:{anim("ripple", .6, t_fotos, "ease-out")}"></div>')
        toggle = (f'<div class="abs mono" style="left:774px;top:560px;display:flex;border-radius:999px;background:{TINTA};padding:8px;font-weight:700;font-size:30px;animation:{anim("pop", .3, s + .3)}">'
                  f'<span style="position:relative;padding:12px 22px;border-radius:999px;color:{TINTA};background:{LIMA}">ES<span class="abs" style="inset:0;border-radius:999px;background:{TINTA};color:{BLANCO};display:flex;align-items:center;justify-content:center;opacity:0;animation:{anim("fadein", .12, t_en)}">ES</span></span>'
                  f'<span style="position:relative;padding:12px 22px;border-radius:999px;color:{BLANCO}">EN<span class="abs" style="inset:0;border-radius:999px;background:{LIMA};color:{TINTA};display:flex;align-items:center;justify-content:center;opacity:0;animation:{anim("fadein", .12, t_en)}">EN</span></span></div>')
        return (f'<div class="grid abs" style="inset:0;background-color:{ROJO}"></div><div class="num" style="animation:{anim("pop", .3, s)}">0{esc["paso"]}</div>'
                + telefono(scr, s) + toggle)
    if t == 'pago':
        num = f'<div class="num" style="animation:{anim("pop", .3, s)}">0{esc["paso"]}</div>' if esc.get('paso') else ''
        return f'<div class="grid abs" style="inset:0;background-color:{ROJO}"></div>{num}' + telefono(pantalla_pago(fr, s, esc.get('metodos'), 0), s)
    if t == 'panel':
        estados = [('1', 'Libre', 'l'), ('2', 'Pidiendo', 'r'), ('3', 'Libre', 'l'), ('4', 'Pagado', 'g'), ('5', 'En cocina', 'w'), ('6', 'Libre', 'l'),
                   ('7', 'Pidiendo', 'r'), ('8', 'En cocina', 'w'), ('9', 'Pagado', 'g')]
        col = {'l': ('rgba(253,253,255,.10)', 'rgba(253,253,255,.6)'), 'r': (ROJO, BLANCO), 'g': (LIMA, TINTA), 'w': (BLANCO, TINTA)}
        celdas = ''
        for k, (n, est, c) in enumerate(estados):
            bgc, fgc = col[c]
            borde = f'border:4px solid {LIMA};' if n == '4' else 'border:2px solid rgba(253,253,255,.14);'
            celdas += (f'<div style="height:200px;border-radius:26px;background:rgba(253,253,255,.05);{borde}padding:22px;display:flex;flex-direction:column;justify-content:space-between;animation:{anim("rise", .3, s + .06 + k * .045)}">'
                       f'<div class="mono" style="font-weight:700;font-size:24px;letter-spacing:.05em;color:rgba(253,253,255,.75)">MESA {n}</div>'
                       f'<div style="align-self:flex-start;padding:8px 18px 10px;border-radius:999px;background:{bgc};color:{fgc};font-weight:800;font-size:27px">{est}</div></div>')
        t_toast = s + (fr['e'] - fr['s']) * 0.45
        return (f'<div class="grid abs" style="inset:0;background-color:{ROJO}"></div>'
                f'<div class="abs" style="left:52px;top:286px;width:976px;height:930px;border-radius:44px;background:{TINTA};padding:40px;box-shadow:0 60px 110px -40px rgba(40,0,0,.8);animation:{anim("rise", .38, s)}">'
                f'<div style="display:flex;align-items:center;justify-content:space-between"><div class="hl" style="font-size:56px">Mesas en vivo</div>'
                f'<div class="mono" style="display:flex;align-items:center;gap:12px;font-weight:700;font-size:22px;letter-spacing:.06em"><i style="width:16px;height:16px;border-radius:50%;background:{ROJO};animation:{anim("pulse", .8, s, "ease-in-out", "infinite both")}"></i>EN VIVO</div></div>'
                f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:34px">{celdas}</div></div>'
                f'<div class="abs" style="left:96px;right:96px;top:1062px;padding:26px 32px;border-radius:28px;background:{LIMA};color:{TINTA};display:flex;align-items:center;gap:22px;box-shadow:0 30px 60px -20px rgba(0,0,0,.6);opacity:0;animation:{anim("rise", .32, t_toast)}">'
                f'<div style="width:64px;height:64px;border-radius:50%;background:{TINTA};display:flex;align-items:center;justify-content:center;flex:none"><svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="{LIMA}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div>'
                f'<div style="font-weight:800;font-size:34px;line-height:1.1">Mesa 4 pagó $62.000<div class="mono" style="font-size:20px;font-weight:700;letter-spacing:.05em;margin-top:6px">NEQUI · PEDIDO #014 A COCINA</div></div></div>')
    if t == 'mito':
        return (f'<div class="grid abs" style="inset:0;background-color:{TINTA}"></div>'
                f'<div class="abs hl" style="right:-40px;bottom:170px;font-size:1050px;line-height:.78;color:transparent;-webkit-text-stroke:5px rgba(253,253,255,.13);animation:{anim("rise", .5, s)}">{esc["paso"]}</div>'
                f'<div class="chip" style="background:{ROJO};color:{BLANCO};animation:{anim("pop", .3, s)}">Mentira {esc["paso"]}</div>'
                f'<div class="abs fit" data-w="952" data-max="118" data-maxh="400" id="cita{idx}" style="left:64px;top:400px;width:952px;font-weight:800;font-size:118px;line-height:1.04;letter-spacing:-.03em;animation:{anim("rise", .34, s + .04)}"><span class="qs">{e(esc["cita"])}</span></div>')
    if t == 'cta':
        mark_bg, mark_fg = LIMA, TINTA
        return (f'<div class="grid abs" style="inset:0;background-color:{ROJO}"></div>'
                f'<img src="{LOGO_B.as_uri()}" class="abs" style="left:50%;top:330px;height:120px;margin-left:-95px;width:190px;object-fit:contain;animation:{anim("pop", .34, s)}">'
                f'<div class="abs hl fit" data-w="952" data-max="140" style="left:64px;top:560px;width:952px;text-align:center;animation:{anim("rise", .36, s + .08)}">{lineas_hl(esc["lineas"], esc.get("resalta", -1), mark_bg, mark_fg)}</div>'
                f'<div class="abs" style="left:0;right:0;top:1010px;display:flex;justify-content:center;animation:{anim("pop", .34, s + .3)}"><div class="mono" style="padding:26px 46px;border-radius:999px;background:{LIMA};color:{TINTA};font-weight:700;font-size:38px;letter-spacing:-.01em;text-transform:uppercase;box-shadow:0 26px 50px -20px rgba(0,0,0,.5);animation:{anim("pulse", 1.1, s + .7, "ease-in-out", "infinite both")}">{e(esc["pill"])}</div></div>'
                f'<div class="abs mono" style="left:0;right:0;top:1150px;text-align:center;font-weight:700;font-size:30px;letter-spacing:.04em;animation:{anim("fadein", .3, s + .5)}">@menuo.app</div>')
    raise ValueError(t)

def extra_html(idx, x, fr, s):
    t = x['tipo']
    t0 = t_palabra(fr, x['palabra']) - .03 if 'palabra' in x else s + .05
    if t == 'sticker':
        bg = {'lima': LIMA, 'rojo': ROJO, 'blanco': BLANCO}[x.get('color', 'lima')]
        fg = TINTA if x.get('color', 'lima') in ('lima', 'blanco') else BLANCO
        fs = 70 if x.get('chico') else 104
        return f'<div class="stk" style="--r:{x.get("rot", -3)}deg;top:{x.get("top", 600)}px;font-size:{fs}px;background:{bg};color:{fg};opacity:0;animation:{anim("slam", .2, t0, "cubic-bezier(.5,0,.75,0)")}">{e(x["texto"])}</div>'
    if t == 'sinsenal':
        return (f'<div class="abs" style="--r:-6deg;right:84px;top:470px;width:250px;height:250px;border-radius:50%;background:{ROJO};display:flex;align-items:center;justify-content:center;box-shadow:0 30px 60px -20px rgba(0,0,0,.6);opacity:0;'
                f'animation:{anim("slam", .2, t0, "cubic-bezier(.5,0,.75,0)")},{anim("shake", .16, t0 + .22, "linear", "3 both")}">'
                f'<svg width="150" height="150" viewBox="0 0 24 24" fill="{BLANCO}"><rect x="3" y="15" width="3" height="5" rx="1"/><rect x="8" y="12" width="3" height="8" rx="1"/><rect x="13" y="8" width="3" height="12" rx="1" opacity=".45"/><rect x="18" y="4" width="3" height="16" rx="1" opacity=".45"/>'
                f'<path d="M3 3l18 18" stroke="{BLANCO}" stroke-width="2.6" stroke-linecap="round"/></svg></div>')
    if t == 'falso':
        return (f'<style>#cita{idx} .qs{{animation:{anim("strikebg", .24, t0)},{anim("dimtxt", .24, t0)}}}</style>'
                f'<div class="stk" style="--r:-8deg;left:auto;right:64px;top:770px;font-size:120px;background:{ROJO};color:{BLANCO};opacity:0;animation:{anim("slam", .2, t0, "cubic-bezier(.5,0,.75,0)")}">{e(x["texto"])}</div>')
    if t == 'realidad':
        return (f'<div class="abs" style="left:64px;width:952px;top:950px;padding:36px 42px 42px;border-radius:36px;background:{LIMA};color:{TINTA};box-shadow:0 30px 60px -20px rgba(0,0,0,.6);opacity:0;animation:{anim("rise", .34, t0)}">'
                f'<div class="mono" style="font-weight:700;font-size:26px;letter-spacing:.08em">REALIDAD</div>'
                f'<div style="font-weight:800;font-size:72px;line-height:1.04;letter-spacing:-.02em;margin-top:12px">{e(x["texto"])}</div></div>')
    raise ValueError(t)

def armar(reel_id, tl, dur):
    reel = REELS[reel_id]; frases = reel['frases']
    # escenas: cada frase con `escena` abre una; corte en el punto medio entre frases
    cortes = []
    for i, f in enumerate(frases):
        if 'escena' in f:
            c = 0.0 if i == 0 else (tl[i - 1]['e'] + tl[i]['s']) / 2
            cortes.append((i, c))
    escenas, ventanas = [], []
    for k, (i, c) in enumerate(cortes):
        fin = cortes[k + 1][1] if k + 1 < len(cortes) else dur
        j_fin = cortes[k + 1][0] if k + 1 < len(cortes) else len(frases)
        esc = frases[i]['escena']
        cuerpo = escena_html(k, esc, tl[i], c, fin - c, reel)
        for j in range(i, j_fin):
            for x in frases[j].get('extra', []):
                cj = c if j == i else (tl[j - 1]['e'] + tl[j]['s']) / 2
                cuerpo += extra_html(k, x, tl[j], cj)
        punch = f'animation:{anim("punch", .26, c)}' if k else ''
        escenas.append(f'<div class="sc" id="e{k}" style="{punch}">{cuerpo}</div>')
        ventanas.append([round(c, 3), round(fin, 3), esc.get('paso', 0)])
    # subtítulos: trozos de máximo 7 palabras, cortando en puntuación
    caps = []
    for i, f in enumerate(frases):
        if f.get('cap', True) is False: continue
        ws = tl[i]['words']; n = len(ws)
        partes = -(-n // 7); tam = n / partes; cortes, ini = [], 0
        for c in range(1, partes):
            ideal = int(round(c * tam)); mejor = ideal
            for dlt in (0, -1, 1, -2, 2):
                j = ideal + dlt
                if ini + 3 <= j <= n - 3 and re.search(r'[,:.…?!]["»]?$', ws[j - 1][0]): mejor = j; break
            cortes.append(mejor); ini = mejor
        for a, b in zip([0] + cortes, cortes + [n]): caps.append(ws[a:b])
    capjs = []
    for k, tr in enumerate(caps):
        s0 = tr[0][1] - 0.06
        e0 = tr[-1][2] + 0.35
        capjs.append(dict(s=round(s0, 3), e=round(e0, 3), w=[[w, round(a, 3), round(b, 3)] for w, a, b in tr]))
    for k in range(len(capjs) - 1):  # no solapar; tapar huecos cortos
        nxt = capjs[k + 1]['s']
        if capjs[k]['e'] > nxt or nxt - capjs[k]['e'] < 0.5: capjs[k]['e'] = nxt
    pasos = reel.get('pasos', 0)
    pasos_html = f'<div id="pasos">{"".join("<i><b></b></i>" for _ in range(pasos))}</div>' if pasos else ''
    data = json.dumps(dict(V=ventanas, C=capjs, P=pasos), ensure_ascii=False)
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Azeret+Mono:wght@500;700&display=swap">
<style>{CSS}</style></head><body><div id="c">{''.join(escenas)}
<img id="logo" src="{LOGO_B.as_uri()}"><span id="tag">{e(reel['tag'])}</span>{pasos_html}
<div id="cap"><div id="capin"></div></div></div>
<script>
const D={data};
const ease=x=>1-Math.pow(1-Math.min(Math.max(x,0),1),3);
let capAct=-1;
window.render=function(t){{
  document.getAnimations().forEach(a=>{{a.pause();a.currentTime=t*1000;}});
  let paso=0;
  D.V.forEach((v,i)=>{{const on=t>=v[0]&&t<v[1];document.getElementById('e'+i).style.visibility=on?'visible':'hidden';if(on)paso=v[2];}});
  if(D.P){{const p=document.getElementById('pasos');p.style.opacity=paso?1:0;
    [...p.querySelectorAll('b')].forEach((b,i)=>{{b.style.transform='scaleX('+(i+1<paso?1:(i+1==paso?1:0))+')';}});}}
  const ci=D.C.findIndex(c=>t>=c.s&&t<c.e), box=document.getElementById('capin');
  if(ci<0){{box.style.opacity=0;capAct=-1;return;}}
  const c=D.C[ci];
  if(ci!==capAct){{box.innerHTML='<span class="box">'+c.w.map((w,i)=>'<span class="w" id="w'+i+'">'+w[0]+'</span>').join(' ')+'</span>';capAct=ci;}}
  c.w.forEach((w,i)=>{{const el=document.getElementById('w'+i);el.className='w'+(t<w[1]-0.02?' f':(t<w[2]+0.08?' a':''));}});
  const k=ease((t-c.s)/0.14);box.style.opacity=k;box.style.transform='scale('+(0.9+0.1*k)+')';
}};
(async()=>{{await document.fonts.ready;
  for(const el of document.querySelectorAll('.fit')){{let s=+el.dataset.max;const w=+el.dataset.w,mh=+(el.dataset.maxh||9999);el.style.fontSize=s+'px';
    while((el.scrollWidth>w+1||el.scrollHeight>mh)&&s>40){{s-=2;el.style.fontSize=s+'px';}}}}
  await Promise.all([...document.images].map(i=>i.decode().catch(()=>{{}})));window.__ok=true;}})();
</script></body></html>'''

def render(reel_id, audio, out, portada=None, t_portada=None):
    frases = REELS[reel_id]['frases']
    tmp = SCR / f'reel2_{reel_id}'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    wav = tmp / 'voz.wav'
    if audio == '-':
        tl, fin_voz = estimar(frases)
        dur = fin_voz + COLA
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r={SR}:cl=mono', '-t', f'{dur:.3f}', str(wav)], check=True)
    else:
        tl, fin_voz = preparar_audio(audio, frases, str(wav))
        dur = fin_voz + COLA
    (pathlib.Path(out).with_suffix('.tiempos.json')).write_text(json.dumps(dict(dur=dur, frases=[dict(t=f['t'], **x) for f, x in zip(frases, tl)]), ensure_ascii=False, indent=1))
    for f, x in zip(frases, tl):
        print(f"{x['s']:6.2f}–{x['e']:6.2f}  {f['t']}")
    page = tmp / 'reel.html'; page.write_text(armar(reel_id, tl, dur), encoding='utf-8')
    frames = tmp / 'f'; frames.mkdir()
    n = int(round(dur * FPS))
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(page.as_uri(), wait_until='networkidle'); pg.wait_for_function('window.__ok===true', timeout=30000)
        for i in range(n):
            pg.evaluate(f'window.render({i / FPS:.4f})')
            pg.screenshot(path=str(frames / f'f{i:04d}.jpg'), type='jpeg', quality=90, clip=dict(x=0, y=0, width=1080, height=1920))
        if portada:
            pg.evaluate(f'window.render({(t_portada if t_portada is not None else 0.7):.3f})')
            pg.screenshot(path=portada, type='jpeg', quality=92, clip=dict(x=0, y=0, width=1080, height=1920))
        b.close()
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', str(frames / 'f%04d.jpg'), '-i', str(wav),
                    '-filter_complex', '[1:a]apad,aformat=channel_layouts=stereo[a]', '-map', '0:v', '-map', '[a]', '-t', f'{dur:.3f}',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS),
                    '-c:a', 'aac', '-b:a', '192k', '-ar', str(SR), '-movflags', '+faststart', out], check=True)
    print('ok', out, f'{dur:.2f}s', n, 'cuadros')
    return tl, dur

def muestras(reel_id, audio, out_jpg, por_frase=2):
    """Hoja de contacto: cuadros al inicio y a mitad de cada frase (para revisar sin renderizar todo)."""
    from PIL import Image, ImageDraw
    frases = REELS[reel_id]['frases']
    tmp = SCR / f'reel2_{reel_id}_m'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    if audio == '-': tl, fin = estimar(frases)
    else: tl, fin = preparar_audio(audio, frases, str(tmp / 'voz.wav'))
    dur = fin + COLA
    ts = [0.0, 0.14]
    for x in tl:
        ts += [x['s'] + 0.25, x['s'] + (x['e'] - x['s']) * 0.85]
    ts = sorted(set(round(t, 2) for t in ts if t < dur))
    page = tmp / 'reel.html'; page.write_text(armar(reel_id, tl, dur), encoding='utf-8')
    ims = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(page.as_uri(), wait_until='networkidle'); pg.wait_for_function('window.__ok===true', timeout=30000)
        for t in ts:
            pg.evaluate(f'window.render({t:.3f})')
            f = tmp / f'm{t:06.2f}.jpg'; pg.screenshot(path=str(f), type='jpeg', quality=80, clip=dict(x=0, y=0, width=1080, height=1920)); ims.append((t, f))
        b.close()
    W, H, cols = 270, 480, 6
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (W * cols, (H + 26) * rows), 'white'); d = ImageDraw.Draw(sheet)
    for k, (t, f) in enumerate(ims):
        im = Image.open(f).resize((W, H)); x, y = (k % cols) * W, (k // cols) * (H + 26)
        sheet.paste(im, (x, y)); d.text((x + 6, y + H + 6), f'{t:.2f}s', fill='black')
    sheet.save(out_jpg, quality=82)
    print('hoja', out_jpg, len(ims), 'cuadros', f'{dur:.2f}s')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('reel'); ap.add_argument('audio'); ap.add_argument('out')
    ap.add_argument('--portada'); ap.add_argument('--t-portada', type=float)
    ap.add_argument('--muestras', action='store_true')
    a = ap.parse_args()
    if a.muestras: muestras(a.reel, a.audio, a.out)
    else: render(a.reel, a.audio, a.out, a.portada, a.t_portada)
