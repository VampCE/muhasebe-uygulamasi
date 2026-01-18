import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont



FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")

def ensure_tr_font():
    try:
        pdfmetrics.registerFont(TTFont("TR", FONT_PATH))
        pdfmetrics.registerFont(TTFont("TR-B", FONT_PATH))
    except Exception:
        pass



def df_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Rapor")
    buf.seek(0)
    return buf.getvalue()

def fmt_try_tl(x) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return ""
    # 1,234.56 -> 1.234,56
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} ₺"


def pdf_template_bytes(df: pd.DataFrame, title: str, subtitle: str) -> bytes:
    ensure_tr_font()

    # styles önce tanımlanmalı
    styles = getSampleStyleSheet()
    styles["Title"].fontName = "TR-B"
    styles["Normal"].fontName = "TR"

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24
    )

    story = []
    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(subtitle, styles["Normal"]))
    story.append(Spacer(1, 12))

    safe_df = df.copy().fillna("")

# TL formatını sadece bu kolonlara uygula (kolon isimleri bunlar olmalı)
    money_cols = [c for c in safe_df.columns if c in ["Birim Fiyat", "Tutar"]]

    for c in money_cols:
        safe_df[c] = safe_df[c].apply(fmt_try_tl)

    # Genel toplam (Tutar)
    total_sum = 0.0
    if "Tutar" in df.columns:
        try:
            total_sum = float(pd.to_numeric(df["Tutar"], errors="coerce").fillna(0).sum())
        except Exception:
            total_sum = 0.0

    data = [list(safe_df.columns)] + safe_df.astype(str).values.tolist()

    # Alt toplam satırı ekle
    if "Tutar" in safe_df.columns:
        total_row = [""] * len(safe_df.columns)
        total_row[0] = "GENEL TOPLAM"
        tutar_idx = list(safe_df.columns).index("Tutar")
        total_row[tutar_idx] = fmt_try_tl(total_sum)
        data.append(total_row)

    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        # header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "TR-B"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),

        # body
        ("FONTNAME", (0, 1), (-1, -1), "TR"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),

        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.whitesmoke, colors.HexColor("#e5e7eb")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),

        # toplam satırı (en son satır)
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f3f4f6")),
        ("FONTNAME", (0, -1), (-1, -1), "TR-B"),
    ]))


    story.append(t)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
