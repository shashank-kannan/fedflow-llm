"""Build study_guide/FedFlow_Study_Guide.pdf from the Markdown source (a small, fixed Markdown subset).
Needs reportlab:  python3 study_guide/build_pdf.py study_guide/FedFlow_Study_Guide.md study_guide/FedFlow_Study_Guide.pdf"""
import re
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

INK = colors.HexColor("#1F2A36")
CALLOUT_FILL = {"In one line": "#DCE9F5", "Watch out": "#FCE8C8", "If pushed": "#DDEFD9"}

BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=10.5, leading=15, spaceAfter=6, textColor=INK)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=9, leading=12, spaceAfter=0)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Helvetica-Bold", fontSize=20, leading=24, spaceAfter=4)
H1 = ParagraphStyle("h1", parent=BODY, fontName="Helvetica-Bold", fontSize=15, leading=19, spaceBefore=4, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=8, spaceAfter=4)
LIST = ParagraphStyle("list", parent=BODY, leftIndent=16, bulletIndent=2, spaceAfter=3)
MONO = ParagraphStyle("mono", fontName="Courier", fontSize=8.3, leading=11, textColor=INK)


def inline(text):
    """Markdown **bold** and `code` -> reportlab markup, with everything else escaped."""
    out = []
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if part.startswith("**") and part.endswith("**"):
            out.append(f"<b>{escape(part[2:-2])}</b>")
        elif part.startswith("`") and part.endswith("`"):
            out.append(f'<font face="Courier">{escape(part[1:-1])}</font>')
        else:
            out.append(escape(part))
    return "".join(out)


def boxed(flowable, fill, width):
    t = Table([[flowable]], colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fill)),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def md_table(rows, width):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    data = [cells[0]] + cells[2:]
    head = ParagraphStyle("th", parent=SMALL, fontName="Helvetica-Bold")
    body = [[Paragraph(inline(c), head if i == 0 else SMALL) for c in row] for i, row in enumerate(data)]
    t = Table(body, colWidths=[width / len(data[0])] * len(data[0]), repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C2CC")),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7ECF2")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, f"FedFlow-LLM study guide  |  page {doc.page}")
    canvas.restoreState()


def main(src, out):
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm, title="FedFlow-LLM Study Guide")
    width = A4[0] - 4.4 * cm
    story, lines, i, first = [], open(src, encoding="utf-8").read().split("\n"), 0, True
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            block = []
            i += 1
            while not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            story += [boxed(Preformatted("\n".join(block), MONO), "#F3F4F6", width), Spacer(1, 6)]
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            story += [md_table(rows, width), Spacer(1, 8)]
            continue
        m = re.match(r"^> \*\*([^*]+?):\*\*\s*(.*)$", line)
        if m:
            p = Paragraph(f"<b>{escape(m.group(1))}:</b> {inline(m.group(2))}", ParagraphStyle("c", parent=BODY, spaceAfter=0))
            story += [boxed(p, CALLOUT_FILL.get(m.group(1), "#EEEEEE"), width), Spacer(1, 8)]
            i += 1
            continue
        if line.startswith("# "):
            if first:
                story.append(Paragraph(inline(line[2:]), TITLE))
                first = False
            else:
                # Sections flow on; only the cheat sheet starts a fresh page so it can be printed alone.
                story += ([PageBreak()] if "Cheat sheet" in line else [Spacer(1, 6)]) + [Paragraph(inline(line[2:]), H1)]
            i += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), H2))
            i += 1
            continue
        m = re.match(r"^(\d+)\. (.*)$", line)
        if m:
            story.append(Paragraph(inline(m.group(2)), LIST, bulletText=f"{m.group(1)}."))
            i += 1
            continue
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|>|\||\d+\. |```)", lines[i]):
            buf.append(lines[i])
            i += 1
        story.append(Paragraph(inline(" ".join(b.strip() for b in buf)), BODY))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
