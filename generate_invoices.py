#!/usr/bin/env python3
"""
Generate synthetic Moroccan-style invoices (French) with ground-truth labels.

Install:
    pip install reportlab pypdfium2 pillow numpy

Run:
    python generate_invoices.py --n 200 --out data/synthetic --seed 42

Output:
    <out>/pdf/inv_0001.pdf       clean vector PDF (text is selectable)
    <out>/images/inv_0001.jpg    scan-like image (rotation, blur, noise, JPEG) -> feed this to OCR
    <out>/labels/inv_0001.json   ground truth for evaluation
    <out>/manifest.csv           one row per invoice, with dev/test split

Design notes:
  * A small pool of suppliers and 1-2 "customer" companies (the tenant) is reused,
    so questions like "who do we owe the most?" are meaningful later for the SQL agent.
  * Each supplier keeps its own layout, so the extractor must generalise across layouts.
  * The split is BY SUPPLIER: test suppliers/layouts are never seen during dev.
  * A field is in the label only if it is visible on the document
    (hidden patente / client ICE / due date -> null).
  * All identifiers (ICE, IF, RC, patente) are random fictitious numbers.
    Formats are only approximately realistic and are NOT checksum-valid.
"""
import argparse
import csv
import io
import json
import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageEnhance, ImageFilter
from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

W, H = A4
M = 40

MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
          "août", "septembre", "octobre", "novembre", "décembre"]

CITIES = {"Casablanca": "20000", "Rabat": "10000", "Tanger": "90000", "Marrakech": "40000",
          "Fès": "30000", "Agadir": "80000", "Mohammedia": "28800", "Oujda": "60000",
          "Kénitra": "14000", "Salé": "11000", "Témara": "12000", "Meknès": "50000",
          "Tétouan": "93000", "El Jadida": "24000", "Nador": "62000"}

STREETS = ["Bd Zerktouni", "Avenue Mohammed V", "Rue Ibn Sina", "Bd Mohammed VI",
           "Rue Al Massira", "Avenue Hassan II", "Rue des Orangers", "Bd Anfa",
           "Rue Moulay Youssef", "Avenue des FAR", "Rue Al Qods", "Bd Abdelmoumen"]

NAME_A = ["Atlas", "Maghreb", "Sahara", "Anfa", "Souss", "Rif", "Chaouia", "Doukkala",
          "Tingis", "Marrakech", "Oum Errabia", "Bouregreg", "Zagora", "Ifrane", "Tafilalet"]
NAME_B = ["Distribution", "Négoce", "Services", "Electro", "Froid", "Cuisine Pro",
          "Import Export", "Logistique", "Bureautique", "Matériaux", "Informatique",
          "Maintenance", "Équipement", "Conseil", "Hygiène"]
LEGAL = ["SARL", "SA", "SARL AU", "SNC"]

# (description, min price HT, max price HT)
CATALOG = [
    ("Ramette papier A4 80g", 28, 45),
    ("Cartouche toner HP 305A", 550, 950),
    ("Ordinateur portable 15,6 pouces", 4200, 9800),
    ("Écran 24 pouces", 1100, 1900),
    ("Maintenance climatisation - forfait", 600, 2500),
    ("Transport de marchandises Casablanca-Rabat", 800, 2200),
    ("Nettoyage des locaux - mensuel", 1500, 4500),
    ("Hébergement web annuel", 900, 2400),
    ("Formation bureautique - journée", 2500, 5000),
    ("Réfrigérateur professionnel inox", 6500, 14000),
    ("Four électrique encastrable", 2800, 6500),
    ("Hotte aspirante inox", 1500, 3800),
    ("Lave-vaisselle 12 couverts", 3500, 7500),
    ("Installation et mise en service", 300, 1200),
    ("Câble réseau RJ45 Cat6 (bobine)", 350, 900),
    ("Chaise de bureau ergonomique", 650, 1600),
    ("Bureau 140 cm", 900, 2200),
    ("Fournitures diverses de bureau", 150, 700),
    ("Impression flyers A5 (1000 ex.)", 450, 1300),
    ("Carburant - carte prépayée", 1000, 5000),
    ("Licence logiciel comptable", 1800, 6000),
    ("Audit de sécurité applicative - forfait", 6000, 20000),
    ("Palette eau minérale", 180, 320),
    ("Gants et EPI - lot", 250, 900),
    ("Pièces détachées - lot", 400, 3500),
    ("Stylos à bille (boîte de 50)", 40, 95),
    ("Location de véhicule utilitaire - jour", 450, 900),
]

