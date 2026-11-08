"""Promos animados de Menuo (motion graphics, sin fotos de stock): texto cinético sincronizado con la voz + la app en movimiento.

Uso:
  python3 promo.py <promo> <audio.mp3|-> <salida.mp4> [--portada portada.jpg] [--t-portada 0.6]
  python3 promo.py <promo> <audio.mp3|-> <hoja.jpg> --muestras
<promo> es una clave de guiones_promo.PROMOS. Con '-' arma una versión muda con tiempos estimados.
"""
import os, sys, re, json, html, pathlib, subprocess, shutil, argparse
from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from guiones_promo import PROMOS
from reel2 import estimar, preparar_audio, palabras, qr_svg, KIT, SCR, FPS, SR

COLA = 0.8
e = html.escape
LOGO_B = (KIT / 'menuo-logo-blanco.svg').as_uri()
LOGO_T = (KIT / 'menuo-logo-tinta.svg').as_uri()
FOTO = lambda i: (KIT / 'fotos' / f'{i}.jpg').as_uri()

def norm(w): return re.sub(r'[^\wáéíóúüñ]', '', w.lower())

# ------------------------------------------------------------------ visuales (HTML con data-in / data-out por evento)
def ck(color='#1A1B1F', w=26):
    return f'<svg width="{w}" height="{w}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'

def tap(ev, x, y):
    """Dedo que toca en (x, y) del teléfono cuando ocurre `ev`."""
    return f'<div class="tap" data-tap="{ev}" style="left:{x - 32}px;top:{y - 32}px"><i></i></div>'

ITEMS = [  # nombre ES, nombre EN, descripción ES, descripción EN, precio, foto
    ('Hamburguesa de la casa', 'House burger', 'Doble carne, queso y papas', 'Double patty, cheese & fries', '$32.000', '15010285'),
    ('Pizza margarita', 'Margherita pizza', 'Tomate, mozzarella y albahaca', 'Tomato, mozzarella & basil', '$38.000', '14965994'),
    ('Soda de maracuyá', 'Passion fruit soda', 'Maracuyá natural con soda', 'Fresh passion fruit & soda', '$12.000', '5947109'),
]

