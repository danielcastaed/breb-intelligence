"""Lee los reportes públicos de Power BI de BanRep (MOL y DICE) y actualiza data/.

Los reportes se leen directamente en app.powerbi.com (sin el captcha del sitio de BanRep).
La dirección de cada reporte lleva una clave y se pasa por variable de entorno:

    BREB_MOL_URL   reporte "Indicadores Bre-B - MOL"
    BREB_DICE_URL  reporte "Indicadores Bre-B - DICE"

Uso:
    python scripts/fetch_banrep.py            # cierres de mes que falten + último corte + DICE
    python scripts/fetch_banrep.py --backfill # igual, pero revisa todos los meses desde el lanzamiento
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

DATA = Path(__file__).resolve().parent.parent / "data"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
RANGOS = ["1 - 1.000", "1.000 - 10.000", "10.000 - 50.000", "50.000 - 100.000",
          "100.000 - 500.000", "500.000 - 1.000.000", "Mayor a 1.000.000"]
FUENTE_MOL = "Reporte MOL de BanRep (Power BI público: indicadores-mol)"
LANZAMIENTO = dt.date(2025, 10, 6)


def num(s):
    return int(re.sub(r"[^\d]", "", s))


def lines(page):
    return [s.strip() for s in page.inner_text("body").split("\n") if s.strip()]


def corte_text(d):
    return f"Fecha de corte: {d.day} de {MESES[d.month - 1]} de {d.year}"


def diagnose(page):
    """Imprime en el log qué está viendo el navegador (sin la query string, que lleva la clave del reporte)."""
    u = page.url.split("?")[0]
    print(f"[diagnóstico] url={u} título={page.title()!r}")
    texto = " | ".join(s.strip() for s in page.inner_text("body").split("\n") if s.strip())
    print("[diagnóstico] texto:", texto[:1500])


def open_report(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=120_000)
    try:
        page.wait_for_function("document.body.innerText.includes('Fecha de corte')", timeout=120_000)
    except Exception:
        diagnose(page)
        raise


def available_range(page):
    """(inicio, fin) disponibles según el aria-label del campo de fecha final."""
    label = page.locator('input[aria-label^="Fecha de finalizaci"]').first.get_attribute("aria-label")
    m = re.search(r"(\d{2}/\d{2}/\d{4}) a (\d{2}/\d{2}/\d{4})", label)
    f = lambda s: dt.datetime.strptime(s, "%d/%m/%Y").date()
    return f(m.group(1)), f(m.group(2))


def set_end_date(page, d):
    box = page.locator('input[aria-label^="Fecha de finalizaci"]').first
    box.click()                      # el primer clic solo da foco
    box.click(click_count=3)
    box.press("Control+A")
    box.type(d.strftime("%d/%m/%Y"), delay=40)
    box.press("Enter")
    page.mouse.click(5, 400)         # confirma el filtro
    expected = corte_text(d)
    page.wait_for_function(
        "t => [...document.body.innerText.split('\\n')].filter(s => s.trim().startsWith('Fecha de corte')).some(s => s.trim() === t)",
        arg=expected, timeout=30_000)
    page.wait_for_timeout(1500)


def parse_mol(page):
    L = lines(page)
    i_tot = L.index("Total")
    txn, valor = num(L[i_tot + 1]), num(L[i_tot + 3])
    i_pesos = L.index("(pesos)")
    ticket = num(L[i_pesos + 2])
    filas = []
    for r in RANGOS:
        i = L.index(r)
        filas.append([r, num(L[i + 1]), num(L[i + 4])])
    assert sum(f[1] for f in filas) == txn and sum(f[2] for f in filas) == valor, "la distribución no suma el total"
    assert abs(valor / txn - ticket) < 2, "valor / transacciones no reproduce el ticket"
    return txn, valor, ticket, filas


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def month_ends(until):
    """Cierres de mes desde oct-2025 que son anteriores a `until`."""
    out, y, m = [], 2025, 10
    while True:
        first_next = dt.date(y + (m == 12), m % 12 + 1, 1)
        last_day = first_next - dt.timedelta(days=1)
        if last_day >= until:
            return out
        out.append(last_day)
        y, m = first_next.year, first_next.month


def update_mol(page, url, backfill):
    path = DATA / "breb_mol_cortes.csv"
    rows = read_csv(path)
    have = {r["fecha"] for r in rows if r["tipo"] in ("mensual", "inicio", "referencia")}
    dist_path = DATA / "breb_distribucion_monto.json"
    dist = json.loads(dist_path.read_text(encoding="utf-8"))
    dist_have = {c["fecha"] for c in dist["cortes"]}

    open_report(page, url)
    _, last = available_range(page)
    wanted = [d for d in month_ends(last) if d.isoformat() not in have]
    if not backfill:
        wanted = wanted[-2:]  # el mes recién cerrado (y uno de margen)
    added = []

    for d in wanted:
        set_end_date(page, d)
        txn, valor, ticket, filas = parse_mol(page)
        rows.append(dict(fecha=d.isoformat(), tipo="mensual", txn_acumuladas=txn, valor_acumulado_cop=valor,
                         ticket_promedio_cop=ticket, fuente=FUENTE_MOL, nota=""))
        if d.isoformat() not in dist_have:
            dist["cortes"].append({"fecha": d.isoformat(), "filas": filas})
        added.append(d.isoformat())

    # último corte disponible (reemplaza al anterior "ultimo")
    set_end_date(page, last)
    txn, valor, ticket, filas = parse_mol(page)
    rows = [r for r in rows if r["tipo"] != "ultimo" and r["fecha"] != last.isoformat()]
    es_fin_de_mes = (last + dt.timedelta(days=1)).month != last.month
    rows.append(dict(fecha=last.isoformat(), tipo="mensual" if es_fin_de_mes else "ultimo", txn_acumuladas=txn, valor_acumulado_cop=valor,
                     ticket_promedio_cop=ticket, fuente=FUENTE_MOL,
                     nota=f"Último corte disponible al momento de la captura ({last.isoformat()})"))
    dist["cortes"] = [c for c in dist["cortes"] if c["fecha"] != last.isoformat()] + [{"fecha": last.isoformat(), "filas": filas}]
    added.append(last.isoformat())

    rows.sort(key=lambda r: r["fecha"])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", "tipo", "txn_acumuladas", "valor_acumulado_cop",
                                          "ticket_promedio_cop", "fuente", "nota"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    dist["cortes"].sort(key=lambda c: c["fecha"], reverse=True)  # el más reciente primero (lo usa el dashboard)
    dist_path.write_text(json.dumps(dist, ensure_ascii=False, indent=1), encoding="utf-8")
    return added


def parse_dice(page):
    L = lines(page)
    corte = next(s for s in L if s.startswith("Fecha de corte"))
    m = re.search(r"(\d+) de (\w+) de (\d{4})", corte)
    fecha = dt.date(int(m.group(3)), MESES.index(m.group(2)) + 1, int(m.group(1)))
    i = L.index("Total de llaves registradas")
    vals = [s for s in L[i + 1:i + 14] if re.fullmatch(r"[\d.]+|\d,\d", s)]
    # orden del reporte: llaves, medios de pago, clientes, llaves/medio, llaves/cliente, medios/cliente
    prom = lambda s: float(s.replace(",", "."))
    return fecha, dict(llaves=num(vals[0]), medios_de_pago=num(vals[1]), clientes=num(vals[2]),
                       llaves_por_medio=prom(vals[3]), llaves_por_cliente=prom(vals[4]), medios_por_cliente=prom(vals[5]))


# Cada sector de los gráficos de dona trae su nombre y cantidad exacta en el aria-label.
ETIQUETAS = {
    "tipo_de_llave": re.compile(r"^Tipo llave (.+?)\. Cantidad de llaves ([\d.]+) \(([\d,]+)%\)\.$"),
    "medio_de_pago": re.compile(r"^Tipo medio de pago (.+?)\. Cantidad medios de pago ([\d.]+) \(([\d,]+)%\)\.$"),
    "cliente": re.compile(r"^Tipo usuario (.+?)\. Cantidad de clientes ([\d.]+) \(([\d,]+)%\)\.$"),
    "llaves_por_tipo_de_cliente": re.compile(r"^Tipo de cliente (.+?)\. Cantidad de llaves ([\d.]+) \(([\d,]+)%\)\.$"),
}
PANELES = [("tipo_de_llave", "Tipo llave "), ("medio_de_pago", "Tipo medio de pago "), ("cliente", "Tipo usuario ")]


def parse_composicion(labels):
    """aria-labels -> {panel: [(nombre, cantidad, porcentaje)]}, de mayor a menor."""
    out = {}
    for panel, rx in ETIQUETAS.items():
        filas = {}
        for lab in labels:
            m = rx.match(lab.strip())
            if m:
                filas[m.group(1)] = (m.group(1), num(m.group(2)), float(m.group(3).replace(",", ".")))
        out[panel] = sorted(filas.values(), key=lambda f: -f[1])
    return out


def read_composicion(page):
    labels = lambda: page.evaluate("() => [...document.querySelectorAll('[aria-label]')].map(e => e.getAttribute('aria-label'))")
    # las pestañas Llaves / Medios de pago / Clientes son imágenes sin etiqueta: las tres primeras del costado izquierdo
    idx = page.evaluate("""() => { const w = innerWidth;
        return [...document.querySelectorAll('.imageContainer')].map((e, i) => ({ i, r: e.getBoundingClientRect() }))
          .filter(o => o.r.left < w * 0.05 && o.r.width > w * 0.2 && o.r.width < w * 0.4)
          .sort((a, b) => a.r.top - b.r.top).map(o => o.i); }""")
    if len(idx) < 3:
        raise RuntimeError(f"no encontré las pestañas del panel DICE (imágenes candidatas: {len(idx)})")
    out = {}
    for k, (panel, prefijo) in enumerate(PANELES):
        if not any(l.startswith(prefijo) for l in labels()):
            page.locator(".imageContainer").nth(idx[k]).click()
            page.wait_for_function("p => [...document.querySelectorAll('[aria-label]')].some(e => e.getAttribute('aria-label').startsWith(p))",
                                   arg=prefijo, timeout=20_000)
            page.wait_for_timeout(800)
        leidos = parse_composicion(labels())
        out[panel] = leidos[panel]
        if leidos["llaves_por_tipo_de_cliente"]:  # visual aparte, siempre presente
            out["llaves_por_tipo_de_cliente"] = leidos["llaves_por_tipo_de_cliente"]
    return out


def validar_composicion(tot, comp):
    esperado = dict(tipo_de_llave=tot["llaves"], medio_de_pago=tot["medios_de_pago"], cliente=tot["clientes"],
                    llaves_por_tipo_de_cliente=tot["llaves"])
    for panel, total in esperado.items():
        assert comp[panel] and sum(f[1] for f in comp[panel]) == total, f"{panel}: las categorías no suman el total ({total})"


def read_csv_or_empty(path):
    return read_csv(path) if path.exists() else []


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def dice_json(fecha, tot, comp, previo):
    lista = lambda filas: [[n, round(c / 1e6, 2), p, c] for n, c, p in filas]  # [nombre, millones, %, cantidad]
    par = lambda filas, nombre: next(([round(c / 1e6, 2), p, c] for n, c, p in filas if n == nombre), None)
    return {
        "fuente": previo.get("fuente", "Reporte DICE de BanRep (Power BI público: indicadores-dice)"),
        "corte": fecha.isoformat(),
        "nota": previo.get("nota", "Indicadores construidos con el total de llaves activas y bloqueadas (nota del propio reporte)."),
        "totales": tot,
        "tipos_de_llave": lista(comp["tipo_de_llave"]),
        "medios_de_pago": lista(comp["medio_de_pago"]),
        "medios_de_pago_nota": "Categorías y cantidades tal como las publica el reporte (etiqueta de cada sector del gráfico).",
        "clientes": {"naturales": par(comp["cliente"], "Persona Natural"), "juridicas": par(comp["cliente"], "Persona Jurídica")},
        "llaves_por_tipo_de_cliente": {"naturales": par(comp["llaves_por_tipo_de_cliente"], "Persona Natural"),
                                       "juridicas": par(comp["llaves_por_tipo_de_cliente"], "Persona Jurídica")},
    }


def guardar_dice(fecha, tot, comp):
    """Escribe el histórico de totales, la composición de esa captura y el JSON del último corte. Idempotente."""
    f = fecha.isoformat()
    path = DATA / "breb_dice_historico.csv"
    rows = read_csv_or_empty(path)
    if f not in {r["fecha"] for r in rows}:
        rows.append(dict(fecha=f, llaves=tot["llaves"], medios_de_pago=tot["medios_de_pago"], clientes=tot["clientes"],
                         llaves_por_cliente=tot["llaves_por_cliente"]))
        rows.sort(key=lambda r: r["fecha"])
        write_csv(path, ["fecha", "llaves", "medios_de_pago", "clientes", "llaves_por_cliente"], rows)

    path = DATA / "breb_dice_composicion.csv"
    rows = [r for r in read_csv_or_empty(path) if r["fecha"] != f]
    for panel, filas in comp.items():
        rows += [dict(fecha=f, panel=panel, categoria=n, cantidad=c, porcentaje=p) for n, c, p in filas]
    rows.sort(key=lambda r: (r["fecha"], r["panel"]))
    write_csv(path, ["fecha", "panel", "categoria", "cantidad", "porcentaje"], rows)

    path = DATA / "breb_dice.json"
    previo = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if f >= previo.get("corte", ""):
        path.write_text(json.dumps(dice_json(fecha, tot, comp, previo), ensure_ascii=False, indent=1), encoding="utf-8")
    return f


def update_dice(page, url):
    open_report(page, url)
    try:  # el encabezado aparece antes que las cifras: espera a que las tres primeras estén pintadas
        page.wait_for_function(
            """() => { const L = document.body.innerText.split('\\n').map(s => s.trim()).filter(Boolean);
                      const i = L.indexOf('Total de llaves registradas');
                      return i >= 0 && L.slice(i + 1, i + 14).filter(s => /^[\\d.]+$/.test(s)).length >= 3; }""",
            timeout=60_000)
        fecha, tot = parse_dice(page)
        comp = read_composicion(page)
        validar_composicion(tot, comp)
    except Exception:
        diagnose(page)
        raise
    return guardar_dice(fecha, tot, comp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true")
    args = ap.parse_args()
    mol, dice = os.environ.get("BREB_MOL_URL"), os.environ.get("BREB_DICE_URL")
    if not mol:
        sys.exit("Falta BREB_MOL_URL")
    debug = Path("debug")
    debug.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(viewport={"width": 1456, "height": 900}, locale="es-CO",
                                  user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36").new_page()
        fallo = None
        try:
            print("MOL, cortes agregados:", update_mol(page, mol, args.backfill))
            if dice:
                print("DICE, corte agregado:", update_dice(page, dice))
        except Exception as e:
            page.screenshot(path=str(debug / "error.png"), full_page=True)
            (debug / "error.txt").write_text(page.inner_text("body"), encoding="utf-8")
            fallo = e
        finally:
            browser.close()
    if fallo:  # lo ya escrito en data/ se publica igual (ver workflow); el job queda en rojo
        raise fallo


if __name__ == "__main__":
    main()
