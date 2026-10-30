"""Build study_guide/FedFlow_Study_Guide.docx from the Markdown source (a small, fixed Markdown subset)."""
import re
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SRC, OUT = sys.argv[1], sys.argv[2]
FONT, MONO = "Calibri", "Consolas"
CALLOUT_FILL = {"In one line": "DCE9F5", "Watch out": "FCE8C8", "If pushed": "DDEFD9"}
INK = RGBColor(0x1F, 0x2A, 0x36)


def set_cell_fill(cell, hex_fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def add_field(paragraph, instr):
    """A Word field (PAGE, NUMPAGES, TOC ...) in its own runs."""
    for kind, text in (("begin", None), (None, instr), ("separate", None), (None, ""), ("end", None)):
        run = paragraph.add_run()
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
            run._r.append(el)
        elif text is not None and text != "":
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
            run._r.append(el)


def add_inline(paragraph, text, size=None, bold_all=False):
    """**bold** and `code` inside a line."""
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = MONO
        else:
            run = paragraph.add_run(part)
            run.bold = bold_all or None
        if size:
            run.font.size = Pt(size)


def tight(paragraph, size=None):
    pf = paragraph.paragraph_format
    pf.space_after = Pt(2)
    pf.space_before = Pt(0)
    pf.line_spacing = 1.0
    if size:
        for r in paragraph.runs:
            r.font.size = Pt(size)


def setup(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)        # A4
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Cm(2.5))
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = FONT, Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(8)
    for name, size, before in (("Title", 26, 0), ("Heading 1", 20, 0), ("Heading 2", 15, 10), ("Heading 3", 12.5, 8)):
        st = doc.styles[name]
        st.font.name, st.font.size, st.font.bold, st.font.color.rgb = FONT, Pt(size), True, INK
        st.element.rPr.rFonts.set(qn("w:asciiTheme"), "") if False else None
        rfonts = st.element.rPr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            st.element.rPr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rfonts.set(qn(attr), FONT)
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rfonts.get(qn(attr)) is not None:
                del rfonts.attrib[qn(attr)]
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.line_spacing = 1.15
        st.paragraph_format.keep_with_next = True
    # Footer: "Page X of Y" on every page.
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.add_run("Page ")
    add_field(fp, "PAGE")
    fp.add_run(" of ")
    add_field(fp, "NUMPAGES")
    # Ask Word to refresh fields (table of contents, page count) when the file is opened.
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)


def callout(doc, label, text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    set_cell_fill(cell, CALLOUT_FILL.get(label, "EEEEEE"))
    p = cell.paragraphs[0]
    run = p.add_run(f"{label}: ")
    run.bold = True
    add_inline(p, text)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.3
    doc.add_paragraph().paragraph_format.space_after = Pt(0)   # small gap after the box


def md_table(doc, rows, small):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], [r for r in cells[2:]]
    table = doc.add_table(rows=1 + len(body), cols=len(header))
    table.style = "Table Grid"
    size = 9.5 if small else 10.5
    for j, h in enumerate(header):
        c = table.rows[0].cells[j]
        set_cell_fill(c, "E7ECF2")
        add_inline(c.paragraphs[0], h, size=size, bold_all=True)
        tight(c.paragraphs[0])
    for i, r in enumerate(body, start=1):
        for j, v in enumerate(r[: len(header)]):
            add_inline(table.rows[i].cells[j].paragraphs[0], v, size=size)
            tight(table.rows[i].cells[j].paragraphs[0])
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def code_block(doc, lines):
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    set_cell_fill(cell, "F3F4F6")
    p = cell.paragraphs[0]
    for k, line in enumerate(lines):
        run = p.add_run(line)
        run.font.name, run.font.size = MONO, Pt(9)
        if k < len(lines) - 1:
            run.add_break()
    tight(p)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def main():
    doc = Document()
    setup(doc)
    lines = open(SRC, encoding="utf-8").read().split("\n")
    i, first_h1, part = 0, True, ""
    while i < len(lines):
        line = lines[i]
        small = part.startswith("Part 12")            # cheat sheet: compact tables so it fits one page
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            block = []
            i += 1
            while not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            code_block(doc, block)
            i += 1
            continue
        if line.strip() == "[[TOC]]":
            doc.add_heading("Contents", level=2)
            p = doc.add_paragraph()
            add_field(p, 'TOC \\o "1-2" \\h \\z \\u')
            p.add_run("(Word fills in the contents when the file is opened; if it does not, right-click here and choose Update Field.)").italic = True
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            md_table(doc, rows, small)
            continue
        m = re.match(r"^> \*\*([^*]+?):\*\*\s*(.*)$", line)
        if m:
            callout(doc, m.group(1), m.group(2))
            i += 1
            continue
        if line.startswith("# "):
            text = line[2:].strip()
            if first_h1:
                doc.add_heading(text, level=0)
                first_h1 = False
            else:
                h = doc.add_heading(text, level=1)
                h.paragraph_format.page_break_before = True     # every Part starts on a new page
                part = text
            i += 1
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
            i += 1
            continue
        if line.startswith("## "):
            h = doc.add_heading(line[3:].strip(), level=2)
            if small:
                h.paragraph_format.space_before = Pt(4)
            i += 1
            continue
        if line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, line[2:])
            i += 1
            continue
        m = re.match(r"^(\d+)\. (.*)$", line)
        if m:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.first_line_indent = Cm(-0.6)
            add_inline(p, f"{m.group(1)}.  {m.group(2)}")
            i += 1
            continue
        # Ordinary paragraph: join wrapped lines until a blank line.
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|>|\||- |\d+\. |```)", lines[i]):
            buf.append(lines[i])
            i += 1
        text = " ".join(b.strip() for b in buf)
        p = doc.add_paragraph()
        if text.startswith("Source:"):
            run = p.add_run("Source: ")
            run.bold = True
            add_inline(p, text[len("Source:"):].strip())
        else:
            add_inline(p, text)
    doc.core_properties.title = "FedFlow-LLM Study Guide"
    doc.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
