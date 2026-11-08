# Promos animados de Menuo (motion graphics, sin fotos de stock).
# Cada frase: `t` = lo que dice la voz y lo que se escribe en pantalla (texto cinético, palabra por palabra).
#   pos: 'top' (texto arriba, visual abajo) o 'centro' (solo texto).  marca: palabras resaltadas (sin puntuación, minúsculas).
#   vis: visual que arranca en esta frase ('espera', 'telefono', 'panel', 'cocina', 'logo' o None).
#   ev:  eventos del visual atados a una palabra de la frase {evento: índice de palabra}.
#   cam: cámara {'s': zoom, 'f': (x, y) punto del lienzo que queda en el centro de la zona visual}.
#   fondo: 'rojo' para frases de golpe.  kt=False: sin texto cinético (el visual ya lo dice).

TONO = '[upbeat]'

ZOOM_MENU = dict(s=1.45, f=(540, 1035))
ZOOM_HOJA = dict(s=1.38, f=(540, 1270))
ZOOM_QR = dict(s=1.22, f=(540, 1060))
NORMAL = dict(s=1.0, f=(540, 1080))
VER_OK = dict(s=1.08, f=(540, 1070))

PROMOS = {
    'mesas': dict(
        fecha='2026-11-09', hora='18:00', tag='Para dueños', pill='Escríbenos DEMO por DM', lema='Pide. Paga. Listo.',
        frases=[
            dict(t='¿Te ha pasado?', pos='centro', marca=['pasado'], vis=None),
            dict(t='Viernes, restaurante lleno, y todas las mesas pidiendo la cuenta al tiempo.', pos='top', marca=['cuenta'], vis='espera',
                 ev={'b1': 4, 'b2': 7, 'b3': 9}, cam=NORMAL),
            dict(t='Y tu equipo cobrando mesa por mesa.', pos='top', marca=['mesa', 'por'], ev={'alerta': 3, 'timer': 0}),
            dict(t='¿Qué tal si cada mesa pagara sola?', pos='centro', marca=['sola'], fondo='rojo', vis=None),
            dict(t='Escanean el QR.', pos='top', marca=['qr'], vis='telefono', ev={'link': 1}, cam=ZOOM_QR),
            dict(t='Piden lo que quieren, desde el menú con fotos.', pos='top', marca=['piden'], ev={'menu': 0, 'add1': 3, 'add2': 7}, cam=ZOOM_MENU),
            dict(t='Y pagan con Nequi, PSE o tarjeta, sin esperar a nadie.', pos='top', marca=['pagan'],
                 ev={'sheet': 0, 'm_nequi': 3, 'm_pse': 4, 'm_tarjeta': 6, 'sel': 7, 'pay': 8, 'ok': 10}, cam=ZOOM_HOJA, cam_ev={'ok': VER_OK}),
            dict(t='Tú lo ves al instante en tu panel.', pos='top', marca=['panel'], vis='panel', ev={'p_pago': 3}, cam=NORMAL),
            dict(t='Menuo.', pos='centro', kt=False, vis='logo', cam=NORMAL),
            dict(t='Pruébalo dos meses gratis. Escríbenos DEMO por DM.', tts='Pruébalo dos meses gratis. Escríbenos «demo» por DM.', pos='top', marca=['demo'], ev={'cta': 4}),
        ],
        caption='¿Te ha pasado? Viernes, restaurante lleno y todas las mesas pidiendo la cuenta al mismo tiempo.\n\n'
                'Con Menuo cada mesa escanea el QR, pide y paga desde el celular con Nequi, PSE o tarjeta. Tú lo ves al instante en tu panel.\n\n'
                'Pruébalo 2 meses gratis: escríbenos DEMO por DM.\n\n#RestaurantesMedellín',
    ),
    'cuenta': dict(
        fecha='2026-11-11', hora='10:00', tag='Para comensales', pill='Mándaselo al dueño', lema='Pide. Paga. Listo.',
        frases=[
            dict(t='¿Te ha pasado que pides la cuenta… y nunca llega?', pos='top', marca=['nunca', 'llega'], vis='espera',
                 ev={'b1': 4, 'timer': 8}, cam=NORMAL),
            dict(t='Catorce minutos después, sigues esperando.', pos='top', marca=['catorce', 'minutos'], ev={'b2': 0, 'b3': 3}),
            dict(t='¿Qué tal si pagaras desde tu celular?', pos='centro', marca=['celular'], fondo='rojo', vis=None),
            dict(t='Escaneas el QR de la mesa.', pos='top', marca=['qr'], vis='telefono', ev={'link': 3, 'menu': 5}, cam=ZOOM_QR),
            dict(t='Revisas tu cuenta.', pos='top', marca=['cuenta'], ev={'sheet': 0}, cam=ZOOM_HOJA),
            dict(t='Y pagas con Nequi en segundos.', pos='top', marca=['nequi'], ev={'m_nequi': 3, 'sel': 3, 'pay': 4, 'ok': 5}, cam_ev={'ok': VER_OK}),
            dict(t='Sin esperar al mesero.', pos='top', marca=['sin', 'esperar']),
            dict(t='Mándale esto al dueño de tu restaurante favorito.', pos='top', marca=['dueño'], vis='logo', ev={'cta': 2}, cam=NORMAL),
        ],
        caption='¿Te ha pasado que pides la cuenta… y nunca llega?\n\n'
                'Con Menuo escaneas el QR de la mesa, revisas tu cuenta y pagas con Nequi, PSE o tarjeta en segundos, sin esperar al mesero.\n\n'
                'Mándale esto al dueño de tu restaurante favorito.\n\n#ComerEnMedellín',
    ),
    'pantalla': dict(
        fecha='2026-11-13', hora='18:00', tag='Para dueños', pill='Escríbenos DEMO por DM', lema='Todo, en una pantalla.',
        frases=[
            dict(t='¿Qué tal si vieras todo tu restaurante en una sola pantalla?', pos='top', marca=['una', 'sola', 'pantalla'], vis='panel',
                 ev={}, cam=NORMAL),
            dict(t='Qué mesa está pidiendo.', pos='top', marca=['pidiendo'], ev={'p_pide': 1}, cam=dict(s=1.3, f=(540, 900))),
            dict(t='Qué pedido va para cocina.', pos='top', marca=['cocina'], ev={'p_cocina': 1}, cam=dict(s=1.3, f=(540, 1240))),
            dict(t='Y quién ya pagó.', pos='top', marca=['pagó'], ev={'p_pago': 2}, cam=dict(s=1.15, f=(540, 1080))),
            dict(t='La comanda sale sola, y llega a cocina ya pagada.', pos='top', marca=['ya', 'pagada'], vis='cocina', ev={'print': 1, 'stamp': 8}, cam=NORMAL),
            dict(t='En el computador o la tablet que ya tienes.', pos='top', marca=['ya', 'tienes'], vis='panel', cam=dict(s=0.86, f=(540, 1080))),
            dict(t='Menuo.', pos='centro', kt=False, vis='logo', cam=NORMAL),
            dict(t='¿Lo vemos en tu restaurante? Escríbenos DEMO por DM.', tts='¿Lo vemos en tu restaurante? Escríbenos «demo» por DM.', pos='top', marca=['demo'], ev={'cta': 5}),
        ],
        caption='Todo tu restaurante en una sola pantalla: qué mesa está pidiendo, qué pedido va para cocina y quién ya pagó.\n\n'
                'Con Menuo la comanda sale sola y llega a cocina ya pagada. Funciona en el computador o la tablet que ya tienes.\n\n'
                '¿Lo vemos en tu restaurante? Escríbenos DEMO por DM.\n\n#RestaurantesMedellín',
    ),
}


def texto_tts(reel):
    return TONO + ' ' + '\n\n'.join(f.get('tts', f['t']) for f in PROMOS[reel]['frases'])