def v_telefono():
    qr = qr_svg('https://menuo.com.co', 168)
    cam = f'''<div class="scr" style="background:radial-gradient(120% 80% at 50% 40%,#3a3b42 0%,#16171b 70%)">
  <div class="abs" style="left:24px;right:24px;top:540px;height:260px;border-radius:30px;background:linear-gradient(180deg,#5a3a2a,#3b261b);opacity:.55"></div>
  <div class="abs tent">
    <img src="{LOGO_T}" style="height:26px;display:block;margin:0 auto 10px">
    <div style="background:#fff;padding:10px;border-radius:14px;display:inline-block">{qr}</div>
    <div style="font-weight:800;font-size:17px;margin-top:10px">Escanea para pedir</div>
    <div class="mono" style="font-size:12px;letter-spacing:.08em;margin-top:2px;color:#F42902">MESA 4</div></div>
  <div class="abs scanframe"></div><div class="abs scanline" data-scan="1"></div>
  <div class="abs linkpill" data-in="link:pop:.28:0" data-out="menu:fade:.15">
    <span style="width:30px;height:30px;border-radius:9px;background:#F42902;display:inline-flex;align-items:center;justify-content:center;flex:none"><img src="{LOGO_B}" style="height:12px"></span>
    <span style="flex:1;line-height:1.15"><b style="font-size:15px">menuo.app</b><br><span style="font-size:12px;opacity:.7">Mesa 4 · Abrir el menú</span></span><span style="font-weight:800;color:#0a84ff;font-size:15px">Abrir</span></div>
  {tap('menu', 195, 128)}
</div>'''
    items, taps_menu = '', []
    for k, (es, en, des, den, pr, foto) in enumerate(ITEMS):
        add = {0: 'add1', 2: 'add2'}.get(k)
        y_btn = 268 + k * 128 + 66
        boton = (f'<div class="plus"><span>+</span>' + (f'<span class="plus1" data-in="{add}:pop:.25:0">1</span>' if add else '') + '</div>')
        items += f'''<div class="item"><div class="thumb" style="background-image:url({FOTO(foto)})"></div>
  <div style="flex:1;min-width:0;position:relative;height:96px">
    <div class="abs" style="inset:0" data-out="en:fade:.15"><div class="iname">{e(es)}</div><div class="idesc">{e(des)}</div></div>
    <div class="abs" style="inset:0" data-in="en:fade:.18:0"><div class="iname">{e(en)}</div><div class="idesc">{e(den)}</div></div>
    <div class="iprice">{pr}</div></div>{boton}</div>'''
        if add: taps_menu.append(tap(add, 316, 250 + k * 128 + 80))
    menu = f'''<div class="scr" data-in="menu:slidel:.34:0" style="background-color:#F42902" >
  <div class="grid abs" style="inset:0"></div>
  <img src="{LOGO_B}" class="abs" style="left:22px;top:58px;height:30px">
  <div class="abs lang"><span class="on">ES</span><span>EN</span><span class="abs on2" data-in="en:fade:.15:0">EN</span></div>
  <div class="abs mono" style="right:22px;top:58px;padding:7px 12px;border-radius:999px;border:1.5px solid rgba(253,253,255,.6);font-size:12px;font-weight:700">MESA 4</div>
  <div class="abs mtitle" data-out="en:fade:.15">¿Qué se te<br>antoja?</div>
  <div class="abs mtitle" data-in="en:fade:.18:0">What are you<br>craving?</div>
  <div class="abs chips"><span class="on">Fuertes</span><span>Bebidas</span><span>Postres</span></div>
  <div class="abs" style="left:16px;right:16px;top:250px;display:flex;flex-direction:column;gap:14px">{items}</div>
  <div class="abs cart" data-in="add1:slideup:.3:0" data-out="add2:fade:.12"><div><b>Ver pedido</b><div class="mono" style="font-size:11px;letter-spacing:.06em;opacity:.75">1 PRODUCTO</div></div><b style="margin-left:auto">$32.000</b><span class="go">→</span></div>
  <div class="abs cart" data-in="add2:fade:.12:0"><div><b>Ver pedido</b><div class="mono" style="font-size:11px;letter-spacing:.06em;opacity:.75">2 PRODUCTOS</div></div><b style="margin-left:auto">$44.000</b><span class="go">→</span></div>
  {tap('sheet', 331, 762)}{''.join(taps_menu)}
</div>'''
    metodos = ''
    for k, (nom, ev) in enumerate([('Tarjeta', 'm_tarjeta'), ('PSE', 'm_pse'), ('Nequi', 'm_nequi'), ('Bancolombia', 'm_banco')]):
        sel = '<div class="abs msel" data-in="sel:fade:.15:0"></div>' if nom == 'Nequi' else ''
        metodos += f'<div class="met">{sel}<div class="abs mflash" data-in="{ev}:fade:.1:0" data-out="sel:fade:.2"></div><span style="position:relative">{nom}</span></div>'
    hoja = f'''<div class="abs dim" data-in="sheet:fade:.25:0"></div>
<div class="abs sheet" data-in="sheet:slideup:.36:0">
  <div style="width:44px;height:5px;border-radius:5px;background:#d6d6dc;margin:0 auto 16px"></div>
  <div style="display:flex;justify-content:space-between;align-items:baseline"><div style="font-weight:900;font-size:26px;letter-spacing:-.02em">Tu pedido</div><div class="mono" style="font-size:12px;font-weight:700;color:#F42902">MESA 4</div></div>
  <div class="row"><span>1 · Hamburguesa de la casa</span><span>$32.000</span></div>
  <div class="row"><span>1 · Soda de maracuyá</span><span>$12.000</span></div>
  <div class="row tot"><span>Total</span><span>$44.000</span></div>
  <div style="font-weight:800;font-size:15px;margin:16px 0 10px">¿Cómo quieres pagar?</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">{metodos}</div>
  <div class="paybtn" data-pulse="sel">Pagar $44.000</div>
  {tap('pay', 195, 556)}
</div>
<div class="scr ok" data-in="ok:zoom:.3:0">
  <div style="width:120px;height:120px;border-radius:50%;background:#1A1B1F;display:flex;align-items:center;justify-content:center" data-in="ok:pop:.35:.1">{ck('#C9FB00', 64)}</div>
  <div style="font-weight:900;font-stretch:104%;font-size:46px;text-transform:uppercase;letter-spacing:-.03em;margin-top:22px">¡Pagado!</div>
  <div class="mono" style="font-size:14px;font-weight:700;margin-top:8px;letter-spacing:.04em">NEQUI · $44.000</div>
  <div style="font-size:15px;font-weight:600;margin-top:26px;padding:10px 16px;border-radius:14px;background:rgba(26,27,31,.08)">Mesa 4 · Tu pedido ya va para cocina</div>
</div>'''
    return f'''<div class="abs phone" style="left:355px;top:650px"><div class="screen">{cam}{menu}{hoja}</div><div class="island"></div></div>'''

