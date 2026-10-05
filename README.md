# Bre-B Intelligence — Colombia

Tracker de **Bre-B**, el sistema de pagos inmediatos interoperable del Banco de la República (operación plena desde el 6 de octubre de 2025): transacciones, valor, ticket, llaves, usuarios y adopción.

Proyecto hermano de [visa-intelligence](https://github.com/danielcastaed/visa-intelligence) (tarjetas, fuente SFC; [dashboard en vivo](https://danielcastaed.github.io/visa-intelligence/)); este dashboard enlaza al de tarjetas desde el pie y desde la sección de franquicias. Se mantiene aparte porque la fuente (BanRep), la cadencia y la estructura de datos son distintas.

## Cómo está organizado

El dashboard es una sola página con pestañas (el enlace conserva la vista, por ejemplo `#tarjetas/lento`):

| Pestaña | Contenido |
|---|---|
| **Resumen** | Cifras clave y cinco mensajes con enlace a su detalle |
| **Volumen** | Transacciones y valor por mes, crecimiento, serie diaria |
| **Adopción** | Rangos de monto, entidades, origen, QR vs llave |
| **Llaves** | Directorio DICE: llaves por tipo, medios de pago, naturales y jurídicas |
| **Tarjetas** | Seis subvistas: Panorama (valor y transacciones), Franquicias y productos, Quién cede más, Emisores, ¿Crecen más lento?, Tarjetas y llaves; cada una abre con una línea de lectura |
| **Datos y notas** | Fuentes, contexto, tabla de cortes y notas |

Las notas largas de cada gráfico están plegadas en «Cómo leerlo y salvedades».

## Qué muestra

- **Evolución**: transacciones y valor acumulados, ritmo diario implícito.
- **Volumen operacional**: transacciones diarias en el MOL (desde el 6-oct-2025) y por mes.
- **Adopción**: entidades participantes por tipo, origen de las operaciones, montos y tipo de operación.
- **Directorio de llaves (DICE)**: llaves registradas por mes y usuarios; personas naturales vs jurídicas.
- **Bre-B frente a las tarjetas**: transacciones y valor por mes de Bre-B contra las compras con tarjeta de crédito y débito (SFC), Bre-B como porcentaje de ellas, el desglose por producto (crédito / débito) y franquicia (Visa, Mastercard, Amex, Diners, otras) con el peso de Bre-B frente a cada una, una gráfica del peso de cada franquicia y producto frente a Bre-B mes a mes desde ene-2025 con su tabla de quién cede más, en valor y en número de transacciones (separando dilución de pérdida real) qué emisores mueven el crédito de cada franquicia, y si las tarjetas crecen más lento desde Bre-B (crecimiento mes a mes y acumulado por ventanas comparables), y **tarjetas vigentes contra llaves** (parque de instrumentos, y transacciones al mes por instrumento).
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
| `tarjetas_sfc_mensual.csv` | Compras con tarjeta de crédito (nacionales) y débito, y retiros con débito, por mes desde ene-2015: número y monto en COP, más tarjetas vigentes a la fecha de corte (solo la línea de total, sin las subcategorías contactless / sin chip). Base de emisores; sin administradoras de sistemas de pago | Datos abiertos de la SFC, conjunto [Tarjetas de crédito y débito](https://www.datos.gov.co/d/h2jg-r3zg) (`scripts/fetch_sfc_tarjetas.py`) |
| `tarjetas_sfc_franquicia.csv` | Compras por producto y franquicia, por mes. Crédito: directo de la SFC (valor y número). Débito: valor **estimado** por franquicia con la llave de ingresos por tarifa interbancaria (TII) de Visa y Mastercard, con las excepciones manuales del análisis de tarjetas (Scotiabank Colpatria, Falabella, Mibanco y Nu 100 % Mastercard; JFK 100 % Visa) | Datos abiertos de la SFC (`scripts/fetch_sfc_tarjetas.py`) |
| `tarjetas_sfc_emisores_credito.csv` | Compras de crédito (número y monto) por emisor para Visa y Mastercard, desde oct-2023; suma exacta la franquicia | Datos abiertos de la SFC (`scripts/fetch_sfc_tarjetas.py`) |
| `breb_contexto.json` | Entidades participantes, origen de operaciones, contexto | Documento técnico de BanRep (feb 2026) |

Lo calculado aquí y no publicado se marca como **derivado** en el dashboard (transacciones y valor del mes, promedio diario, crecimiento).

**Validación.** Las composiciones del DICE se leen de los `aria-label` de cada sector (nombre y cantidad exacta) y el script exige que cada panel sume su total (llaves, medios de pago, clientes). En cada corte, transacciones × ticket reproduce el valor; las tablas de distribución suman exactamente el total; las cifras del 31-ene-2026 coinciden con el documento técnico (370,4 M, $59 billones, $159.456) y varias fechas citadas por la prensa coinciden con el reporte (4-may-2026: 782.218.571 transacciones, ticket $155.755, idéntico a Infobae). La serie diaria suma exactamente el total acumulado del reporte (1.780.392.143 al 3-oct-2026, 363 días sin huecos) y el script lo exige en cada corrida. Frente a la digitalización previa del Gráfico 7 del documento técnico (hasta el 31-ene-2026) difiere 0,007 M por día en promedio (máx. 0,02 M).

## Actualización automática

BanRep incrusta sus reportes de Power BI en páginas protegidas con captcha, pero **los reportes en sí son públicos y se abren sin captcha** en `app.powerbi.com`. El workflow `update-data.yml` los lee con Playwright cada mes (día 2) y hace commit de los datos nuevos; GitHub Pages se republica solo.

El mismo workflow baja las compras con tarjeta de los datos abiertos de la SFC (`scripts/fetch_sfc_tarjetas.py`, sin credenciales): reescribe todo el histórico cada vez, porque la SFC corrige meses anteriores, y descarta el último mes si lo reportan muy pocas entidades. La SFC publica con rezago de un par de meses; hoy el último mes es julio de 2026.

Configuración (una vez), en *Settings → Secrets and variables → Actions*:

| Secret | Valor |
|---|---|
| `BREB_MOL_URL` | Dirección del reporte MOL: abrir la página de indicadores MOL de BanRep, y cuando el reporte cargue, copiar la URL `https://app.powerbi.com/view?r=…` |
| `BREB_DICE_URL` | Igual, para el reporte DICE |

La dirección lleva la clave del reporte; si BanRep lo republica con otra clave, hay que actualizar el secret. Si el script no logra leer el reporte, el workflow falla y guarda una captura en el artefacto `debug-banrep`.

Ejecutar a mano: *Actions → Actualizar datos de BanRep → Run workflow* (la opción `backfill` revisa todos los cierres de mes).

**Estado:** verificado en GitHub Actions el 4-oct-2026. El runner lee cortes mensuales, serie diaria (363 días), tipos de llave, medios de pago y clientes, y reproduce byte a byte los archivos de `data/` que se habían capturado a mano en Chrome (la corrida terminó en verde y sin cambios que publicar). Un corte nuevo genera un commit del bot. Ojo con los secrets: deben ser la URL del reporte completo, no la de la portada.

- `BREB_MOL_URL` → el reporte de `banrep.gov.co/es/bre-b/indicadores-mol` ("Indicadores MOL", el que tiene el filtro de fecha). El de `/indicadores` es solo la portada ("Intro") y no sirve.
- `BREB_DICE_URL` → el de `/indicadores-dice` ("Total de llaves registradas").
- Si algo falla, el log imprime `[diagnóstico]` con la URL (sin clave), el título y el texto que vio el navegador.

## Pendiente

Nada por ahora. El enlace de vuelta desde el dashboard de tarjetas queda a criterio de ese proyecto (no se tocó).

## Vista local

```bash
python3 -m http.server 8000
```
