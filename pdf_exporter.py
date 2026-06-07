# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 12:21:49 2026

@author: Admin
"""

# pdf_exporter.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io
import re
from datetime import datetime


def _clean_markdown(text: str) -> str:
    """Strip markdown symbols that don't render in PDF."""
    text = re.sub(r"#{1,3}\s*", "", text)       # remove ## headings
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text) # remove **bold**
    text = re.sub(r"\*(.*?)\*", r"\1", text)      # remove *italic*
    text = re.sub(r"`(.*?)`", r"\1", text)        # remove `code`
    return text.strip()


def generate_pdf(
    ticker: str,
    report: str,
    technical: dict,
    news: list
) -> bytes:
    """
    Build a professional A4 PDF report and return it as bytes
    so Streamlit can offer it as a download.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # ── Styles ─────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#16213e"),
        spaceBefore=14,
        spaceAfter=4,
        borderPad=2,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#222222"),
        leading=15,
        spaceAfter=6,
    )
    news_style = ParagraphStyle(
        "NewsStyle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#333333"),
        leading=13,
        spaceAfter=3,
    )
    caption_style = ParagraphStyle(
        "CaptionStyle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    story = []

    # ── Header ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"AI Financial Analysis Report", title_style))
    story.append(Paragraph(f"Ticker: {ticker.upper()}", subtitle_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}",
        caption_style
    ))
    story.append(HRFlowable(
        width="100%", thickness=2,
        color=colors.HexColor("#16213e"), spaceAfter=12
    ))

    # ── Technical Snapshot Table ────────────────────────────────────────
    if technical and "error" not in technical:
        story.append(Paragraph("Technical Snapshot", section_style))
        story.append(Spacer(1, 0.2 * cm))

        table_data = [
            ["Metric", "Value"],
            ["Current Price", f"${technical.get('Current Price', 'N/A')}"],
            ["MA20",          f"${technical.get('MA20', 'N/A')}"],
            ["MA50",          f"${technical.get('MA50', 'N/A')}"],
            ["RSI (14)",      str(technical.get("RSI (14)", "N/A"))],
            ["Trend Signal",  technical.get("Trend Signal", "N/A")],
            ["RSI Signal",    technical.get("RSI Signal",  "N/A")],
        ]

        table = Table(table_data, colWidths=[5 * cm, 11 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#f0f4ff"), colors.white]),
            ("FONTSIZE",     (0, 1), (-1, -1), 9),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.4 * cm))

    # ── AI Report Sections ──────────────────────────────────────────────
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#cccccc"), spaceAfter=6
    ))
    story.append(Paragraph("AI-Generated Analysis", section_style))
    story.append(Spacer(1, 0.2 * cm))

    # Split report by ## headings and render each as section
    sections = re.split(r"(##\s+.+)", report)
    for chunk in sections:
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk.startswith("##"):
            heading = _clean_markdown(chunk)
            story.append(Paragraph(heading, section_style))
        else:
            # Split into paragraphs on double newlines
            paragraphs = chunk.split("\n")
            for para in paragraphs:
                para = _clean_markdown(para).strip()
                if para:
                    story.append(Paragraph(para, body_style))

    # ── News Headlines ──────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#cccccc"), spaceAfter=6
    ))
    story.append(Paragraph("Recent News Headlines", section_style))
    story.append(Spacer(1, 0.2 * cm))

    for i, article in enumerate(news, 1):
        title = article.get("title", "N/A")
        pub   = article.get("pubDate", "")
        link  = article.get("link", "#")
        story.append(Paragraph(
            f"<b>{i}. {title}</b>",
            news_style
        ))
        story.append(Paragraph(
            f"{pub} — {link}",
            caption_style
        ))

    # ── Footer ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#16213e"), spaceAfter=6
    ))
    story.append(Paragraph(
        "This report was generated by an AI Financial Analyst Agent powered by "
        "Groq Llama 3.3 and Alpha Vantage. It is for informational purposes only "
        "and does not constitute financial advice. Always consult a qualified "
        "financial advisor before making investment decisions.",
        caption_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()