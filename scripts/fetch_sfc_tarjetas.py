"""Compras con tarjeta de crédito y débito por mes, de los datos abiertos de la SFC (datos.gov.co).

Conjunto "Tarjetas de crédito y débito" (h2jg-r3zg). Se usa lo que reportan los emisores (establecimientos
de crédito): cada tarjeta se cuenta una vez. Se excluyen las "administradoras de sistemas de pago de bajo valor"
(Credibanco, Redeban, redes de Visa y Mastercard...) porque reportan lo que procesa cada red o adquirente y se
solapan entre sí.

Escribe todo el histórico (la SFC corrige meses anteriores, así que se reescribe completo):
  data/tarjetas_sfc_mensual.csv     compras y retiros por producto (crédito / débito)
  data/tarjetas_sfc_franquicia.csv  compras por producto y franquicia
No necesita credenciales ni dependencias externas.

Franquicia. En crédito la SFC la reporta directo (campo nombre_uca). En débito no: se estima por emisor y mes con la
llave de distribución de los ingresos por tarifa interbancaria (TII) de Visa y de Mastercard, igual que el análisis
de tarjetas de visa-intelligence, con las mismas excepciones manuales (BANCOS_100_MC / BANCOS_100_VISA) y Mastercard
por defecto cuando el emisor no reporta TII. Por eso el débito por franquicia es una estimación, y solo se publica en valor.

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
DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "tarjetas_sfc_mensual.csv"
OUT_FRANQ = DATA / "tarjetas_sfc_franquicia.csv"
FRANQ_CREDITO = {"CREDIBANCO-VISA": "VISA", "MASTERCARD": "MASTERCARD", "AMERICAN EXPRESS": "AMEX", "DINERS": "DINERS",
                 "OTRAS TARJETAS DE CREDITO": "OTRAS"}
BANCOS_100_MC = {"SCOTIABANK COLPATRIA S.A.", "BANCO FALABELLA S.A.", "MIBANCO S.A.", "NU FINANCIERA S.A."}
BANCOS_100_VISA = {"JFK COOPERATIVA FINANCIERA"}  # excepción manual: casi no reporta TII Visa
EXCLUIDA = "ADMINISTRADORAS DE SISTEMAS DE PAGO DE BAJO VALOR"
CAMPOS = {  # descripción de la SFC (espacios normalizados) -> columna
    "Número de transacciones por compras a nivel nacional con tarjeta de crédito": "credito_compras_num",
    "Monto de las transacciones por compras con tarjeta de crédito a nivel nacional": "credito_compras_cop",
    "Número de transacciones por compras con tarjetas débito": "debito_compras_num",
    "Monto de transacciones por compras con tarjetas débito": "debito_compras_cop",
    "Número de transacciones por retiros con tarjetas débito": "debito_retiros_num",
    "Monto de transacciones por retiros con tarjetas débito": "debito_retiros_cop",
}
VIGENTES = {  # solo la línea de total; las de contactless / sin chip son subconjuntos y no se suman
    "Número total de tarjetas de crédito vigentes a la fecha de corte": "credito_vigentes",
    "Número total de tarjetas débito vigentes a la fecha de corte": "debito_vigentes",
}
COLUMNAS = ["mes", *CAMPOS.values(), *VIGENTES.values(), "entidades"]


def consulta(params):
    url = URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)


def franquicias(meses_ok):
    """Compras por producto y franquicia. Crédito: directo de la SFC. Débito: valor estimado por TII."""
    excl = f"nombre_uca != '{EXCLUIDA}'"
    cred = consulta({"$select": "fechacorte,nombre_uca,descripcion,sum(total_tarjetas) as v",
                     "$where": excl + " and (upper(descripcion) like '%COMPRAS A NIVEL NACIONAL CON TARJETA DE CR%' or upper(descripcion) like '%COMPRAS CON TARJETA DE CR%NIVEL NACIONAL%')",
                     "$group": "fechacorte,nombre_uca,descripcion", "$limit": "50000"})
    deb = consulta({"$select": "fechacorte,nombreentidad,descripcion,sum(total_tarjetas) as v",
                    "$where": excl + " and (descripcion like 'Monto de transacciones por compras con tarjetas d%' or upper(descripcion) like 'INGRESOS POR TARIFA INTERBANCARIA DE INTERCAMBIO - TII POR TARJETA %')",
                    "$group": "fechacorte,nombreentidad,descripcion", "$limit": "50000"})

    filas = defaultdict(lambda: {"num": 0.0, "cop": 0.0})  # (mes, producto, franquicia)
    for r in cred:
        f = FRANQ_CREDITO.get(r["nombre_uca"])
        if not f:
            continue
        d = re.sub(r"\s+", " ", r["descripcion"])
        filas[(r["fechacorte"][:7], "credito", f)]["num" if d.startswith("Número") else "cop"] += float(r["v"])

    monto, tii = defaultdict(float), defaultdict(lambda: defaultdict(float))
    for r in deb:
        d, m, e = re.sub(r"\s+", " ", r["descripcion"]), r["fechacorte"][:7], r["nombreentidad"].strip('"')
        if d.startswith("Monto de transacciones"):
            monto[(m, e)] += float(r["v"])
        else:
            up = d.upper()
            f = "VISA" if ("ELECTR" in up or "DÉBITO VISA" in up or "DEBITO VISA" in up) else "MASTERCARD"
            tii[(m, e)][f] += float(r["v"])
    for (m, e), v in monto.items():
        if e in BANCOS_100_MC:
            reparto = {"MASTERCARD": 1.0}
        elif e in BANCOS_100_VISA:
            reparto = {"VISA": 1.0}
        elif sum(tii[(m, e)].values()) > 0:
            tot = sum(tii[(m, e)].values())
            reparto = {f: x / tot for f, x in tii[(m, e)].items()}
        else:
            reparto = {"MASTERCARD": 1.0}
        for f, share in reparto.items():
            filas[(m, "debito", f)]["cop"] += v * share

    out = []
    for (m, prod, f), d in sorted(filas.items()):
        if m in meses_ok:
            out.append({"mes": m, "producto": prod, "franquicia": f, "compras_num": int(round(d["num"])) if prod == "credito" else "",
                        "compras_cop": int(round(d["cop"])), "metodo": "directo" if prod == "credito" else "estimado_tii"})
    # las partes deben sumar el total por producto de tarjetas_sfc_mensual.csv
    for m, tot in meses_ok.items():
        for prod, col in (("credito", "credito_compras_cop"), ("debito", "debito_compras_cop")):
            suma = sum(r["compras_cop"] for r in out if r["mes"] == m and r["producto"] == prod)
            assert abs(suma - tot[col]) <= 50, f"{prod} {m}: franquicias suman {suma:,}, el total es {tot[col]:,}"
    with open(OUT_FRANQ, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["mes", "producto", "franquicia", "compras_num", "compras_cop", "metodo"], lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    return len(out)


def main():
    donde = (f"(upper(descripcion) like '%TRANSACCIONES POR COMPRAS%' or upper(descripcion) like '%TRANSACCIONES POR RETIROS%') "
             f"and nombre_uca != '{EXCLUIDA}'")
    filas = consulta({"$select": "fechacorte,descripcion,sum(total_tarjetas) as v", "$where": donde,
                      "$group": "fechacorte,descripcion", "$limit": "50000"})
    # entidades que reportan compras con débito ese mes: guarda contra meses a medio publicar
    ents = consulta({"$select": "fechacorte,count(distinct nombreentidad) as n", "$where": donde + " and upper(descripcion) like '%COMPRAS CON TARJETAS D%'",
                     "$group": "fechacorte", "$limit": "50000"})
    entidades = {e["fechacorte"][:7]: int(e["n"]) for e in ents}

    vig = consulta({"$select": "fechacorte,descripcion,sum(total_tarjetas) as v",
                    "$where": f"nombre_uca != '{EXCLUIDA}' and (descripcion like 'Número total de tarjetas de crédito vigentes%a la fecha de corte' or descripcion like 'Número total de tarjetas débito%vigentes%a la fecha de corte')",
                    "$group": "fechacorte,descripcion", "$limit": "50000"})
    vigentes = defaultdict(lambda: defaultdict(float))
    for r in vig:
        col = VIGENTES.get(re.sub(r"\s+", " ", r["descripcion"]).strip())
        if col:
            vigentes[r["fechacorte"][:7]][col] += float(r["v"])

    meses = defaultdict(lambda: defaultdict(float))
    for r in filas:
        col = CAMPOS.get(re.sub(r"\s+", " ", r["descripcion"]).strip())
        if col:
            meses[r["fechacorte"][:7]][col] += float(r["v"])

    out = []
    for m in sorted(meses):
        d = meses[m]
        if set(d) != set(CAMPOS.values()) or set(vigentes[m]) != set(VIGENTES.values()):
            continue  # mes con líneas faltantes
        out.append({"mes": m, **{c: int(round(d[c])) for c in CAMPOS.values()},
                    **{c: int(round(vigentes[m][c])) for c in VIGENTES.values()}, "entidades": entidades.get(m, 0)})

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
    print("SFC tarjetas por franquicia:", franquicias({r["mes"]: r for r in out}), "filas")


if __name__ == "__main__":
    sys.exit(main())
