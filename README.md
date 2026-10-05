# Bre-B Intelligence — Colombia

Tracker de **Bre-B**, el sistema de pagos inmediatos interoperable del Banco de la República (operación plena desde el 6 de octubre de 2025): transacciones, valor, ticket, llaves, adopción, y su comparación con las compras con tarjeta.

**Dashboard:** https://danielcastaed.github.io/breb-intelligence/ · Proyecto hermano: [visa-intelligence](https://github.com/danielcastaed/visa-intelligence) (tarjetas, fuente SFC; [dashboard](https://danielcastaed.github.io/visa-intelligence/)), al que este dashboard enlaza desde el pie y desde la vista de franquicias. Se mantiene aparte porque la fuente (BanRep), la cadencia y la estructura de datos son distintas.

Es una página estática (`index.html`, Chart.js, tema oscuro/claro) que lee los archivos de `data/`. Los datos se actualizan solos cada mes con GitHub Actions.

## Cómo se usa

### Pestañas

El enlace conserva la vista (por ejemplo `#tarjetas/lento`).

| Pestaña | Contenido |
|---|---|
| **Resumen** | KPI del período con variación frente al período anterior, gráficos de evolución y, al final, cinco mensajes clave con enlace a su detalle |
| **Volumen** | Transacciones y valor por mes, crecimiento mensual, serie diaria del MOL |
| **Adopción** | *General*: distribución por rango de monto, entidades por tipo, origen, QR vs llave. *Bancos y entidades*: lista oficial de participantes, tarjetas de cada entidad y cifras por banco de prensa |
| **Llaves** | Directorio DICE: llaves en el tiempo, por tipo, medios de pago, personas naturales y jurídicas |
| **Tarjetas** | *Panorama* (Bre-B frente a las compras con tarjeta), *Franquicias y productos*, *Quién cede más*, *Emisores*, *¿Crecen más lento?* y *Tarjetas y llaves*; cada una abre con una línea de lectura |
| **Datos y notas** | Fuentes, contexto, tabla de cortes y notas |

Las notas largas de cada gráfico están plegadas en «Cómo leerlo y salvedades». Cada cifra lleva una etiqueta: **oficial** (de la fuente), **derivado** (calculado aquí), **estimado** (reparto propio, ver metodología) o **prensa** (sin reporte oficial que la verifique).

### Filtros

Como en el dashboard de Visa, una barra arriba afecta toda la página, y los controles que no aplican a la vista se atenúan con un aviso de qué sí aplica.

| Filtro | Qué hace | Dónde aplica |
|---|---|---|
| **Período** (desde / hasta, «Todo», «6 m», «3 m») | Recorta series, KPI, tabla de cortes y la distribución por monto | Resumen, Volumen, Adopción (general), Llaves, Tarjetas (panorama, franquicias, tarjetas y llaves), Datos |
| **Tipo** (crédito / débito / total) | Qué compras con tarjeta se comparan con Bre-B | Tarjetas (panorama, franquicias, tarjetas y llaves) |
| **Franquicia** (todas / Visa / Mastercard / Amex, Diners y otras) | Idem. Con una franquicia, las transacciones de débito no se muestran: la SFC no las reparte por franquicia | Tarjetas (panorama, franquicias) |
| **Banco** (selección múltiple) | Filtra las entidades | Adopción > Bancos y entidades |

- Los KPI del período se comparan con el período anterior de igual largo; si el período incluye el mes en curso, los totales no se comparan.
- «Quién cede más», «Emisores» y «¿Crecen más lento?» comparan **ventanas fijas** (desde el lanzamiento frente al mismo periodo de años anteriores) y no responden a los filtros.
- La distribución por monto se recorta como la diferencia entre dos cortes mensuales acumulados. Si algún día falta un corte, la barra de filtros lo avisa y la gráfica muestra el acumulado.
- No hay filtros de persona natural/jurídica, mes suelto ni descargas: los datos no los sostienen.

## Datos (`data/`)

### BanRep (se actualizan solos)

| Archivo | Contenido | Fuente |
|---|---|---|
| `breb_mol_cortes.csv` | Transacciones, valor y ticket acumulados: cierres de mes y último corte, más fechas citadas por la prensa que coinciden con el reporte | Reporte MOL (Power BI público), con fecha final exacta |
| `breb_diario_mol.csv` | Transacciones por día desde el 6-oct-2025 (`fecha, transacciones`, enteros exactos) | Gráfico de evolución del reporte MOL |
| `breb_distribucion_monto.json` | Distribución de transacciones y valor por rango de monto en cada cierre de mes y en el último corte | Reporte MOL |
| `breb_acceso.json` | QR vs llave (desde el 19-ene-2026) | Reporte MOL, tecnología de acceso |
| `breb_dice.json` | Último corte: llaves por tipo, medios de pago (5 categorías), clientes y llaves naturales/jurídicas, con cantidades exactas | Reporte DICE |
| `breb_dice_historico.csv` | Totales del DICE en cada captura | Reporte DICE |
| `breb_dice_composicion.csv` | Las composiciones del DICE en cada captura (`fecha, panel, categoria, cantidad, porcentaje`) | Reporte DICE |

