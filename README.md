# Bre-B Intelligence — Colombia

Tracker de **Bre-B**, el sistema de pagos inmediatos interoperable del Banco de la República (lanzado el 6 de octubre de 2025): transacciones, valor, ticket, llaves y usuarios.

Proyecto hermano de [visa-intelligence](https://github.com/danielcastaed/visa-intelligence) (tarjetas, fuente SFC). Se mantiene aparte porque la fuente (BanRep), la cadencia y la estructura de datos son distintas.

## Cómo funciona

- `index.html` — dashboard estático (Chart.js), tema oscuro/claro. Lee `data/breb_hitos.csv`.
- `data/breb_hitos.csv` — una fila por **corte publicado**, con fuente, URL y estado de verificación.

Para agregar un corte: añadir una fila al CSV (columnas documentadas en la cabecera). Lo calculado aquí y no publicado por BanRep se marca `valor_derivado=true`.

## Limitación de datos (importante)

BanRep publica los indicadores de Bre-B ([DICE](https://www.banrep.gov.co/es/bre-b/indicadores) y [MOL](https://www.banrep.gov.co/es/bre-b/indicadores-mol)) en dashboards interactivos, sin descarga de datos, y su sitio bloquea clientes automatizados. Por eso la serie **no es mensual**: son hitos de documentos y comunicados oficiales, y de notas de prensa que los citan. Cada fila indica si ya fue cotejada contra el documento primario.

Se descartó un borrador anterior (`breb-intelligence-preview.html`) porque su serie no cuadraba con las cifras oficiales (p. ej. acumulado al 31-ene-2026: $32,5 B en el borrador vs $59 B en el documento técnico de BanRep) y varias secciones estáticas no tenían fuente trazable.

## Pendiente

- Cotejar con el documento primario las filas marcadas "pendiente cotejo".
- Cortes intermedios (marzo, mayo, julio–septiembre) cuando haya fuente fechada.
- Comparación contra volumen de tarjetas (publicar un JSON anual desde visa-intelligence y leerlo aquí).
- Refresco periódico (hoy es manual por la limitación de datos).

## Vista local

```bash
python3 -m http.server 8000
```