def v_panel():
    mesas = [('1', 'Libre', 'l', None), ('2', 'Pidiendo', 'r', 'p_pide'), ('4', 'Por pagar', 'w', 'p_pago'),
             ('5', 'En cocina', 't', None), ('7', 'Libre', 'l', None), ('9', 'En cocina', 't', None)]
    col = {'l': ('#EFEFF2', '#8A8A94'), 'r': ('#F42902', '#FDFDFF'), 'w': ('#FFE9E4', '#F42902'), 't': ('#1A1B1F', '#FDFDFF')}
    celdas = ''
    for n, est, c, ev in mesas:
        bg, fg = col[c]
        extra = ''
        if ev == 'p_pide':
            extra = '<div class="abs ring" data-in="p_pide:pop:.25:0" data-pulse="p_pide"></div>'
        if ev == 'p_pago':
            extra = (f'<div class="abs" style="left:18px;bottom:18px;padding:6px 12px 7px;border-radius:999px;background:#C9FB00;color:#1A1B1F;font-weight:800;font-size:17px;display:flex;gap:6px;align-items:center" data-in="p_pago:pop:.3:0">{ck("#1A1B1F", 16)}Pagado</div>'
                     '<div class="abs ring lime" data-in="p_pago:pop:.25:0"></div>')
        celdas += (f'<div class="mesa"><div class="mono" style="font-size:14px;font-weight:700;letter-spacing:.06em;color:#8A8A94">MESA</div>'
                   f'<div style="font-weight:900;font-size:44px;line-height:1;letter-spacing:-.03em">{n}</div>'
                   f'<div class="est" style="background:{bg};color:{fg}">{est}</div>{extra}</div>')
    return f'''<div class="abs tablet"><div class="tscreen">
  <div style="display:flex;align-items:center;gap:14px;padding:22px 26px 10px"><img src="{LOGO_T}" style="height:26px"><div style="font-weight:900;font-size:26px;letter-spacing:-.02em;margin-left:6px">Mesas en vivo</div>
    <div class="mono" style="margin-left:auto;display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;letter-spacing:.06em;color:#F42902"><i class="live"></i>EN VIVO · 8:14 P. M.</div></div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;padding:6px 26px">{celdas}</div>
  <div style="padding:16px 26px 0;font-weight:900;font-size:20px;letter-spacing:-.01em">Pedidos</div>
  <div class="abs" style="left:26px;right:26px;top:520px;display:flex;flex-direction:column;gap:12px">
    <div class="pcard" data-in="p_pago:rise:.3:0" style="background:#C9FB00"><div class="mono pm">MESA 4</div><div style="flex:1"><b>Hamburguesa + Soda</b><div class="ps">Nequi · $44.000</div></div><div class="pst" style="background:#1A1B1F;color:#C9FB00">{ck('#C9FB00', 16)} Pagado</div></div>
    <div class="pcard"><div class="mono pm">MESA 9</div><div style="flex:1"><b>2 × Pizza margarita</b><div class="ps">Tarjeta · $76.000</div></div>
      <div class="pst" style="background:#EFEFF2;color:#1A1B1F" data-out="p_cocina:fade:.15">Pagado</div><div class="pst abs" style="right:16px;background:#1A1B1F;color:#FDFDFF" data-in="p_cocina:pop:.25:0">→ Cocina</div>
      <div class="abs ring" style="inset:-6px;border-radius:24px" data-in="p_cocina:pop:.25:0"></div></div>
    <div class="pcard"><div class="mono pm">MESA 5</div><div style="flex:1"><b>Limonada × 3</b><div class="ps">PSE · $27.000</div></div><div class="pst" style="background:#1A1B1F;color:#FDFDFF">En cocina</div></div>
  </div>
  <div class="abs toast" data-in="p_pago:slidedown:.3:.15">{ck('#C9FB00', 20)}<span><b>Mesa 4 pagó $44.000</b> · Nequi</span></div>
</div></div>'''

def v_espera():
    burbujas = [('b1', 'Mesa 2', 'La cuenta, por favor', '8:02 p. m.'), ('b2', 'Mesa 7', '¿Nos cobras?', '8:09 p. m.'), ('b3', 'Mesa 4', 'Llevamos rato esperando', '8:16 p. m.')]
    out = ''
    for k, (ev, m, txt, h) in enumerate(burbujas):
        out += (f'<div class="abs burbuja" style="top:{700 + k * 140}px;--r:{(-1.5, 1.2, -0.8)[k]}deg" data-in="{ev}:pop:.3:0" data-shake="alerta">'
                f'<div class="av">{m.split()[1]}</div><div style="flex:1"><div class="mono" style="font-size:20px;font-weight:700;letter-spacing:.06em;color:#C9FB00">{m.upper()}</div>'
                f'<div style="font-weight:800;font-size:36px;letter-spacing:-.015em">{e(txt)}</div></div><div class="mono" style="font-size:20px;opacity:.6">{h}</div></div>')
    out += ('<div class="abs" style="left:0;right:0;top:1100px;text-align:center" data-in="timer:zoom:.25:0">'
            '<div class="timer" data-count="timer:0:840:1.6:mmss">00:00</div><div class="mono" style="font-size:24px;font-weight:700;letter-spacing:.1em;color:rgba(253,253,255,.7)">MINUTOS ESPERANDO</div></div>'
            '<div class="abs" style="left:0;right:0;top:1350px;display:flex;justify-content:center" data-in="alerta:slam:.22:0"><div class="alerta">3 mesas esperando la cuenta</div></div>')
    return out

