# Reels de Menuo

Kit para producir los Reels de @menuo.app: 3 por semana (lunes 6 p. m., miércoles 10 a. m., viernes 6 p. m., hora de Bogotá), con la voz de Andrés (ElevenLabs) y la identidad de marca de Menuo. Cada lunes se revisan las métricas en Metricool y se hace más de lo que funcionó. Los resultados se anotan en [BITACORA.md](BITACORA.md).

## Archivos

- `guiones.py`: los guiones. Cada frase es un subtítulo y puede abrir una escena nueva (`escena`) o sumar elementos a la actual (`extra`). `texto_tts(reel)` devuelve el bloque que se le pasa a ElevenLabs.
- `reel2.py`: arma el video (1080×1920, 30 fps).
  - `python3 reel2.py <reel> <audio.mp3> <salida.mp4> --portada <portada.jpg>` renderiza el video y su portada.
  - Con `-` en lugar del audio arma una versión muda con tiempos estimados.
  - Con `--muestras` saca una hoja de contacto para revisar sin renderizar todo.
  - Variable `REEL_TMP`: carpeta para los cuadros temporales.
- `kit/`:
  - `fotos/<id de Pexels>.jpg`: fotos de stock con licencia Pexels.
  - Logos de Menuo.
  - `app-menu-rojo.png`: pantalla del menú en el celular.
- `AAAA-MM-DD_<reel>.mp4` y `.jpg`: videos publicados y sus portadas. Metricool los toma de aquí por URL pública.

## Tipos de escena

| Tipo | Qué muestra |
|---|---|
| `hook` | Gancho en letra grande, con foto o sobre fondo tinta. |
| `foto` | Foto a sangre con movimiento lento y etiqueta de hora. Acepta `zoom`. |
| `ticket` | Comanda en cocina con sello PAGADO. |
| `qr` | Celular escaneando el QR. |
| `app` | Menú en el celular con selector ES/EN. |
| `pago` | Pantalla de pago con Tarjeta, PSE, Nequi y Bancolombia, y luego «Pagado». |
| `panel` | Mesas en vivo, con aviso «Mesa 4 pagó». |
| `mito` | Cita tachada; se completa con los extras `falso` y `realidad`. |
| `cta` | Cierre con logo, frase y botón lima. |

**Extras:**
- `sticker`: texto inclinado.
- `sinsenal`: ícono de señal tachada.
- `falso` / `realidad`.

## Reglas para un buen gancho y retención (investigación de noviembre de 2026)

1. **Primeras 5 palabras.** Lo que está en juego va ahí: un número, un costo o un error. Nada de «¿Estás cansado de…?» ni «Hola, somos…».
2. **Cuadro 1.** Debe estar armado y con texto grande en pantalla. Sin logo de entrada ni fundido desde negro.
3. **Ritmo.** Algo cambia cada ~2 segundos: escena, sticker o subtítulo. El script recorta las pausas a 0,34 s entre frases y 0,22 s dentro de una frase.
4. **Duración.** Entre 18 y 24 s. Terminar apenas se cumple la promesa del gancho.
5. **Subtítulos.** Palabra por palabra en la franja de 1236–1432 px, porque la mayoría ve sin sonido. Lo importante va entre 220 y 1440 px de alto, lejos de los botones de la derecha.
6. **Un solo llamado por Reel.** Rotar entre:
   - «Mándaselo a alguien con restaurante»: envíos, la señal que más pesa para llegar a no seguidores.
   - «Escríbenos <PALABRA> por DM»: la palabra clave dice qué Reel trajo el mensaje.
   - «Déjalo en comentarios».
7. **Voz.** Andrés (`1xdfDg2OYI81A119UVlK`), modelo `eleven_v4`, con UNA sola marca `[upbeat]` al inicio.
   - Con 3 marcas sonaba exagerada; con `eleven_multilingual_v2`, plana.
   - Escribir los números en palabras («catorce»).
   - Generar solo con el plan pago, que es el que da licencia comercial.
8. **Sin datos inventados.** Usar escenas concretas (8:00 p. m., mesa 3) en lugar de estadísticas sin fuente.
9. **En Metricool:**
   - Tipo `REEL`, `isAiGenerated: true` (la voz es sintética).
   - `videoThumbnailUrl` con la portada.
   - Un solo hashtag.

## Cómo leer las métricas (connector `reels` de Metricool)

| Métrica | Qué mide | Meta |
|---|---|---|
| `reelsViewRate` | % que pasó de 3 s: mide el gancho | > 50 % |
| `retention` | % promedio visto | > 45 % aceptable, > 60 % fuerte (Reels de 15–30 s) |
| `shares` / `reach` | Envíos por alcance: lo que más reparte el Reel a no seguidores | — |
| `saved` / `reach` y `comments` / `reach` | Interés real | — |
| DMs con la palabra clave | Intención de compra | Contar a mano |

Con 3 Reels por semana no hay certeza estadística. Una semana sirve para descartar; para decidir un formato ganador hay que mirar 2 o 3 semanas.