FONTS = {"sans": ("Helvetica", "Helvetica-Bold"),
         "serif": ("Times-Roman", "Times-Bold"),
         "mono": ("Courier", "Courier-Bold")}
PALETTE = ["#1f3a5f", "#7a1f2b", "#1b5e3b", "#333333", "#0b5c73", "#5a2a82"]


# ---------------------------------------------------------------- helpers
def q(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def digits(rng, n):
    return "".join(str(rng.randint(0, 9)) for _ in range(n))


def fmt_money(v, style):
    s = f"{v:,.2f}"
    if style == "fr":
        return s.replace(",", " ").replace(".", ",")
    if style == "plain":
        return s.replace(",", "").replace(".", ",")
    return s


def fmt_date(d, style):
    if style == "long":
        return f"{d.day} {MONTHS[d.month - 1]} {d.year}"
    sep = "/" if style == "slash" else "-"
    return f"{d.day:02d}{sep}{d.month:02d}{sep}{d.year}"


def t(c, x, y, text, font="Helvetica", size=9, color=black, align="l"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "r":
        c.drawRightString(x, y, text)
    elif align == "c":
        c.drawCentredString(x, y, text)
    else:
        c.drawString(x, y, text)


# ---------------------------------------------------------------- data
def make_company(rng, with_catalog=False):
    city = rng.choice(list(CITIES))
    co = {
        "name": f"{rng.choice(NAME_A)} {rng.choice(NAME_B)} {rng.choice(LEGAL)}",
        "ice": digits(rng, 15),
        "if": digits(rng, 8),
        "rc": digits(rng, 6),
        "patente": digits(rng, 8),
        "address": f"{rng.randint(1, 240)} {rng.choice(STREETS)}",
        "postal_code": CITIES[city],
        "city": city,
    }
    if with_catalog:
        items = rng.sample(CATALOG, k=rng.randint(4, 8))
        co["_items"] = [(d, q(rng.uniform(lo, hi) if rng.random() < 0.5 else round(rng.uniform(lo, hi) / 5) * 5))
                        for d, lo, hi in items]
        co["_seq"] = rng.randint(1, 300)
        co["_numfmt"] = rng.choice(["F{y}-{n:04d}", "FAC/{y}/{n:05d}", "{y}{n:05d}", "FA-{n:06d}", "{n:04d}/{y}"])
        co["_terms"] = rng.choice([0, 15, 30, 30, 45, 60])
        co["_pay_prob"] = rng.uniform(0.35, 0.9)
    return co


def make_style(rng, template=None):
    template = template or rng.choices(["classic", "modern", "minimal"], [4, 4, 2])[0]
    fam = "mono" if template == "minimal" else rng.choice(["sans", "sans", "serif"])
    font, bold = FONTS[fam]
    return {
        "template": template, "font": font, "bold": bold,
        "color": HexColor(rng.choice(PALETTE)),
        "money": rng.choice(["fr", "fr", "plain", "en"]),
        "date": rng.choice(["slash", "slash", "dash", "long"]),
        "cur": rng.choice(["DH", "MAD", "Dhs"]),
        "title": rng.choice(["FACTURE", "FACTURE", "Facture"]),
        "lbl_no": rng.choice(["N°", "N° :", "Réf :"]),
        "lbl_client": rng.choice(["Client", "Facturé à", "Destinataire"]),
        "lbl_from": rng.choice(["Émetteur", "Fournisseur", "Vendeur"]),
        "lbl_due": rng.choice(["Échéance", "Date d'échéance", "À payer avant le"]),
        "l_ice": rng.choice(["ICE", "N° ICE", "ICE N°"]),
        "l_if": rng.choice(["IF", "I.F.", "Identifiant fiscal"]),
        "l_rc": rng.choice(["RC", "R.C.", "N° RC"]),
        "l_pat": rng.choice(["Patente", "TP", "Taxe professionnelle"]),
        "h_desc": rng.choice(["Désignation", "Description", "Libellé"]),
        "h_qty": rng.choice(["Qté", "Quantité", "Qte"]),
        "h_pu": rng.choice(["P.U. HT", "PU HT", "Prix unitaire HT"]),
        "h_total": rng.choice(["Total HT", "Montant HT"]),
        "l_ht": rng.choice(["Total HT", "Montant HT", "Sous-total HT"]),
        "l_tva": rng.choice(["TVA {rate}%", "TVA ({rate} %)"]),
        "l_ttc": rng.choice(["Total TTC", "Net à payer TTC", "Montant TTC"]),
        "show_patente": rng.random() < 0.6,
        "show_customer_ice": rng.random() < 0.85,
        "zebra": Color(0.95, 0.95, 0.95),
    }


def make_invoice(rng, idx, supplier, customer, style, d0, d1):
    span = (d1 - d0).days
    issue = d0 + timedelta(days=rng.randint(0, span))
    terms = supplier["_terms"]
    due = issue + timedelta(days=terms) if terms > 0 else None
    supplier["_seq"] += rng.randint(1, 4)
    number = supplier["_numfmt"].format(y=issue.year, n=supplier["_seq"])

    lines = []
    for desc, unit in rng.sample(supplier["_items"], k=min(len(supplier["_items"]), rng.choice([1, 2, 2, 3, 3, 4, 5, 6, 8]))):
        qty = rng.randint(5, 60) if unit < 100 else (rng.randint(1, 20) if unit < 1000 else rng.randint(1, 4))
        lines.append({"description": desc, "quantity": qty, "unit_price_ht": unit, "total_ht": q(unit * qty)})
    total_ht = sum((ln["total_ht"] for ln in lines), Decimal("0"))
    rate = rng.choices([20, 10, 14, 7], [80, 10, 5, 5])[0]
    tva = q(total_ht * Decimal(rate) / 100)
    ttc = total_ht + tva

    paid = rng.random() < supplier["_pay_prob"]
    paid_date = issue + timedelta(days=rng.randint(0, terms + 20)) if paid else None
    stamp = paid and rng.random() < 0.5

    sup = {k: v for k, v in supplier.items() if not k.startswith("_")}
    cus = {k: v for k, v in customer.items() if not k.startswith("_")}
    if not style["show_patente"]:
        sup["patente"] = None
    if not style["show_customer_ice"]:
        cus["ice"] = None
    cus.pop("patente", None)
    cus.pop("rc", None)
    cus.pop("if", None)

    return {
        "id": f"inv_{idx:04d}", "invoice_number": number,
        "invoice_date": issue, "due_date": due,
        "supplier": sup, "customer": cus, "lines": lines,
        "total_ht": total_ht, "tva_rate": rate, "total_tva": tva, "total_ttc": ttc,
        "currency": "MAD", "payment_status": "paid" if paid else "unpaid",
        "paid_date": paid_date, "payment_status_visible": stamp,
    }


def to_label(inv, style, scan):
    def conv(v):
        if isinstance(v, Decimal):
            return float(v)
        if isinstance(v, date):
            return v.isoformat()
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        if isinstance(v, list):
            return [conv(x) for x in v]
        return v
    out = conv(inv)
    out["template"] = style["template"]
    out["scan_profile"] = scan
    out["language"] = "fr"
    return out


# ---------------------------------------------------------------- rendering
def id_parts(sup, s):
    parts = [f"{s['l_ice']} : {sup['ice']}", f"{s['l_if']} : {sup['if']}",
             f"{s['l_rc']} : {sup['rc']} {sup['city']}"]
    if sup.get("patente"):
        parts.append(f"{s['l_pat']} : {sup['patente']}")
    return parts


def customer_lines(cus, s):
    lines = [cus["address"], f"{cus['postal_code']} {cus['city']}"]
    if cus.get("ice"):
        lines.append(f"{s['l_ice']} : {cus['ice']}")
    return lines


def draw_table(c, inv, s, y_top, header_bg, header_fg, zebra, grid, row_h=20, size=9):
    f, fb = s["font"], s["bold"]
    xs = [M, M + 265, M + 325, M + 430, W - M]
    heads = [s["h_desc"], s["h_qty"], s["h_pu"], s["h_total"]]
    if header_bg is not None:
        c.setFillColor(header_bg)
        c.rect(M, y_top - row_h, W - 2 * M, row_h, fill=1, stroke=0)
    t(c, xs[0] + 5, y_top - row_h + 7, heads[0], fb, size, header_fg)
    for i in (1, 2, 3):
        t(c, xs[i + 1] - 5, y_top - row_h + 7, heads[i], fb, size, header_fg, "r")
    y = y_top - row_h
    if header_bg is None:
        c.setStrokeColor(black)
        c.setLineWidth(0.6)
        c.line(M, y, W - M, y)
    for k, ln in enumerate(inv["lines"]):
        if zebra is not None and k % 2 == 1:
            c.setFillColor(zebra)
            c.rect(M, y - row_h, W - 2 * M, row_h, fill=1, stroke=0)
        sz = size
        while c.stringWidth(ln["description"], f, sz) > xs[1] - xs[0] - 10 and sz > 5.5:
            sz -= 0.5
        base = y - row_h + 7
        t(c, xs[0] + 5, base, ln["description"], f, sz)
        t(c, xs[2] - 5, base, str(ln["quantity"]), f, size, black, "r")
        t(c, xs[3] - 5, base, fmt_money(ln["unit_price_ht"], s["money"]), f, size, black, "r")
        t(c, xs[4] - 5, base, fmt_money(ln["total_ht"], s["money"]), f, size, black, "r")
        y -= row_h
    if grid:
        c.setStrokeColor(Color(0.4, 0.4, 0.4))
        c.setLineWidth(0.5)
        c.rect(M, y, W - 2 * M, y_top - y)
        for x in xs[1:-1]:
            c.line(x, y, x, y_top)
        for k in range(1, len(inv["lines"]) + 1):
            c.line(M, y_top - k * row_h, W - M, y_top - k * row_h)
    return y


def draw_totals(c, inv, s, y_top, fill=None):
    f, fb = s["font"], s["bold"]
    rows = [(s["l_ht"], inv["total_ht"]),
            (s["l_tva"].format(rate=inv["tva_rate"]), inv["total_tva"]),
            (s["l_ttc"], inv["total_ttc"])]
    x0 = W - M - 215
    if fill is not None:
        c.setFillColor(fill)
        c.rect(x0 - 8, y_top - 58, 223, 62, fill=1, stroke=0)
    y = y_top - 14
    for i, (lab, val) in enumerate(rows):
        bold = i == 2
        t(c, x0, y, lab, fb if bold else f, 10)
        t(c, W - M - 4, y, f"{fmt_money(val, s['money'])} {s['cur']}", fb if bold else f, 10, black, "r")
        y -= 18
    return y


def draw_footer(c, inv, s):
    sup = inv["supplier"]
    text = " - ".join([sup["name"]] + id_parts(sup, s))
    size = 7
    while c.stringWidth(text, s["font"], size) > W - 2 * M and size > 5:
        size -= 0.5
    t(c, W / 2, 34, text, s["font"], size, Color(0.35, 0.35, 0.35), "c")
    terms = "Paiement à réception" if inv["due_date"] is None else "Paiement par virement ou chèque"
    t(c, W / 2, 46, terms, s["font"], 7.5, Color(0.35, 0.35, 0.35), "c")


def draw_stamp(c, inv):
    if not inv["payment_status_visible"]:
        return
    green = Color(0.1, 0.45, 0.25)
    c.saveState()
    c.translate(W - 190, 190)
    c.rotate(18)
    c.setStrokeColor(green)
    c.setFillColor(green)
    c.setLineWidth(2)
    c.rect(-70, -18, 140, 36)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(0, -6, "ACQUITTÉE")
    c.restoreState()


def tpl_classic(c, inv, s):
    f, fb, col = s["font"], s["bold"], s["color"]
    sup, cus = inv["supplier"], inv["customer"]
    y = H - 50
    t(c, M, y, sup["name"], fb, 15, col)
    y -= 16
    for ln in [sup["address"], f"{sup['postal_code']} {sup['city']}"] + id_parts(sup, s):
        t(c, M, y, ln, f, 8.5)
        y -= 11
    t(c, W - M, H - 52, s["title"], fb, 22, col, "r")
    t(c, W - M, H - 74, f"{s['lbl_no']} {inv['invoice_number']}", fb, 11, black, "r")
    t(c, W - M, H - 90, f"Date : {fmt_date(inv['invoice_date'], s['date'])}", f, 10, black, "r")
    if inv["due_date"]:
        t(c, W - M, H - 104, f"{s['lbl_due']} : {fmt_date(inv['due_date'], s['date'])}", f, 10, black, "r")
    bx, by, bw, bh = 305, H - 215, W - M - 305, 78
    c.setStrokeColor(col)
    c.setLineWidth(0.8)
    c.rect(bx, by, bw, bh)
    t(c, bx + 8, by + bh - 14, s["lbl_client"], fb, 8, col)
    yy = by + bh - 28
    t(c, bx + 8, yy, inv["customer"]["name"], fb, 10)
    yy -= 12
    for ln in customer_lines(cus, s):
        t(c, bx + 8, yy, ln, f, 8.5)
        yy -= 11
    y_end = draw_table(c, inv, s, H - 260, col, white, None, True)
    draw_totals(c, inv, s, y_end - 14)
    draw_stamp(c, inv)
    draw_footer(c, inv, s)


def tpl_modern(c, inv, s):
    f, fb, col = s["font"], s["bold"], s["color"]
    sup, cus = inv["supplier"], inv["customer"]
    c.setFillColor(col)
    c.rect(0, H - 120, W, 120, fill=1, stroke=0)
    t(c, M, H - 58, sup["name"], fb, 19, white)
    t(c, M, H - 76, f"{sup['address']} - {sup['postal_code']} {sup['city']}", f, 9, white)
    t(c, W - M, H - 58, s["title"], fb, 26, white, "r")
    t(c, W - M, H - 80, f"{s['lbl_no']} {inv['invoice_number']}", f, 11, white, "r")
    t(c, W - M, H - 96, fmt_date(inv["invoice_date"], s["date"]), f, 10, white, "r")
    y = H - 150
    t(c, M, y, s["lbl_from"], fb, 8, col)
    y -= 13
    for p in id_parts(sup, s):
        t(c, M, y, p, f, 8.5)
        y -= 11
    x, y = 330, H - 150
    t(c, x, y, s["lbl_client"], fb, 8, col)
    y -= 13
    t(c, x, y, cus["name"], fb, 10)
    y -= 12
    for ln in customer_lines(cus, s):
        t(c, x, y, ln, f, 8.5)
        y -= 11
    if inv["due_date"]:
        t(c, x, y - 4, f"{s['lbl_due']} : {fmt_date(inv['due_date'], s['date'])}", fb, 9)
    y_end = draw_table(c, inv, s, H - 270, col, white, s["zebra"], False)
    draw_totals(c, inv, s, y_end - 14, fill=Color(0.92, 0.94, 0.97))
    draw_stamp(c, inv)
    draw_footer(c, inv, s)


def tpl_minimal(c, inv, s):
    f, fb = s["font"], s["bold"]
    sup, cus = inv["supplier"], inv["customer"]
    y = H - 60
    t(c, M, y, f"{s['title']} {inv['invoice_number']}", fb, 14)
    y -= 18
    t(c, M, y, f"Date: {fmt_date(inv['invoice_date'], s['date'])}", f, 10)
    y -= 13
    if inv["due_date"]:
        t(c, M, y, f"{s['lbl_due']}: {fmt_date(inv['due_date'], s['date'])}", f, 10)
        y -= 13
    y -= 6
    c.setStrokeColor(black)
    c.setLineWidth(0.6)
    c.line(M, y, W - M, y)
    y -= 18
    t(c, M, y, f"{s['lbl_client']}:", fb, 10)
    y -= 13
    t(c, M, y, cus["name"], f, 10)
    y -= 12
    for ln in customer_lines(cus, s):
        t(c, M, y, ln, f, 9)
        y -= 11
    y_end = draw_table(c, inv, s, y - 16, None, black, None, False)
    draw_totals(c, inv, s, y_end - 14)
    draw_stamp(c, inv)
    c.line(M, 112, W - M, 112)
    t(c, M, 98, sup["name"], fb, 9)
    t(c, M, 86, f"{sup['address']}, {sup['postal_code']} {sup['city']}", f, 8)
    parts = id_parts(sup, s)
    t(c, M, 74, " | ".join(parts[:2]), f, 8)
    t(c, M, 63, " | ".join(parts[2:]), f, 8)


TEMPLATES = {"classic": tpl_classic, "modern": tpl_modern, "minimal": tpl_minimal}


def render_pdf(inv, style):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(inv["invoice_number"])
    TEMPLATES[style["template"]](c, inv, style)
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------- scan simulation
def make_scan_profile(rng):
    kind = rng.choices(["clean", "scan", "bad"], [2, 6, 2])[0]
    if kind == "clean":
        p = dict(angle=rng.uniform(-0.3, 0.3), blur=0.0, noise=2.0, contrast=1.0,
                 brightness=1.0, shadow=0.0, quality=90, gray=False)
    elif kind == "scan":
        p = dict(angle=rng.uniform(-1.5, 1.5), blur=rng.uniform(0.3, 0.8), noise=rng.uniform(4, 10),
                 contrast=rng.uniform(0.9, 1.1), brightness=rng.uniform(0.95, 1.05),
                 shadow=rng.uniform(0, 0.1), quality=rng.randint(55, 85), gray=rng.random() < 0.5)
    else:
        p = dict(angle=rng.uniform(-3.5, 3.5), blur=rng.uniform(0.8, 1.4), noise=rng.uniform(10, 18),
                 contrast=rng.uniform(0.75, 0.95), brightness=rng.uniform(0.9, 1.05),
                 shadow=rng.uniform(0.15, 0.3), quality=rng.randint(35, 55), gray=rng.random() < 0.7)
    p = {k: round(v, 2) if isinstance(v, float) else v for k, v in p.items()}
    p["kind"] = kind
    return p


def scanify(img, p, nrng):
    img = img.convert("L") if p["gray"] else img.convert("RGB")
    fill = 255 if img.mode == "L" else (255, 255, 255)
    img = img.rotate(p["angle"], resample=Image.BICUBIC, expand=True, fillcolor=fill)
    if p["blur"] > 0:
        img = img.filter(ImageFilter.GaussianBlur(p["blur"]))
    img = ImageEnhance.Contrast(img).enhance(p["contrast"])
    img = ImageEnhance.Brightness(img).enhance(p["brightness"])
    arr = np.asarray(img).astype(np.float32)
    arr += nrng.normal(0, p["noise"], arr.shape)
    if p["shadow"] > 0:
        grad = np.linspace(1.0, 1.0 - p["shadow"], arr.shape[0], dtype=np.float32)
        arr *= grad[:, None, None] if arr.ndim == 3 else grad[:, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def pdf_to_image(pdf_bytes, dpi):
    pdf = pdfium.PdfDocument(pdf_bytes)
    try:
        return pdf[0].render(scale=dpi / 72).to_pil()
    finally:
        pdf.close()


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=200, help="number of invoices")
    ap.add_argument("--out", default="data/synthetic")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--suppliers", type=int, default=15)
    ap.add_argument("--customers", type=int, default=2)
    ap.add_argument("--start", default="2025-01-01")
    ap.add_argument("--end", default="2026-08-31")
    ap.add_argument("--no-pdf", action="store_true", help="do not keep clean PDFs")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    d0, d1 = date.fromisoformat(a.start), date.fromisoformat(a.end)
    out = Path(a.out)
    for sub in ("images", "labels") + (() if a.no_pdf else ("pdf",)):
        (out / sub).mkdir(parents=True, exist_ok=True)

    suppliers = [make_company(rng, with_catalog=True) for _ in range(a.suppliers)]
    styles = [make_style(rng, ["classic", "modern", "minimal"][i % 3]) for i in range(a.suppliers)]
    customers = [make_company(rng) for _ in range(a.customers)]
    n_test = max(1, round(a.suppliers * 0.3))
    test_ids = set(rng.sample(range(a.suppliers), n_test))

    rows = []
    for i in range(1, a.n + 1):
        k = rng.randrange(a.suppliers)
        sup, style = suppliers[k], styles[k]
        inv = make_invoice(rng, i, sup, rng.choice(customers), style, d0, d1)
        pdf_bytes = render_pdf(inv, style)
        scan = make_scan_profile(rng)
        img = scanify(pdf_to_image(pdf_bytes, a.dpi), scan, np.random.default_rng(rng.getrandbits(32)))

        img.save(out / "images" / f"{inv['id']}.jpg", quality=scan["quality"])
        if not a.no_pdf:
            (out / "pdf" / f"{inv['id']}.pdf").write_bytes(pdf_bytes)
        label = to_label(inv, style, scan)
        (out / "labels" / f"{inv['id']}.json").write_text(json.dumps(label, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append({"id": inv["id"], "split": "test" if k in test_ids else "dev",
                     "supplier": inv["supplier"]["name"], "template": style["template"],
                     "scan_profile": scan["kind"], "invoice_date": label["invoice_date"],
                     "payment_status": inv["payment_status"], "total_ttc": label["total_ttc"]})
        if i % 25 == 0 or i == a.n:
            print(f"{i}/{a.n}")

    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n_dev = sum(r["split"] == "dev" for r in rows)
    print(f"Done: {len(rows)} invoices -> {out} (dev={n_dev}, test={len(rows) - n_dev})")


if __name__ == "__main__":
    main()