def v_cocina():
    filas = ['1 · Hamburguesa de la casa', '1 · Soda de maracuyá']
    return f'''<div class="abs" style="left:180px;top:700px;width:720px;height:40px;border-radius:20px;background:#0E0F12;box-shadow:0 0 0 2px rgba(253,253,255,.12)"></div>
<div class="abs" style="left:200px;top:720px;width:680px;height:780px;overflow:hidden">
  <div class="abs ticket mono" data-in="print:drop:.9:0">
    <div style="display:flex;justify-content:space-between;font-weight:700;letter-spacing:.06em"><span>MESA 4</span><span>#014</span></div>
    <div class="dash"></div>{''.join(f'<div>{f}</div>' for f in filas)}<div class="dash"></div>
    <div style="display:flex;justify-content:space-between;font-weight:700"><span>TOTAL $44.000</span><span>8:14 P. M.</span></div>
    <div style="margin-top:14px;font-size:20px;opacity:.6">Nequi · Mesa 4</div>
    <div class="abs sello" data-in="stamp:slam:.2:0">PAGADO</div>
  </div></div>'''

def v_logo(promo):
    return f'''<img src="{LOGO_B}" class="abs" style="left:50%;top:700px;width:400px;margin-left:-200px" data-in="logo:slam:.3:0">
<div class="abs" style="left:60px;right:60px;top:990px;text-align:center;font-weight:900;font-stretch:104%;text-transform:uppercase;font-size:78px;line-height:.95;letter-spacing:-.035em" data-in="logo:rise:.35:.2">{e(promo["lema"])}</div>
<div class="abs" style="left:0;right:0;top:1190px;display:flex;justify-content:center" data-in="cta:pop:.3:0"><div class="ctapill" data-pulse="cta">{e(promo["pill"])}</div></div>
<div class="abs mono" style="left:0;right:0;top:1320px;text-align:center;font-weight:700;font-size:30px;letter-spacing:.05em" data-in="cta:fade:.3:.2">@menuo.app</div>'''

CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000}
#c{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:Archivo,Arial,sans-serif;color:#FDFDFF;background:#1A1B1F}
.abs{position:absolute}
.mono{font-family:'Azeret Mono',monospace}
.grid{background-image:linear-gradient(rgba(253,253,255,.09) 1px,transparent 1px),linear-gradient(90deg,rgba(253,253,255,.09) 1px,transparent 1px);background-size:72px 72px}
#bgred{position:absolute;inset:0;background-color:#F42902;opacity:0}
.glow{position:absolute;border-radius:50%;filter:blur(120px)}
#stage{position:absolute;inset:0;transform-origin:540px 1080px}
.vis{position:absolute;inset:0;visibility:hidden}
#topfade{position:absolute;left:0;right:0;top:0;height:690px;background:linear-gradient(180deg,rgba(26,27,31,.96) 0%,rgba(26,27,31,.9) 62%,rgba(26,27,31,0) 100%)}
#logo{position:absolute;left:64px;top:150px;height:44px;z-index:40}
.kt{position:absolute;left:70px;right:70px;display:flex;flex-direction:column;justify-content:center;font-weight:900;font-stretch:104%;text-transform:uppercase;letter-spacing:-.035em;line-height:.98;z-index:30;visibility:hidden}
.kt.top{top:236px;height:380px}
.kt.centro{top:420px;height:1000px;text-align:center;align-items:center}
.kt .in{display:block}
.kt .w{display:inline-block;margin-right:.18em}
.kt .w.m{background:#C9FB00;color:#1A1B1F;padding:0 .1em;border-radius:.1em;margin-right:.24em}
/* teléfono */
.phone{width:390px;height:844px;border-radius:58px;background:#0E0F12;padding:12px;transform-origin:0 0;transform:scale(.95);box-shadow:0 60px 120px -40px rgba(0,0,0,.9),0 0 0 2px rgba(253,253,255,.14)}
.screen{position:relative;width:100%;height:100%;border-radius:46px;overflow:hidden;background:#000}
.scr{position:absolute;inset:0;overflow:hidden;color:#FDFDFF}
.island{position:absolute;left:50%;top:22px;width:112px;height:32px;margin-left:-56px;border-radius:20px;background:#000}
.tent{left:95px;top:250px;width:176px;padding:16px 14px 14px;border-radius:22px;background:#FDFDFF;color:#1A1B1F;text-align:center;box-shadow:0 30px 50px -20px rgba(0,0,0,.8)}
.scanframe{left:93px;top:290px;width:180px;height:180px;border:5px solid #C9FB00;border-radius:24px;box-shadow:0 0 30px rgba(201,251,0,.35)}
.scanline{left:100px;width:166px;height:4px;border-radius:4px;background:#C9FB00;box-shadow:0 0 18px 5px rgba(201,251,0,.55);top:300px}
.linkpill{left:14px;right:14px;top:66px;height:64px;border-radius:20px;background:rgba(245,245,247,.92);color:#1A1B1F;display:flex;align-items:center;gap:12px;padding:0 16px;box-shadow:0 20px 40px -14px rgba(0,0,0,.6)}
.lang{left:132px;top:58px;display:flex;border-radius:999px;background:rgba(26,27,31,.35);padding:3px;font-family:'Azeret Mono',monospace;font-weight:700;font-size:12px}
.lang span{padding:6px 10px;border-radius:999px}
.lang .on{background:#C9FB00;color:#1A1B1F}
.lang .on2{right:3px;top:3px;background:#C9FB00;color:#1A1B1F}
.mtitle{left:22px;top:112px;font-weight:900;font-stretch:104%;text-transform:uppercase;font-size:38px;line-height:.92;letter-spacing:-.03em}
.chips{left:16px;top:200px;display:flex;gap:8px}
.chips span{padding:8px 16px;border-radius:999px;border:1.5px solid rgba(253,253,255,.7);font-weight:700;font-size:15px}
.chips .on{background:#C9FB00;border-color:#C9FB00;color:#1A1B1F}
.item{display:flex;align-items:center;gap:12px;height:114px;padding:9px;border-radius:22px;background:#FDFDFF;color:#1A1B1F;box-shadow:0 10px 24px -12px rgba(60,0,0,.5)}
.thumb{width:96px;height:96px;border-radius:16px;background-size:cover;background-position:center;flex:none}
.iname{font-weight:800;font-size:17px;letter-spacing:-.01em;line-height:1.1}
.idesc{font-size:12.5px;color:#6b6b74;margin-top:4px;line-height:1.2}
.iprice{position:absolute;left:0;bottom:2px;font-weight:800;font-size:16px}
.plus{position:relative;width:42px;height:42px;border-radius:50%;background:#F42902;color:#fff;font-weight:700;font-size:26px;display:flex;align-items:center;justify-content:center;flex:none;align-self:flex-end;margin:0 4px 4px 0}
.plus1{position:absolute;inset:0;border-radius:50%;background:#C9FB00;color:#1A1B1F;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:900}
.cart{left:14px;right:14px;bottom:24px;height:68px;border-radius:999px;background:#1A1B1F;color:#FDFDFF;display:flex;align-items:center;gap:12px;padding:0 10px 0 24px;font-size:17px;box-shadow:0 20px 40px -14px rgba(0,0,0,.6)}
.go{width:50px;height:50px;border-radius:50%;background:#C9FB00;color:#1A1B1F;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:22px}
.dim{inset:0;background:rgba(10,10,12,.5)}
.sheet{left:0;right:0;bottom:0;height:600px;border-radius:30px 30px 0 0;background:#FDFDFF;color:#1A1B1F;padding:12px 22px 30px}
.row{display:flex;justify-content:space-between;font-size:15px;padding:9px 0;border-bottom:1px solid #ececf0}
.row.tot{font-weight:900;font-size:22px;border-bottom:0;padding-top:12px}
.met{position:relative;height:56px;border-radius:16px;border:1.5px solid #e2e2e8;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px;overflow:hidden}
.msel{inset:0;background:#C9FB00}
.mflash{inset:0;border:3px solid #F42902;border-radius:16px}
.paybtn{margin-top:16px;height:60px;border-radius:999px;background:#1A1B1F;color:#FDFDFF;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px}
.ok{background:#C9FB00;color:#1A1B1F;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:30px}
.tap{position:absolute;width:64px;height:64px;border-radius:50%;background:rgba(253,253,255,.55);border:3px solid rgba(255,255,255,.95);box-shadow:0 6px 20px rgba(0,0,0,.35);opacity:0;z-index:20}
.tap i{position:absolute;inset:-3px;border-radius:50%;border:3px solid #FDFDFF;opacity:0}
/* panel */
.tablet{left:110px;top:650px;width:860px;height:820px;border-radius:44px;background:#0E0F12;padding:16px;box-shadow:0 60px 120px -40px rgba(0,0,0,.9),0 0 0 2px rgba(253,253,255,.14)}
.tscreen{position:relative;width:100%;height:100%;border-radius:30px;background:#F7F7F9;color:#1A1B1F;overflow:hidden}
.live{width:12px;height:12px;border-radius:50%;background:#F42902;display:inline-block}
.mesa{position:relative;height:178px;border-radius:22px;background:#FDFDFF;box-shadow:0 2px 0 rgba(26,27,31,.05),0 10px 24px -16px rgba(26,27,31,.3);padding:16px 18px}
.est{position:absolute;left:18px;bottom:18px;padding:6px 12px 7px;border-radius:999px;font-weight:800;font-size:17px}
.ring{inset:-5px;border-radius:26px;border:5px solid #F42902}
.ring.lime{border-color:#C9FB00}
.pcard{position:relative;display:flex;align-items:center;gap:16px;height:72px;border-radius:20px;background:#FDFDFF;padding:0 16px;box-shadow:0 10px 24px -16px rgba(26,27,31,.3);font-size:19px}
.pm{font-size:14px;font-weight:700;letter-spacing:.05em;padding:6px 10px;border-radius:10px;background:#1A1B1F;color:#FDFDFF}
.ps{font-size:14px;color:#6b6b74;margin-top:2px}
.pst{display:flex;align-items:center;gap:6px;padding:7px 14px 8px;border-radius:999px;font-weight:800;font-size:15px}
.toast{left:120px;right:120px;top:16px;height:64px;border-radius:20px;background:#1A1B1F;color:#FDFDFF;display:flex;align-items:center;gap:12px;padding:0 20px;font-size:19px;box-shadow:0 20px 40px -14px rgba(0,0,0,.5)}
/* espera */
.burbuja{left:80px;right:80px;height:118px;border-radius:30px;background:rgba(253,253,255,.08);border:1.5px solid rgba(253,253,255,.18);backdrop-filter:blur(18px);display:flex;align-items:center;gap:22px;padding:0 30px}
.av{width:68px;height:68px;border-radius:50%;background:#F42902;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:32px;flex:none}
.timer{font-weight:900;font-stretch:104%;font-size:200px;line-height:1;letter-spacing:-.04em;color:#F42902;font-variant-numeric:tabular-nums}
.alerta{padding:20px 36px;border-radius:999px;background:#F42902;font-weight:900;font-stretch:104%;text-transform:uppercase;font-size:40px;letter-spacing:-.02em}
/* cocina */
.ticket{left:0;top:0;width:680px;padding:46px 50px 64px;background:#FDFDFF;color:#1A1B1F;font-size:28px;line-height:1.6;font-weight:500;border-radius:0 0 12px 12px;box-shadow:0 40px 80px -30px rgba(0,0,0,.8)}
.dash{border-top:3px dashed rgba(26,27,31,.3);margin:16px 0}
.sello{--r:-12deg;left:110px;top:170px;padding:6px 26px 12px;border:10px solid #F42902;border-radius:22px;color:#F42902;font-family:Archivo;font-weight:900;font-stretch:104%;font-size:104px;letter-spacing:-.03em;line-height:1;background:rgba(253,253,255,.85)}
.ctapill{padding:28px 50px;border-radius:999px;background:#C9FB00;color:#1A1B1F;font-family:'Azeret Mono',monospace;font-weight:700;font-size:38px;text-transform:uppercase;box-shadow:0 26px 50px -20px rgba(0,0,0,.6)}
"""

JS = r"""
const D=__DATA__;
const cl=x=>Math.min(1,Math.max(0,x)), eo=x=>1-Math.pow(1-cl(x),3), eio=x=>{x=cl(x);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;};
const eb=x=>{x=cl(x);const c1=1.9,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);};
let T=0;
const els=[...document.querySelectorAll('[data-in],[data-out],[data-pulse],[data-shake]')];
const taps=[...document.querySelectorAll('[data-tap]')], counts=[...document.querySelectorAll('[data-count]')];
const vis=[...document.querySelectorAll('.vis')], kts=[...document.querySelectorAll('.kt')];
function at(ev){return D.EV.hasOwnProperty(ev)?D.EV[ev]:null;}
function anim(el){
  let op=1,tx=0,ty=0,txp=0,typ=0,sc=1;
  const r=parseFloat(getComputedStyle(el).getPropertyValue('--r'))||0;
  if(el.dataset.in){const [ev,a,d,o]=el.dataset.in.split(':');const t0=at(ev);
    if(t0===null){op=0;}else{const k=(T-t0-parseFloat(o||0))/parseFloat(d);
      if(k<0){op=0;}else{
        if(a==='fade')op*=eo(k);
        else if(a==='pop'){sc*=.45+.55*eb(k);op*=cl(k*3);}
        else if(a==='rise'){ty+=(1-eo(k))*70;op*=cl(k*2.5);}
        else if(a==='slideup'){typ+=(1-eo(k))*100;}
        else if(a==='slidedown'){typ-=(1-eo(k))*160;}
        else if(a==='slidel'){txp+=(1-eo(k))*100;}
        else if(a==='drop'){typ-=(1-eio(k))*100;}
        else if(a==='slam'){sc*=1+1.4*(1-eo(k));op*=cl(k*4);}
        else if(a==='zoom'){sc*=.9+.1*eo(k);op*=eo(k);}}}}
  if(el.dataset.out){const [ev,a,d]=el.dataset.out.split(':');const t0=at(ev);
    if(t0!==null&&T>=t0){const k=eo((T-t0)/parseFloat(d));op*=1-k;if(a==='up')ty-=k*50;}}
  if(el.dataset.pulse){const t0=at(el.dataset.pulse);if(t0!==null&&T>t0)sc*=1+.035*Math.sin((T-t0)*8);}
  if(el.dataset.shake){const t0=at(el.dataset.shake);if(t0!==null&&T>t0)tx+=12*Math.sin((T-t0)*42)*Math.max(0,1-(T-t0)/.6);}
  el.style.opacity=op;
  el.style.transform=`translate(${txp}%,${typ}%) translate(${tx}px,${ty}px) scale(${sc}) rotate(${r}deg)`;
}
window.render=function(t){T=t;
  // fondo
  let red=0;D.RED.forEach(([s,e])=>{if(T>=s&&T<e)red=Math.min(eo((T-s)/.14),eo((e-T)/.12));});
  document.getElementById('bgred').style.opacity=red;
  document.getElementById('topfade').style.opacity=1-red;
  document.getElementById('g1').style.transform=`translate(${Math.sin(T*.5)*80}px,${Math.cos(T*.4)*60}px)`;
  document.getElementById('g2').style.transform=`translate(${Math.cos(T*.45)*90}px,${Math.sin(T*.35)*70}px)`;
  // visuales
  let logoOn=false;
  vis.forEach(v=>{const W=D.WIN[v.dataset.vis]||[];let on=null;W.forEach(w=>{if(T>=w[0]&&T<w[1])on=w;});
    if(!on){v.style.visibility='hidden';return;}
    if(v.dataset.vis==='logo')logoOn=true;
    v.style.visibility='visible';const ki=on[0]<.01?1:eo((T-on[0])/.32),ko=eo((on[1]-T)/.16);
    v.style.opacity=Math.min(ki,ko);v.style.transform=`scale(${.9+.1*ki})`;v.style.transformOrigin='540px 1080px';});
  document.getElementById('logo').style.opacity=logoOn?0:1;
  // cámara
  let c=D.CAM[0].slice(1);for(let i=1;i<D.CAM.length;i++){const k=D.CAM[i];if(T>=k[0]){const p=eio((T-k[0])/.6);c=c.map((v,j)=>v+(k[j+1]-v)*p);}}
  const [s,fx,fy]=c, fl=Math.sin(T*1.3)*6;
  document.getElementById('stage').style.transform=`translate(${-s*(fx-540)}px,${-s*(fy-1080)+fl}px) scale(${s})`;
  // elementos por evento
  els.forEach(anim);
  taps.forEach(el=>{const t0=at(el.dataset.tap);if(t0===null){el.style.opacity=0;return;}
    const a=T-(t0-.32);let op=0,sc=1;if(a>=0&&a<.8){op=Math.min(cl(a/.15),cl((.8-a)/.2));sc=T<t0?1.15-.15*cl(a/.3):(T<t0+.12?.8:1);}
    el.style.opacity=op;el.style.transform=`scale(${sc})`;const ring=el.querySelector('i');const b=T-t0;
    ring.style.opacity=(b>0&&b<.45)?1-b/.45:0;ring.style.transform=`scale(${1+b*2.6})`;});
  counts.forEach(el=>{const [ev,a,b,d,f]=el.dataset.count.split(':');const t0=at(ev);let v=+a;if(t0!==null&&T>t0)v=+a+(+b-+a)*eo((T-t0)/+d);
    v=Math.round(v);el.textContent=f==='mmss'?String(Math.floor(v/60)).padStart(2,'0')+':'+String(v%60).padStart(2,'0'):v;});
  document.querySelectorAll('[data-scan]').forEach(el=>{el.style.top=(300+Math.abs(Math.sin(T*2.2))*160)+'px';});
  // texto cinético
  kts.forEach(k=>{const s=+k.dataset.s,e=+k.dataset.e;if(T<s||T>=e){k.style.visibility='hidden';return;}
    k.style.visibility='visible';const ko=cl((e-T)/.12);k.style.opacity=ko;
    const p=eo((T-s)/.3);k.style.transform=k.classList.contains('centro')?`scale(${1.05-.05*p})`:`translateY(${(1-ko)*-30}px)`;
    k.querySelectorAll('.w').forEach(w=>{const q=(T-+w.dataset.t+.04)/.17;w.style.opacity=cl(q*2.5);w.style.transform=`translateY(${(1-eo(q))*.45}em)`;});});
};
(async()=>{await document.fonts.ready;
  kts.forEach(k=>{k.style.visibility='visible';const mx=k.classList.contains('centro')?168:122;const H=k.classList.contains('centro')?900:380;let s=mx;k.style.fontSize=s+'px';
    const inn=k.querySelector('.in');while((inn.offsetHeight>H||[...k.querySelectorAll('.w')].some(w=>w.offsetWidth>940))&&s>48){s-=2;k.style.fontSize=s+'px';}k.style.visibility='hidden';});
  await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));
  document.querySelectorAll('.thumb').forEach(()=>{});
  window.__ok=true;})();
"""

def armar(pid, tl, dur):
    pr = PROMOS[pid]; frases = pr['frases']
    cortes = [0.0] + [(tl[i - 1]['e'] + tl[i]['s']) / 2 for i in range(1, len(frases))] + [dur]
    EV, WIN, CAM, RED, kt_html = {}, {}, [], [], ''
    actual, ini = None, 0.0
    for i, f in enumerate(frases):
        s, e_ = cortes[i], cortes[i + 1]
        ws = tl[i]['words']
        if 'vis' in f and f['vis'] != actual:
            if actual: WIN.setdefault(actual, []).append([round(ini, 3), round(s, 3)])
            actual, ini = f['vis'], s
            if actual == 'logo': EV['logo'] = s + .05
        for ev, k in f.get('ev', {}).items():
            EV[ev] = round(ws[min(k, len(ws) - 1)][1] - .04, 3)
        if 'cam' in f: CAM.append([round(s, 3), f['cam']['s'], *f['cam']['f']])
        for ev, cm in f.get('cam_ev', {}).items():
            if ev in EV: CAM.append([EV[ev], cm['s'], *cm['f']])
        if f.get('fondo') == 'rojo': RED.append([round(s, 3), round(e_, 3)])
        if f.get('kt', True):
            marca = set(f.get('marca', []))
            spans = ''.join(f'<span class="w{" m" if norm(w) in marca else ""}" data-t="{(-0.1 if i == 0 else a):.3f}">{e(w)}</span>' for w, a, b in ws)
            kt_html += f'<div class="kt {f.get("pos", "top")}" data-s="{s:.3f}" data-e="{e_:.3f}"><div class="in">{spans}</div></div>'
    if actual: WIN.setdefault(actual, []).append([round(ini, 3), round(dur, 3)])
    CAM.sort(key=lambda c: c[0])
    if not CAM or CAM[0][0] > 0: CAM.insert(0, [0.0, 1.0, 540, 1080])
    visuales = {'telefono': v_telefono(), 'panel': v_panel(), 'espera': v_espera(), 'cocina': v_cocina(), 'logo': v_logo(pr)}
    vis_html = ''.join(f'<div class="vis" data-vis="{k}">{h}</div>' for k, h in visuales.items() if k in WIN)
    data = json.dumps(dict(EV=EV, WIN=WIN, CAM=CAM, RED=RED))
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Azeret+Mono:wght@500;700&display=swap">
<style>{CSS}</style></head><body><div id="c">
<div class="grid abs" style="inset:0"></div>
<div class="glow" id="g1" style="left:-260px;top:120px;width:760px;height:760px;background:rgba(244,41,2,.38)"></div>
<div class="glow" id="g2" style="right:-300px;bottom:180px;width:700px;height:700px;background:rgba(201,251,0,.14)"></div>
<div id="bgred"><div class="grid abs" style="inset:0"></div></div>
<div id="stage">{vis_html}</div>
<div id="topfade"></div>
<img id="logo" src="{LOGO_B}">
{kt_html}
</div><script>{JS.replace('__DATA__', data)}</script></body></html>'''

def tiempos(pid, audio, wav):
    frases = PROMOS[pid]['frases']
    if audio == '-':
        tl, fin = estimar(frases)
        dur = fin + COLA
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r={SR}:cl=mono', '-t', f'{dur:.3f}', str(wav)], check=True)
    else:
        tl, fin = preparar_audio(audio, frases, str(wav))
        dur = fin + COLA
    for f, x in zip(frases, tl): print(f"{x['s']:6.2f}–{x['e']:6.2f}  {f['t']}")
    return tl, dur

def abrir(p, page):
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto(page.as_uri(), wait_until='networkidle'); pg.wait_for_function('window.__ok===true', timeout=30000)
    return b, pg

def render(pid, audio, out, portada=None, t_portada=None):
    tmp = SCR / f'promo_{pid}'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    wav = tmp / 'voz.wav'
    tl, dur = tiempos(pid, audio, wav)
    page = tmp / 'promo.html'; page.write_text(armar(pid, tl, dur), encoding='utf-8')
    frames = tmp / 'f'; frames.mkdir()
    n = int(round(dur * FPS))
    with sync_playwright() as p:
        b, pg = abrir(p, page)
        for i in range(n):
            pg.evaluate(f'window.render({i / FPS:.4f})')
            pg.screenshot(path=str(frames / f'f{i:04d}.jpg'), type='jpeg', quality=90, clip=dict(x=0, y=0, width=1080, height=1920))
        if portada:
            pg.evaluate(f'window.render({(t_portada if t_portada is not None else 0.9):.3f})')
            pg.screenshot(path=portada, type='jpeg', quality=92, clip=dict(x=0, y=0, width=1080, height=1920))
        b.close()
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', str(frames / 'f%04d.jpg'), '-i', str(wav),
                    '-filter_complex', '[1:a]apad,aformat=channel_layouts=stereo[a]', '-map', '0:v', '-map', '[a]', '-t', f'{dur:.3f}',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS),
                    '-c:a', 'aac', '-b:a', '192k', '-ar', str(SR), '-movflags', '+faststart', out], check=True)
    print('ok', out, f'{dur:.2f}s', n, 'cuadros')

def muestras(pid, audio, out_jpg):
    from PIL import Image, ImageDraw
    tmp = SCR / f'promo_{pid}_m'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    tl, dur = tiempos(pid, audio, tmp / 'voz.wav')
    ts = [0.0, 0.3]
    for x in tl: ts += [x['s'] + 0.35, x['e'] - 0.05]
    ts = sorted(set(round(t, 2) for t in ts if t < dur))
    page = tmp / 'promo.html'; page.write_text(armar(pid, tl, dur), encoding='utf-8')
    ims = []
    with sync_playwright() as p:
        b, pg = abrir(p, page)
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
    print('hoja', out_jpg, len(ims), f'{dur:.2f}s')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('promo'); ap.add_argument('audio'); ap.add_argument('out')
    ap.add_argument('--portada'); ap.add_argument('--t-portada', type=float)
    ap.add_argument('--muestras', action='store_true')
    a = ap.parse_args()
    if a.muestras: muestras(a.promo, a.audio, a.out)
    else: render(a.promo, a.audio, a.out, a.portada, a.t_portada)