### SFC, datos abiertos (se actualizan solos)

Conjunto [«Tarjetas de crédito y débito»](https://www.datos.gov.co/d/h2jg-r3zg) de datos.gov.co, leído por `scripts/fetch_sfc_tarjetas.py`.

| Archivo | Contenido |
|---|---|
| `tarjetas_sfc_mensual.csv` | Por mes desde ene-2015: compras con tarjeta de crédito (nacionales) y débito, retiros con débito (número y monto en COP) y tarjetas vigentes (solo la línea de total) |
| `tarjetas_sfc_franquicia.csv` | Compras por producto y franquicia, por mes. Crédito: directo de la SFC (valor y número). Débito: solo valor, **estimado** (ver metodología) |
| `tarjetas_sfc_emisores_credito.csv` | Compras de crédito (número y monto) por emisor para Visa y Mastercard, desde oct-2023 |
| `tarjetas_sfc_entidades.csv` | Tarjetas vigentes y compras por entidad en el último mes, con el tipo oficial de la SFC (banco, compañía de financiamiento, cooperativa financiera) |

### Carga manual

| Archivo | Contenido | Fuente |
|---|---|---|
| `breb_participantes.json` | Lista oficial de entidades participantes (245 entidades y 5 sistemas de pago), con el cruce al nombre que usa la SFC. **Se actualiza a mano**: la página de BanRep tiene captcha | [BanRep, entidades participantes](https://www.banrep.gov.co/es/bre-b/preguntas-frecuentes/participantes), actualizada el 27-jul-2026 |
| `breb_bancos_prensa.json` | Transacciones, valor y llaves de algunos bancos al 7-feb-2026. Dato de prensa: BanRep no publica volumen por banco | [La República](https://www.larepublica.co/finanzas/bancolombia-y-davivienda-son-los-bancos-que-mas-dinero-mueven-a-traves-de-bre-b-4321886) |
| `breb_llaves_dice.csv` | Llaves por mes: jul-2025 a ene-2026 (documento técnico, Gráfico 6) y puntos etiquetados del reporte DICE | Documento técnico y reporte DICE |
| `breb_contexto.json` | Entidades por tipo (218 a ene-2026), origen de operaciones, contexto de transferencias y PIX | Documento técnico de BanRep (feb 2026) |

## Metodología y decisiones

- **Base de las tarjetas: emisores.** Se usan las cifras de los establecimientos de crédito, donde cada tarjeta cuenta una vez. Se excluyen las «administradoras de sistemas de pago de bajo valor» (Credibanco, Redeban, redes de Visa y Mastercard): reportan lo que procesa cada red y en 2025 sumaron entre 1,4 y 1,6 veces las cifras de los emisores, porque una misma compra puede contarse en la red y en el adquirente.
- **Crédito nacional.** Bre-B es doméstico, así que se comparan las compras nacionales con crédito (el análisis de tarjetas de visa-intelligence suma también las del exterior) y las compras con débito; no se incluyen retiros.
- **Débito por franquicia: estimado.** La SFC no lo reporta. Se reparte el valor de cada emisor y mes según sus ingresos por tarifa interbancaria (TII) de Visa y de Mastercard, con las excepciones manuales de visa-intelligence (Scotiabank Colpatria, Falabella, Mibanco y Nu como 100 % Mastercard; JFK como 100 % Visa) y Mastercard por defecto si el emisor no reporta TII. Alrededor del 95 % del valor sale del reparto por TII, 4 % de las excepciones y 1 % cae por defecto. Es una estimación propia con datos públicos: puede diferir de otras que usen información directa de los emisores, y si cambian las tarifas el reparto se mueve sin que cambie el volumen.
- **Ventanas comparables, nunca un mes suelto.** Comparar un mes contra el mismo mes del año anterior exageró una desaceleración que no existía. Los análisis de crecimiento usan sumas de 10 meses (oct a jul) frente al mismo periodo de uno y dos años antes.
- **Dilución no es sustitución.** Cuando Bre-B entra en el denominador, todo segmento de tarjetas pierde peso aunque crezca. Por eso «Quién cede más» separa el cambio de peso del crecimiento del valor.
- **«Bre-B equivale a» no es una cuota de mercado:** Bre-B también mueve transferencias entre personas.
- **Comparación causal.** Que las tarjetas no crezcan más lento desde Bre-B es una observación sin contrafactual; el valor es nominal (no ajustado por inflación) y la SFC publica con rezago de unos dos meses.

### Validaciones

El script exige y el dashboard muestra, en cada corrida:

- Transacciones × ticket reproduce el valor en cada corte; las distribuciones por monto suman exactamente el total del corte y son crecientes.
- La serie diaria suma exactamente el total acumulado del reporte (1.780.392.143 al 3-oct-2026, 363 días sin huecos).
- Cada panel del DICE suma su total (llaves, medios de pago, clientes).
- Las franquicias suman el total de su producto, los emisores suman la franquicia, y las entidades suman el total del mes (SFC).
- Las cifras del 31-ene-2026 coinciden con el documento técnico (370,4 M, $59 billones, $159.456) y varias fechas citadas por la prensa coinciden con el reporte.

## Actualización automática

BanRep incrusta sus reportes de Power BI en páginas con captcha, pero **los reportes en sí son públicos y se abren sin captcha** en `app.powerbi.com`. El workflow `update-data.yml` corre el **día 2 de cada mes** y tiene tres pasos:

1. `scripts/fetch_banrep.py` (Playwright) lee el reporte MOL (cortes, distribución, serie diaria recorriendo el gráfico) y el DICE (totales y las tres composiciones).
2. `scripts/fetch_sfc_tarjetas.py` (solo biblioteca estándar, sin credenciales) baja las compras con tarjeta de la SFC y reescribe todo el histórico, porque la SFC corrige meses anteriores; descarta el último mes si lo reportan muy pocas entidades.
3. Hace commit de lo que cambió; GitHub Pages se republica solo. Si un paso falla, lo que ya se leyó se publica igual y el job queda en rojo.

**Secrets** (una vez, en *Settings → Secrets and variables → Actions*). Deben ser la URL del reporte **completo**, no la de la portada:

| Secret | Valor |
|---|---|
| `BREB_MOL_URL` | URL `https://app.powerbi.com/view?r=…` del reporte de `banrep.gov.co/es/bre-b/indicadores-mol` (el que tiene el filtro de fecha). La de `/indicadores` es solo la portada («Intro») y no sirve |
| `BREB_DICE_URL` | Igual, para `/indicadores-dice` («Total de llaves registradas») |

Para obtenerlas: abrir la página de BanRep, dejar que cargue el reporte, abrirlo a pantalla completa y copiar la dirección de la barra. La dirección lleva la clave del reporte; si BanRep lo republica con otra, hay que actualizar el secret.

**Ejecutar a mano:** *Actions → Actualizar datos de BanRep → Run workflow*. La opción `backfill` revisa todos los cierres de mes y completa los cortes y distribuciones que falten; si BanRep corrigió una cifra ya guardada, el log imprime un `AVISO` y no la sobrescribe.

**Si falla:** el log imprime `[diagnóstico]` con la URL (sin clave), el título y el texto que vio el navegador, y se guarda una captura en el artefacto `debug-banrep`.

## Mantenimiento manual

- **Lista de participantes** (`breb_participantes.json`): actualizarla a mano desde la página de BanRep cuando cambie («Última actualización» aparece al pie de la lista). Si cambia el nombre de una entidad en la SFC, el cruce `sfc` del archivo debe coincidir exactamente con el nombre del CSV de entidades.
- **Cifras por banco de prensa**: no se actualizan solas; si BanRep, Asobancaria o los bancos entregan cifras actuales, se cargan en `breb_bancos_prensa.json`.
- **Siguiente mes de la SFC:** agosto de 2026 debería aparecer hacia mediados de octubre; el workflow lo incorpora solo y el dashboard recalcula las ventanas.

## Límites conocidos

- BanRep **no publica volumen por banco**; las cifras por banco son de prensa (feb-2026) y no verificables.
- Los datos de tarjetas llegan hasta julio de 2026; agosto y septiembre solo tienen Bre-B.
- Bancolombia incluye Nequi y Davivienda incluye Daviplata en las tarjetas de la SFC, aunque BanRep los lista aparte.
- Scotiabank Colpatria, Tuya, Procredit y Citibank reportan tarjetas a la SFC pero no aparecen en la lista de participantes del 27-jul-2026; el motivo no se conoce.

## Estructura

```
index.html                      dashboard (HTML + JS en un solo archivo)
data/                           datos que lee el dashboard
scripts/fetch_banrep.py         lectura de los reportes MOL y DICE (Playwright)
scripts/fetch_sfc_tarjetas.py   lectura de las tarjetas de la SFC (datos abiertos)
.github/workflows/update-data.yml   actualización mensual y manual
```

## Vista local

```bash
python3 -m http.server 8000
```
