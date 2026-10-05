# Bre-B Intelligence — Colombia

Tracker de **Bre-B**, el sistema de pagos inmediatos interoperable del Banco de la República (operación plena desde el 6 de octubre de 2025): transacciones, valor, ticket, llaves, usuarios y adopción.

Proyecto hermano de [visa-intelligence](https://github.com/danielcastaed/visa-intelligence) (tarjetas, fuente SFC). Se mantiene aparte porque la fuente (BanRep), la cadencia y la estructura de datos son distintas.

## Qué muestra

- **Evolución**: transacciones y valor acumulados, ritmo diario implícito.
- **Volumen operacional**: transacciones diarias en el MOL (desde el 6-oct-2025) y por mes.
- **Adopción**: entidades participantes por tipo, origen de las operaciones, montos y tipo de operación.
- **Directorio de llaves (DICE)**: llaves registradas por mes y usuarios; personas naturales vs jurídicas.
- **Contexto**: transferencias vs tarjetas, crecimiento previo, PIX.
- **Cortes y fuentes**: tabla con cada corte oficial y sus valores derivados.

## Datos (`data/`)

| Archivo | Contenido | Fuente |
|---|---|---|
| `breb_mol_cortes.csv` | Transacciones, valor y ticket acumulados: cierres de mes y último corte | Reporte MOL de BanRep (Power BI público), fecha final exacta |
| `breb_distribucion_monto.json` | Distribución de transacciones y valor por rango de monto | Reporte MOL |
| `breb_acceso.json` | QR vs llave (desde el 19-ene-2026) | Reporte MOL, sección de tecnología de acceso |
| `breb_dice.json` | Último corte: llaves por tipo, medios de pago (5 categorías), clientes y llaves naturales/jurídicas, con cantidades exactas | Reporte DICE de BanRep |
| `breb_dice_composicion.csv` | Las mismas composiciones en cada captura (`fecha, panel, categoria, cantidad, porcentaje`); crece un corte por actualización | Reporte DICE |
| `breb_dice_historico.csv` | Totales del DICE en cada captura | Reporte DICE |
| `breb_llaves_dice.csv` | Llaves por mes: jul-2025 a ene-2026 (documento técnico) y puntos etiquetados del reporte DICE | Documento técnico (Gráfico 6) y reporte DICE |
| `breb_diario_mol.csv` | Transacciones por día, desde el 6-oct-2025 hasta el último corte (`fecha, transacciones`, enteros exactos) | Gráfico de evolución del reporte MOL (valor en el `aria-label` de cada barra, fecha del eje) |
| `breb_contexto.json` | Entidades participantes, origen de operaciones, contexto | Documento técnico de BanRep (feb 2026) |

Lo calculado aquí y no publicado se marca como **derivado** en el dashboard (transacciones y valor del mes, promedio diario, crecimiento).

**Validación.** Las composiciones del DICE se leen de los `aria-label` de cada sector (nombre y cantidad exacta) y el script exige que cada panel sume su total (llaves, medios de pago, clientes). En cada corte, transacciones × ticket reproduce el valor; las tablas de distribución suman exactamente el total; las cifras del 31-ene-2026 coinciden con el documento técnico (370,4 M, $59 billones, $159.456) y varias fechas citadas por la prensa coinciden con el reporte (4-may-2026: 782.218.571 transacciones, ticket $155.755, idéntico a Infobae). La serie diaria suma exactamente el total acumulado del reporte (1.780.392.143 al 3-oct-2026, 363 días sin huecos) y el script lo exige en cada corrida. Frente a la digitalización previa del Gráfico 7 del documento técnico (hasta el 31-ene-2026) difiere 0,007 M por día en promedio (máx. 0,02 M).

## Actualización automática

BanRep incrusta sus reportes de Power BI en páginas protegidas con captcha, pero **los reportes en sí son públicos y se abren sin captcha** en `app.powerbi.com`. El workflow `update-data.yml` los lee con Playwright cada mes (día 2) y hace commit de los datos nuevos; GitHub Pages se republica solo.

Configuración (una vez), en *Settings → Secrets and variables → Actions*:

| Secret | Valor |
|---|---|
| `BREB_MOL_URL` | Dirección del reporte MOL: abrir la página de indicadores MOL de BanRep, y cuando el reporte cargue, copiar la URL `https://app.powerbi.com/view?r=…` |
| `BREB_DICE_URL` | Igual, para el reporte DICE |

La dirección lleva la clave del reporte; si BanRep lo republica con otra clave, hay que actualizar el secret. Si el script no logra leer el reporte, el workflow falla y guarda una captura en el artefacto `debug-banrep`.

Ejecutar a mano: *Actions → Actualizar datos de BanRep → Run workflow* (la opción `backfill` revisa todos los cierres de mes).

**Estado:** verificado en GitHub Actions el 4-oct-2026 (corrida manual en verde, commit del bot incluido). Las cifras que leyó el runner coinciden dígito a dígito con las capturadas a mano. Ojo con los secrets: deben ser la URL del reporte completo, no la de la portada.

- `BREB_MOL_URL` → el reporte de `banrep.gov.co/es/bre-b/indicadores-mol` ("Indicadores MOL", el que tiene el filtro de fecha). El de `/indicadores` es solo la portada ("Intro") y no sirve.
- `BREB_DICE_URL` → el de `/indicadores-dice` ("Total de llaves registradas").
- Si algo falla, el log imprime `[diagnóstico]` con la URL (sin clave), el título y el texto que vio el navegador.

## Pendiente

- Comparación contra volumen de tarjetas (publicar un JSON anual desde visa-intelligence y leerlo aquí).

## Vista local

```bash
python3 -m http.server 8000
```
