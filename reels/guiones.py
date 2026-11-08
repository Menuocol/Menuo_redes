# Guiones de Reels de Menuo. Cada frase = un subtítulo y, si trae `escena`, un cambio de escena.
# Reglas (investigación nov 2026): lo que está en juego en las primeras 5 palabras, texto grande desde el cuadro 1,
# algo cambia cada ~2 s, pausas <= 0,35 s, 18–24 s, terminar apenas se resuelve el gancho.
# `tts` reemplaza el texto que lee la voz cuando difiere del subtítulo. `cap=False` = sin subtítulo (el texto ya está en pantalla).
# `extra` = elementos que aparecen sobre la escena actual cuando empieza esa frase.

TONO = '[upbeat]'  # una sola marca al inicio (toma C aprobada)
VOZ = '1xdfDg2OYI81A119UVlK'  # Andrés
MODELO = 'eleven_v4'

REELS = {
    'mesero': dict(
        fecha='2026-11-09', hora='18:00', aud='Dueño', tag='La noche de un mesero', formato='Historia', llamado='Envíos (mándaselo)',
        frases=[
            dict(t='Catorce minutos para cobrar una mesa.', cap=False,
                 escena=dict(tipo='hook', foto='20609544', pos='50% 28%', lineas=['14 minutos', 'para cobrar', 'una mesa.'], resalta=0)),
            dict(t='Ocho de la noche: la mesa tres pide la cuenta.', escena=dict(tipo='foto', foto='3769740', pos='50% 45%', label='8:00 p. m.')),
            dict(t='El mesero va por el datáfono…', escena=dict(tipo='foto', foto='8475161', pos='45% 50%', label='8:06 p. m.')),
            dict(t='…que está en la caja.', tts='Que está en la caja.', extra=[dict(tipo='sticker', texto='En la caja', color='lima', rot=-4, top=560)]),
            dict(t='Mientras tanto, la mesa siete quería postre.', escena=dict(tipo='foto', foto='6752362', pos='50% 50%', label='8:09 p. m.')),
            dict(t='Nadie la vio.', extra=[dict(tipo='sticker', texto='Nadie la vio', color='rojo', rot=3, top=600)]),
            dict(t='Ocho y catorce: sin señal. Otra vez.', escena=dict(tipo='foto', foto='5332483', pos='50% 40%', label='8:14 p. m.'),
                 extra=[dict(tipo='sinsenal', palabra=3)]),
            dict(t='Con Menuo, la mesa paga sola desde el celular.', escena=dict(tipo='pago', metodos=False)),
            dict(t='Y tu mesero vuelve a atender.', escena=dict(tipo='foto', foto='36572259', pos='50% 22%', label='8:15 p. m.', zoom=1.32)),
            dict(t='Mándaselo a alguien que tenga restaurante.', cap=False,
                 escena=dict(tipo='cta', lineas=['Mándaselo a', 'alguien con', 'restaurante.'], pill='2 meses sin costo · DM')),
        ],
        caption='Catorce minutos para cobrar una sola mesa: pedir la cuenta, ir por el datáfono a la caja, volver, sin señal… y mientras tanto la mesa 7 se quedó sin postre.\n\n'
                'Con Menuo la mesa paga desde el celular con un QR y tu equipo vuelve a atender. 2 meses sin costo para restaurantes en Medellín.\n\n'
                'Mándaselo a alguien que tenga restaurante.\n\n#RestaurantesMedellín',
    ),
    'funciona': dict(
        fecha='2026-11-11', hora='10:00', aud='Dueño', tag='Así funciona Menuo', formato='Paso a paso', llamado='DM con palabra clave (DEMO)', pasos=4,
        frases=[
            dict(t='Este pedido llegó a cocina ya pagado.', cap=False,
                 escena=dict(tipo='ticket', hook=True, lineas=['Este pedido', 'llegó', 'ya pagado.'], resalta=2)),
            dict(t='Y nadie fue a la mesa.', escena=dict(tipo='foto', foto='39910759', pos='45% 50%', label='Mesa 4')),
            dict(t='Uno: el cliente escanea el QR. Sin descargar nada.', escena=dict(tipo='qr', paso=1),
                 extra=[dict(tipo='sticker', texto='Sin descargar nada', color='lima', rot=-3, top=1100, palabra=6, chico=True)]),
            dict(t='Dos: pide del menú con fotos, en español o en inglés.', escena=dict(tipo='app', paso=2, ingles=10)),
            dict(t='Tres: paga con tarjeta, PSE, Nequi o Bancolombia.', escena=dict(tipo='pago', paso=3, metodos=True)),
            dict(t='Cuatro: tú lo ves todo en el panel.', escena=dict(tipo='panel', paso=4)),
            dict(t='Y la cocina lo recibe así.', escena=dict(tipo='ticket', hook=False, sello_palabra=4)),
            dict(t='¿Lo quieres en tu restaurante? Escríbenos «DEMO» por DM.', cap=False,
                 escena=dict(tipo='cta', lineas=['Escríbenos', '«DEMO»', 'por DM.'], resalta=1, pill='2 meses sin costo')),
        ],
        caption='Así funciona Menuo en tu restaurante:\n1. El cliente escanea el QR de la mesa, sin descargar nada.\n2. Pide del menú con fotos, en español o inglés.\n'
                '3. Paga con tarjeta, PSE, Nequi o Bancolombia.\n4. Tú lo ves todo en el panel y la cocina recibe el pedido ya pagado.\n\n'
                '¿Lo quieres en tu restaurante? Escríbenos DEMO por DM. 2 meses sin costo.\n\n#RestaurantesMedellín',
    ),
    'mentiras': dict(
        fecha='2026-11-13', hora='18:00', aud='Dueño', tag='3 mentiras del QR', formato='Mitos (lista)', llamado='Comentarios', pasos=3, fondo='tinta',
        frases=[
            dict(t='Tres mentiras sobre pedir por QR.', cap=False,
                 escena=dict(tipo='hook', foto=None, lineas=['3 mentiras', 'sobre pedir', 'por QR.'], resalta=0)),
            dict(t='Uno: «mis clientes tienen que descargar una app».', tts='Uno: "mis clientes tienen que descargar una app".', cap=False,
                 escena=dict(tipo='mito', paso=1, cita='«Mis clientes tienen que descargar una app.»')),
            dict(t='Falso. El menú abre con la cámara del celular.', cap=False,
                 extra=[dict(tipo='falso', texto='Falso'), dict(tipo='realidad', texto='El menú abre con la cámara del celular.', palabra=1)]),
            dict(t='Dos: «tengo que comprar equipos nuevos».', tts='Dos: "tengo que comprar equipos nuevos".', cap=False,
                 escena=dict(tipo='mito', paso=2, cita='«Tengo que comprar equipos nuevos.»')),
            dict(t='Falso. Usas el computador o la tablet que ya tienes.', cap=False,
                 extra=[dict(tipo='falso', texto='Falso'), dict(tipo='realidad', texto='Usas el computador o la tablet que ya tienes.', palabra=1)]),
            dict(t='Y tres: «mi equipo ya no va a atender».', tts='Y tres: "mi equipo ya no va a atender".', cap=False,
                 escena=dict(tipo='mito', paso=3, cita='«Mi equipo ya no va a atender.»')),
            dict(t='Al revés: deja de cobrar mesa por mesa, y vuelve a atender.', cap=False,
                 extra=[dict(tipo='falso', texto='Al revés'), dict(tipo='realidad', texto='Deja de cobrar mesa por mesa y vuelve a atender.', palabra=2)]),
            dict(t='¿Qué otra mentira has escuchado? Déjala en comentarios.', cap=False,
                 escena=dict(tipo='cta', lineas=['¿Qué otra', 'mentira has', 'escuchado?'], pill='Déjala en comentarios')),
        ],
        caption='3 mentiras sobre los pedidos por QR en restaurantes:\n✕ «Mis clientes tienen que descargar una app.» El menú abre con la cámara del celular.\n'
                '✕ «Tengo que comprar equipos nuevos.» Usas el computador o la tablet que ya tienes.\n'
                '✕ «Mi equipo ya no va a atender.» Al revés: deja de cobrar mesa por mesa y vuelve a atender.\n\n'
                '¿Qué otra mentira has escuchado? Déjala en comentarios.\n\n#RestaurantesMedellín',
    ),
}


def texto_tts(reel):
    """Bloque único para ElevenLabs: una marca de tono al inicio y un párrafo por frase (así se grabó la toma C)."""
    return TONO + ' ' + '\n\n'.join(f.get('tts', f['t']) for f in REELS[reel]['frases'])
