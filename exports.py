import os
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import HRFlowable


# ---------------------------------------------------
# PATHS
# ---------------------------------------------------
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")


# ---------------------------------------------------
# FONT
# ---------------------------------------------------
def ensure_tr_font():
    try:
        pdfmetrics.registerFont(TTFont("TR", FONT_PATH))
        pdfmetrics.registerFont(TTFont("TR-B", FONT_PATH))
    except:
        pass


# ---------------------------------------------------
# TL FORMAT
# ---------------------------------------------------
def fmt_try_tl(x):
    try:
        v = float(x)
    except:
        return ""

    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} ₺"


# ---------------------------------------------------
# EXCEL EXPORT
# ---------------------------------------------------
def df_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Rapor")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------
# TABLE BUILDER
# ---------------------------------------------------
def build_table(df: pd.DataFrame, available_width):
    safe_df = df.copy().fillna("")

    money_cols = [c for c in safe_df.columns if c in ["Birim Fiyat", "Tutar"]]
    for c in money_cols:
        safe_df[c] = safe_df[c].apply(fmt_try_tl)

    data = [list(safe_df.columns)] + safe_df.astype(str).values.tolist()

    # ---------------------------------------
    # AKILLI WIDTH DAĞILIMI
    # ---------------------------------------
    col_widths = []

    for col in safe_df.columns:
        if col in ["Tarih"]:
            col_widths.append(available_width * 0.12)
        elif col in ["Makine"]:
            col_widths.append(available_width * 0.14)
        elif col in ["İş Türü", "İş"]:
            col_widths.append(available_width * 0.32)
        elif col in ["Miktar"]:
            col_widths.append(available_width * 0.08)
        elif col in ["Birim"]:
            col_widths.append(available_width * 0.10)
        elif col in ["Birim Fiyat"]:
            col_widths.append(available_width * 0.12)
        elif col in ["Tutar"]:
            col_widths.append(available_width * 0.12)
        else:
            col_widths.append(available_width * 0.10)

    table = Table(data, colWidths=col_widths, repeatRows=1)

    
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f3e46")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "TR-B"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),

        ("FONTNAME", (0, 1), (-1, -1), "TR"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),

        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    if "Tutar" in safe_df.columns:
        col = safe_df.columns.get_loc("Tutar")
        style.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))

    if "Birim Fiyat" in safe_df.columns:
        col = safe_df.columns.get_loc("Birim Fiyat")
        style.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))

    table.setStyle(TableStyle(style))
    return table


# ---------------------------------------------------
# PDF EXPORT
# ---------------------------------------------------
def pdf_template_bytes(df: pd.DataFrame,
                       title: str,
                       subtitle: str,
                       group_by_machine=False,
                       include_kdv=False,
                       kdv_rate=20,
                       avans=0) -> bytes:

    ensure_tr_font()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=40,
        bottomMargin=40
    )

    width = A4[0] - 60

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TitleStyle",
        parent=styles["Normal"],
        fontName="TR-B",
        fontSize=16,
    ))

    styles["Normal"].fontName = "TR"
    styles["Normal"].fontSize = 9

    story = []

    # -------------------------------------------------
    # HEADER (Logo sağda)
    # -------------------------------------------------
    header_data = []

    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=130, height=80)
        header_data = [[Paragraph(title, styles["TitleStyle"]), logo]]
    else:
        header_data = [[Paragraph(title, styles["TitleStyle"]), ""]]

    header_table = Table(
        header_data,
        colWidths=[width * 0.75, width * 0.25]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(subtitle, styles["Normal"]))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.grey))
    story.append(Spacer(1, 12))

    # -------------------------------------------------
    # TABLO
    # -------------------------------------------------
    total_all = 0.0
    if "Tutar" in df.columns:
        total_all = float(pd.to_numeric(df["Tutar"], errors="coerce").fillna(0).sum())
    # AVANS DÜŞ
    total_after_avans = total_all - avans
    if total_after_avans < 0:
        total_after_avans = 0

    if group_by_machine and "Makine" in df.columns:
        for machine, gdf in df.groupby("Makine"):
            story.append(Paragraph(f"<b>Makine:</b> {machine}", styles["Normal"]))
            story.append(Spacer(1, 6))
            story.append(build_table(gdf, width))
            story.append(Spacer(1, 12))
    else:
        story.append(build_table(df, width))
        story.append(Spacer(1, 12))

    # -------------------------------------------------
    # TOPLAM BLOĞU
    # -------------------------------------------------
    if include_kdv:
        kdv_amount = total_after_avans * (kdv_rate / 100)
        grand_total = total_after_avans + kdv_amount

        summary_data = [
            ["Ara Toplam:", fmt_try_tl(total_all)],
        ]

        if avans > 0:
            summary_data.append(["Avans:", f"- {fmt_try_tl(avans)}"])

        summary_data.extend([
            [f"KDV (%{kdv_rate}):", fmt_try_tl(kdv_amount)],
            ["Genel Toplam:", fmt_try_tl(grand_total)],
        ])

    else:
        summary_data = [
            ["Ara Toplam:", fmt_try_tl(total_all)],
        ]

        if avans > 0:
            summary_data.append(["Avans:", f"- {fmt_try_tl(avans)}"])

        summary_data.append(
            ["Genel Toplam:", fmt_try_tl(total_after_avans)]
        )

    summary_table = Table(summary_data, colWidths=[width * 0.7, width * 0.3])

    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "TR-B"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, colors.black),
    ]))

    story.append(summary_table)

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

