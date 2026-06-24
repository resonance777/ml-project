"""
generate_pdf.py
===============
Generates the source historical document (a 10+ page PDF about the Roman Empire)
that the RAG pipeline will ingest.

Design decisions
----------------
* We use ReportLab's high-level "Platypus" framework (SimpleDocTemplate + flowables)
  rather than drawing on a canvas by hand. This automatically handles page breaks,
  paragraph wrapping, and consistent typography across many pages.
* Each section gets a heading styled distinctly from body text. Clear, consistent
  headings matter for the *downstream* RAG step: they become natural section
  boundaries that our chunker can respect.
* Justified body text and generous spacing keep the document readable and push it
  comfortably past the 10-page minimum required by the assignment.

Run:
    python src/generate_pdf.py
Output:
    data/roman_empire.pdf
"""

from __future__ import annotations

import os

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from content import AUTHOR, SECTIONS, SUBTITLE, TITLE

# Resolve paths relative to this file so the script works from any CWD.
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "roman_empire.pdf")


def _build_styles():
    """Create the paragraph styles used throughout the document."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Title"],
            fontSize=24,
            leading=30,
            spaceAfter=18,
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocSubtitle",
            parent=styles["Normal"],
            fontSize=12,
            leading=16,
            textColor="#555555",
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            spaceBefore=18,
            spaceAfter=10,
            textColor="#6b1f1f",  # a muted Roman red
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyJustified",
            parent=styles["BodyText"],
            fontSize=11,
            leading=17,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
        )
    )
    return styles


def _footer(canvas, doc):
    """Draw a simple page number footer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor("#888888")
    canvas.drawCentredString(A4[0] / 2.0, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(output_path: str = OUTPUT_PATH) -> str:
    """Render the structured content in content.py into a PDF file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = _build_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        title=TITLE,
        author=AUTHOR,
    )

    story = []

    # --- Title page ---
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph(TITLE, styles["DocTitle"]))
    story.append(Paragraph(SUBTITLE, styles["DocSubtitle"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(AUTHOR, styles["DocSubtitle"]))
    story.append(PageBreak())

    # --- Body sections ---
    for title, paragraphs in SECTIONS:
        story.append(Paragraph(title, styles["SectionHeading"]))
        for para in paragraphs:
            story.append(Paragraph(para, styles["BodyJustified"]))
        story.append(Spacer(1, 0.3 * cm))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output_path


if __name__ == "__main__":
    path = build_pdf()
    size_kb = os.path.getsize(path) / 1024
    print(f"[generate_pdf] PDF written to: {path} ({size_kb:.1f} KB)")
