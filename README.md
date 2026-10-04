# Bre-B Intelligence — Colombia

Tracker de **Bre-B**, el sistema de pagos inmediatos interoperable del Banco de la República (operación plena desde el 6 de octubre de 2025): transacciones, valor, ticket, llaves, usuarios y adopción.

Proyecto hermano de [visa-intelligence](https://github.com/danielcastaed/visa-intelligence) (tarjetas, fuente SFC). Se mantiene aparte porque la fuente (BanRep), la cadencia y la estructura de datos son distintas.

## Qué muestra

- **Evolución**: transacciones y valor acumulados, ritmo diario implícito.
- **Volumen operacional**: operaciones diarias en el MOL (6-oct-2025 a 31-ene-2026) y transacciones por mes.
- **Adopción**: entidades participantes por tipo, origen de las operaciones, montos y tipo de operación.
- **Directorio de llaves (DICE)**: llaves registradas por mes y usuarios; personas naturales vs jurídicas.
- **Contexto**: transferencias vs tarjetas, crecimiento previo, PIX.
- **Hitos y fuentes**: tabla con cada corte, su fuente y su estado de verificación.

## Datos (`data/`)

| Archivo | Contenido | Fuente |
|---|---|---|
| `breb_hitos.csv` | Cortes acumulados (transacciones, valor, ticket, llaves, usuarios) | Documento técnico de BanRep (oct y ene) y prensa que cita a BanRep (resto) |
| `breb_diario_mol.csv` | Operaciones diarias liquidadas, 118 días | Gráfico 7 del documento técnico, **digitalizado** y validado |
| `breb_llaves_dice.csv` | Llaves en el DICE, jul-2025 a ene-2026 | Gráfico 6 del documento técnico (etiquetas del gráfico) |
| `breb_contexto.json` | Entidades, origen de operaciones, composición, contexto | Documento técnico y prensa, cada ítem con su fuente |

Para agregar un corte: añadir una fila a `breb_hitos.csv`. Lo calculado aquí y no publicado por BanRep se marca `valor_derivado=true`; las fechas que la fuente no precisa, `fecha_aprox=true`.

**Digitalización del Gráfico 7:** se midió la altura de las 118 barras diarias del PDF y se validó contra totales oficiales del mismo documento: suma 369,6 M (oficial 370,4 M), octubre 64,2 M (64,4 M), promedio de diciembre 3,67 M (3,6 M), pico del 24-dic 4,86 M (4,8 M). Los totales mensuales resultantes (64,2 / 88,9 / 113,9 / 102,6 M) coinciden con las barras del Gráfico 5. Error estimado ≈ 1–2%.

## Limitación de datos

BanRep publica los indicadores de Bre-B ([DICE](https://www.banrep.gov.co/es/indicadores-bre-b-directorio-centralizado-dice) y [MOL](https://www.banrep.gov.co/es/indicadores-bre-b-mecanismo-operativo-liquidacion-mol)) en dashboards interactivos sin descarga, y pide captcha. Por eso la serie posterior a enero de 2026 sale de prensa que cita a BanRep, y no es mensual. Los cortes con fecha aproximada se dibujan huecos y no entran al cálculo del ritmo diario.

Un borrador anterior (`breb-intelligence-preview.html`) traía una serie de llaves y de valor acumulado que no coincidía con el documento técnico (p. ej. valor acumulado al 31-ene-2026: $32,5 B en el borrador vs $59 B oficial; llaves de oct a ene de 3 a 19 M vs 92 a 99 M oficiales). Sus gráficos se retomaron aquí sobre las cifras oficiales.

## Pendiente

- Cotejar con los indicadores primarios de BanRep (MOL y DICE) los cortes confirmados solo por prensa.
- Julio–septiembre de 2026, y valor/transacciones mensuales posteriores a enero.
- Distribución de llaves por tipo y medio de pago asociado, y distribución completa de montos (solo en el dashboard DICE/MOL y en el comunicado de 6 meses de BanRep).
- Comparación contra volumen de tarjetas (publicar un JSON anual desde visa-intelligence y leerlo aquí).
- Refresco periódico (hoy manual).

## Vista local

```bash
python3 -m http.server 8000
```
