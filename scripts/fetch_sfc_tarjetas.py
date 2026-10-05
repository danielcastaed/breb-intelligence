"""Compras con tarjeta de crédito y débito por mes, de los datos abiertos de la SFC (datos.gov.co).

Conjunto "Tarjetas de crédito y débito" (h2jg-r3zg). Se usa lo que reportan los emisores (establecimientos
de crédito): cada tarjeta se cuenta una vez. Se excluyen las "administradoras de sistemas de pago de bajo valor"
(Credibanco, Redeban, redes de Visa y Mastercard...) porque reportan lo que procesa cada red o adquirente y se
solapan entre sí.

Escribe data/tarjetas_sfc_mensual.csv con todo el histórico (la SFC corrige meses anteriores, así que se reescribe
completo). No necesita credenciales ni dependencias externas.

Uso:  python scripts/fetch_sfc_tarjetas.py
"""
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

URL = "https://www.datos.gov.co/resource/h2jg-r3zg.json"
OUT = Path(__file__).resolve().parent.parent / "data" / "tarjetas_sfc_mensual.csv"
EXCLUIDA = "ADMINISTRADORAS DE SISTEMAS DE PAGO DE BAJO VALOR"
CAMPOS = {  # descripción de la SFC (espacios normalizados) -> columna
    "Número de transacciones por compras a nivel nacional con tarjeta de crédito": "credito_compras_num",
    "Monto de las transacciones por compras con tarjeta de crédito a nivel nacional": "credito_compras_cop",
    "Número de transacciones por compras con tarjetas débito": "debito_compras_num",
    "Monto de transacciones por compras con tarjetas débito": "debito_compras_cop",
    "Número de transacciones por retiros con tarjetas débito": "debito_retiros_num",
    "Monto de transacciones por retiros con tarjetas débito": "debito_retiros_cop",
}
COLUMNAS = ["mes", *CAMPOS.values(), "entidades"]


def consulta(params):
    url = URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)


def main():
    donde = (f"(upper(descripcion) like '%TRANSACCIONES POR COMPRAS%' or upper(descripcion) like '%TRANSACCIONES POR RETIROS%') "
             f"and nombre_uca != '{EXCLUIDA}'")
    filas = consulta({"$select": "fechacorte,descripcion,sum(total_tarjetas) as v", "$where": donde,
                      "$group": "fechacorte,descripcion", "$limit": "50000"})
    # entidades que reportan compras con débito ese mes: guarda contra meses a medio publicar
    ents = consulta({"$select": "fechacorte,count(distinct nombreentidad) as n", "$where": donde + " and upper(descripcion) like '%COMPRAS CON TARJETAS D%'",
                     "$group": "fechacorte", "$limit": "50000"})
    entidades = {e["fechacorte"][:7]: int(e["n"]) for e in ents}

    meses = defaultdict(lambda: defaultdict(float))
    for r in filas:
        col = CAMPOS.get(re.sub(r"\s+", " ", r["descripcion"]).strip())
        if col:
            meses[r["fechacorte"][:7]][col] += float(r["v"])

    out = []
    for m in sorted(meses):
        d = meses[m]
        if set(d) != set(CAMPOS.values()):
            continue  # mes con líneas faltantes
        out.append({"mes": m, **{c: int(round(d[c])) for c in CAMPOS.values()}, "entidades": entidades.get(m, 0)})

    # validaciones: sin huecos, tickets plausibles y último mes completo
    for a, b in zip(out, out[1:]):
        ya, ma = map(int, a["mes"].split("-"))
        esperado = f"{ya + (ma == 12)}-{ma % 12 + 1:02d}"
        assert b["mes"] == esperado, f"hueco entre {a['mes']} y {b['mes']}"
    for r in out:
        for pref, lo, hi in (("credito_compras", 50_000, 400_000), ("debito_compras", 30_000, 300_000)):
            t = r[pref + "_cop"] / r[pref + "_num"]
            assert lo < t < hi, f"ticket fuera de rango en {r['mes']} ({pref}): {t:,.0f}"
    if len(out) >= 2 and out[-1]["entidades"] < 0.9 * out[-2]["entidades"]:
        print(f"Aviso: {out[-1]['mes']} tiene {out[-1]['entidades']} entidades frente a {out[-2]['entidades']}; se descarta por incompleto")
        out.pop()
    assert len(out) >= 139, f"faltan meses ({len(out)})"

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"SFC tarjetas: {len(out)} meses, {out[0]['mes']} a {out[-1]['mes']}")


if __name__ == "__main__":
    sys.exit(main())
