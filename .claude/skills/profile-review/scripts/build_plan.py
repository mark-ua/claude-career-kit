#!/usr/bin/env python3
"""Build a LinkedIn update plan (PDF, optionally DOCX) from a plan JSON file.

The plan is written for another person: what to change on their profile, where to
find it in LinkedIn, and ready-to-paste texts. Every "paste" block is counted and
checked against its field limit, so a text LinkedIn would cut off never reaches the
person. The DOCX copy exists because PDF viewers insert line breaks when text is
copied from them; texts are copied from the DOCX.

Usage (run with the kit's venv interpreter):
    python build_plan.py plan.json out.pdf [--docx out.docx] [--preview DIR]
                         [--page-size a4|letter] [--font REGULAR.ttf BOLD.ttf]

JSON schema (../assets/plan.example.json is a complete example):
{
  "meta": {"page_size": "a4",                                   # or "letter"
           "labels": {"where": "Where", "now": "Now",           # optional, in the
                      "chars": "characters", "page": "Page"}},  # plan's language
  "title": "LinkedIn: profile update plan",
  "person": "First Last",
  "subtitle": "linkedin.com/in/slug · profile as of 20 Nov 2026",
  "footer": "LinkedIn update plan · First Last",                # optional
  "intro": ["paragraph", ...],
  "sections": [
    {"heading": "2. Top card",
     "blocks": [
       {"type": "text", "text": "Plain text; **bold** works here."},
       {"type": "subheading", "text": "2.1 Headline"},
       {"type": "where", "text": "Pencil in the top card → Edit intro → Headline"},
       {"type": "now", "text": "the current text, verbatim"},
       {"type": "paste", "label": "Recommended", "text": "verbatim text\\nwith line breaks",
        "limit": 220},
       {"type": "bullets", "items": ["...", "..."]},
       {"type": "table", "columns": ["#", "Change", "Why"], "rows": [["1", "...", "..."]],
        "widths": [1, 6, 8]},                                   # optional relative widths
       {"type": "note", "text": "smaller, muted remark"}
     ]}
  ]
}
"now" and "paste" texts are printed verbatim (no **bold**), line breaks kept.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

for _stream in (sys.stdout, sys.stderr):          # Windows consoles are often cp1252/cp866
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass

RESUME_SCRIPTS = Path(__file__).resolve().parents[2] / "resume-tailor" / "scripts"
sys.path.insert(0, str(RESUME_SCRIPTS))
try:                                              # same embedded fonts and text cleanup as the resume
    from build_resume import clean, find_fonts
except ImportError:
    sys.exit(f"error: {RESUME_SCRIPTS / 'build_resume.py'} not found - profile-review needs the "
             "resume-tailor skill next to it")

LABELS = {"where": "Where", "now": "Now", "chars": "characters", "page": "Page"}
FIELDS = {"text": "text", "subheading": "text", "where": "text", "now": "text", "paste": "text",
          "note": "text", "bullets": "items", "table": "rows"}
INK, MUTED, RULE = "#1a1a1a", "#555555", "#bbbbbb"
PASTE_BG, PASTE_EDGE, NOW_BG, HEAD_BG = "#eaf2fb", "#6b9bd1", "#f1f1f1", "#eeeeee"
PLACEHOLDER = re.compile(r"\[[^\[\]\n]{1,80}\]")
BOLD = re.compile(r"\*\*(.+?)\*\*")


def fail(message):
    sys.exit(f"error: {message}")


def need_text(value, where):
    if not isinstance(value, str) or not value.strip():
        fail(f"{where} must be non-empty text")


def verbatim(text):
    """Normalize line ends and trailing spaces; this is exactly what the person will paste."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").strip("\n").split("\n")
    return "\n".join(line.rstrip() for line in lines)


def validate(data):
    if not isinstance(data, dict):
        fail("the plan file must contain one JSON object")
    need_text(data.get("title"), '"title"')
    need_text(data.get("person"), '"person"')
    data["meta"] = data.get("meta") or {}
    if not isinstance(data["meta"], dict):
        fail('"meta" must be an object')
    labels = data["meta"].get("labels") or {}
    if not isinstance(labels, dict) or set(labels) - set(LABELS):
        fail(f'"meta.labels" may only contain: {", ".join(LABELS)}')
    for key in ("subtitle", "footer"):
        data[key] = data.get(key) or ""
        if not isinstance(data[key], str):
            fail(f'"{key}" must be text')
    intro = data.get("intro") or []
    intro = [intro] if isinstance(intro, str) else intro
    if not isinstance(intro, list) or not all(isinstance(p, str) for p in intro):
        fail('"intro" must be a list of paragraphs')
    data["intro"] = intro
    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        fail('"sections" must be a non-empty list')
    for i, sec in enumerate(sections, 1):
        where = f"sections[{i}]"
        if not isinstance(sec, dict):
            fail(f"{where} must be an object")
        need_text(sec.get("heading"), f'{where}.heading')
        sec["blocks"] = sec.get("blocks") or []
        if not isinstance(sec["blocks"], list):
            fail(f"{where}.blocks must be a list")
        for j, block in enumerate(sec["blocks"], 1):
            w = f"{where}.blocks[{j}]"
            if not isinstance(block, dict) or block.get("type") not in FIELDS:
                fail(f'{w}: "type" must be one of {", ".join(FIELDS)}')
            kind = block["type"]
            if kind == "bullets":
                items = block.get("items")
                if not isinstance(items, list) or not items or not all(isinstance(x, str) for x in items):
                    fail(f'{w}: "items" must be a non-empty list of texts')
            elif kind == "table":
                cols, rows = block.get("columns"), block.get("rows")
                if not isinstance(cols, list) or not cols or not all(isinstance(c, str) for c in cols):
                    fail(f'{w}: "columns" must be a non-empty list of texts')
                if not isinstance(rows, list) or not rows:
                    fail(f'{w}: "rows" must be a non-empty list')
                for k, row in enumerate(rows, 1):
                    if not isinstance(row, list) or len(row) != len(cols):
                        fail(f"{w}: row {k} must be a list of {len(cols)} cells")
                block["rows"] = [["" if c is None else str(c) for c in row] for row in rows]
                widths = block.get("widths")
                if widths is not None and not (
                        isinstance(widths, list) and len(widths) == len(cols)
                        and all(isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0
                                for x in widths)):
                    fail(f'{w}: "widths" must be {len(cols)} positive numbers')
            else:
                need_text(block.get("text"), f'{w}.text')
            if kind in ("paste", "now"):
                block["text"] = verbatim(block["text"])
            if kind == "paste":
                limit = block.get("limit")
                if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0):
                    fail(f'{w}: "limit" must be a positive whole number')
                if block.get("label") is not None and not isinstance(block["label"], str):
                    fail(f'{w}: "label" must be text')
    return data


def paste_blocks(data):
    for sec in data["sections"]:
        for block in sec["blocks"]:
            if block["type"] == "paste":
                yield sec, block


def segments(text):
    """Split **bold** markup into (text, is_bold) pieces."""
    out, pos = [], 0
    for m in BOLD.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], False))
        out.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], False))
    return out


def count_label(block, labels):
    n, limit = len(block["text"]), block.get("limit")
    count = f"{n:,} / {limit:,} {labels['chars']}" if limit else f"{n:,} {labels['chars']}"
    return f"{block['label']} · {count}" if block.get("label") else count


# ---------------------------------------------------------------- PDF

def build_pdf(data, out_path, page_size, fonts):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (HRFlowable, KeepTogether, ListFlowable, ListItem, Paragraph,
                                    SimpleDocTemplate, Table, TableStyle)

    family, reg_path, bold_path = fonts
    regular, bold = family, f"{family}-Bold"
    pdfmetrics.registerFont(TTFont(regular, str(reg_path)))
    pdfmetrics.registerFont(TTFont(bold, str(bold_path)))
    pdfmetrics.registerFontFamily(family, normal=regular, bold=bold)
    labels = {**LABELS, **data["meta"].get("labels", {})}
    page = A4 if page_size == "a4" else letter
    margin = 0.7 * inch
    width = page[0] - 2 * margin

    def style(name, font=regular, size=9.8, leading=13.6, color=INK, **kw):
        return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                              textColor=colors.HexColor(color), **kw)

    S = {"title": style("title", bold, 17, 21),
         "subtitle": style("subtitle", size=9.5, leading=13, color=MUTED, spaceAfter=8),
         "body": style("body", spaceAfter=4),
         "h": style("h", bold, 13, 16, spaceBefore=12, spaceAfter=3),
         "sub": style("sub", bold, 10.8, 14, spaceBefore=9, spaceAfter=2),
         "where": style("where", size=9.4, leading=12.6, color=MUTED, spaceAfter=3),
         "label": style("label", bold, 9.2, 12, spaceBefore=4, spaceAfter=2),
         "box": style("box", size=9.6, leading=13),
         "note": style("note", size=9, leading=12.2, color=MUTED, spaceBefore=2, spaceAfter=4),
         "cell": style("cell", size=9, leading=12),
         "cellh": style("cellh", bold, 9, 12),
         "bullet": style("bullet", size=9.6, leading=13)}

    def markup(text):
        return "".join(f"<b>{escape(t)}</b>" if b else escape(t) for t, b in segments(text))

    def box(text, background, edge=None, head_lines=3):
        """A shaded box as [first lines, rest]: one row per line, so a long text can continue
        on the next page, and the first part can be kept with the label above it."""
        rows = [[Paragraph(escape(line) if line.strip() else "&nbsp;", S["box"])]
                for line in text.split("\n")]
        parts = [rows[:head_lines], rows[head_lines:]] if len(rows) > head_lines else [rows]
        out = []
        for i, part in enumerate(parts):
            first, last = i == 0, i == len(parts) - 1
            commands = [("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(background)),
                        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                        ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]
            if first:
                commands.append(("TOPPADDING", (0, 0), (-1, 0), 6))
            if last:
                commands.append(("BOTTOMPADDING", (0, -1), (-1, -1), 6))
            if edge:
                commands.append(("LINEBEFORE", (0, 0), (0, -1), 2.2, colors.HexColor(edge)))
            table = Table(part, colWidths=[width])
            table.setStyle(TableStyle(commands))
            table.spaceAfter = 6 if last else 0
            out.append(table)
        return out

    def grid(block):
        cols = block["columns"]
        weights = block.get("widths") or [1] * len(cols)
        col_widths = [width * w / sum(weights) for w in weights]
        rows = [[Paragraph(markup(c), S["cellh"]) for c in cols]]
        rows += [[Paragraph(markup(c), S["cell"]) for c in row] for row in block["rows"]]
        table = Table(rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(RULE)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(HEAD_BG)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        table.spaceBefore, table.spaceAfter = 2, 6
        return table

    def render(block):
        """Return (lead-in, body): the lead-in (a heading, "where", a box label) must stay on
        the same page as the first body flowable."""
        kind = block["type"]
        if kind == "text":
            return [], [Paragraph(markup(block["text"]), S["body"])]
        if kind == "subheading":
            return [Paragraph(markup(block["text"]), S["sub"])], []
        if kind == "where":
            return [Paragraph(f"<b>{escape(labels['where'])}:</b> {markup(block['text'])}",
                              S["where"])], []
        if kind == "now":
            return [Paragraph(escape(labels["now"]), S["label"])], box(block["text"], NOW_BG)
        if kind == "paste":
            return ([Paragraph(escape(count_label(block, labels)), S["label"])],
                    box(block["text"], PASTE_BG, PASTE_EDGE))
        if kind == "bullets":
            return [], [ListFlowable([ListItem(Paragraph(markup(t), S["bullet"]), leftIndent=12,
                                               value="•") for t in block["items"]],
                                     bulletType="bullet", start="•", leftIndent=12,
                                     bulletFontName=regular, bulletFontSize=9, spaceAfter=4)]
        if kind == "table":
            return [], [grid(block)]
        return [], [Paragraph(markup(block["text"]), S["note"])]

    story = [Paragraph(escape(data["title"]), S["title"]),
             Paragraph(escape(" · ".join(p for p in (data["person"], data["subtitle"]) if p)),
                       S["subtitle"])]
    story += [Paragraph(markup(p), S["body"]) for p in data["intro"]]
    for sec in data["sections"]:
        pending = [Paragraph(markup(sec["heading"]), S["h"]),
                   HRFlowable(width="100%", thickness=0.6, color=colors.HexColor(MUTED),
                              spaceBefore=0, spaceAfter=4)]
        for block in sec["blocks"]:
            lead, body = render(block)
            pending += lead
            if body:                              # headings and labels never end a page alone
                story.append(KeepTogether(pending + body[:1]))
                story += body[1:]
                pending = []
        story += pending

    footer = data["footer"] or f'{data["title"]} · {data["person"]}'

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont(regular, 8)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(margin, 0.45 * inch, footer)
        canvas.drawRightString(page[0] - margin, 0.45 * inch, f"{labels['page']} {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(out_path), pagesize=page, leftMargin=margin, rightMargin=margin,
                            topMargin=0.6 * inch, bottomMargin=0.75 * inch,
                            title=f'{data["title"]} - {data["person"]}', subject=data["title"],
                            author="", creator="Career Kit")
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


# ---------------------------------------------------------------- DOCX

def build_docx(data, out_path, page_size):
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Mm, Pt, RGBColor

    labels = {**LABELS, **data["meta"].get("labels", {})}
    doc = Document()
    sec = doc.sections[0]
    if page_size == "a4":
        sec.page_width, sec.page_height = Mm(210), Mm(297)
    else:
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(0.7)
    sec.top_margin, sec.bottom_margin = Inches(0.6), Inches(0.7)
    usable = sec.page_width - sec.left_margin - sec.right_margin
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(10)
    normal.paragraph_format.space_after = Pt(3)

    def add_runs(par, text, size=None, color=None, all_bold=False, plain=False):
        for piece, is_bold in ([(text, False)] if plain else segments(text)):
            run = par.add_run(piece)
            run.bold = is_bold or all_bold
            run.font.name = "Arial"
            if size:
                run.font.size = Pt(size)
            if color:
                run.font.color.rgb = RGBColor.from_string(color.lstrip("#").upper())
        return par

    def para(text, size=None, color=None, bold=False, before=0, after=3, plain=False, style=None):
        par = doc.add_paragraph(style=style)
        par.paragraph_format.space_before, par.paragraph_format.space_after = Pt(before), Pt(after)
        return add_runs(par, text, size, color, bold, plain)

    def shade(cell, fill):
        props = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fill.lstrip("#").upper())
        props.append(shd)

    def spacer():                                 # also keeps two tables from merging in Word
        para("", after=2)

    def box(text, fill):
        table = doc.add_table(rows=1, cols=1)
        table.style = "Table Grid"
        cell = table.cell(0, 0)
        shade(cell, fill)
        for i, line in enumerate(text.split("\n")):
            par = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            par.paragraph_format.space_after = Pt(0)
            add_runs(par, line, size=10, plain=True)
        spacer()

    para(data["title"], size=17, bold=True, after=2)
    para(" · ".join(p for p in (data["person"], data["subtitle"]) if p), size=9.5, color=MUTED, after=8)
    for p in data["intro"]:
        para(p)
    for section in data["sections"]:
        para(section["heading"], size=13, bold=True, before=12, after=4)
        for block in section["blocks"]:
            kind = block["type"]
            if kind == "text":
                para(block["text"])
            elif kind == "subheading":
                para(block["text"], size=10.8, bold=True, before=8, after=2)
            elif kind == "where":
                par = para(f"{labels['where']}: ", size=9.5, color=MUTED, bold=True, plain=True)
                add_runs(par, block["text"], size=9.5, color=MUTED)
            elif kind == "now":
                para(labels["now"], size=9.5, bold=True, before=3, after=2, plain=True)
                box(block["text"], NOW_BG)
            elif kind == "paste":
                para(count_label(block, labels), size=9.5, bold=True, before=3, after=2, plain=True)
                box(block["text"], PASTE_BG)
            elif kind == "bullets":
                for item in block["items"]:
                    para(item, style="List Bullet", after=1)
            elif kind == "table":
                cols, rows = block["columns"], block["rows"]
                table = doc.add_table(rows=1 + len(rows), cols=len(cols))
                table.style = "Table Grid"
                weights = block.get("widths") or [1] * len(cols)
                for r, values in enumerate([cols] + rows):
                    for c, value in enumerate(values):
                        cell = table.cell(r, c)
                        cell.width = int(usable * weights[c] / sum(weights))
                        add_runs(cell.paragraphs[0], value, size=9, all_bold=(r == 0))
                        if r == 0:
                            shade(cell, HEAD_BG)
                spacer()
            else:
                para(block["text"], size=9, color=MUTED)

    footer = sec.footer.paragraphs[0]
    add_runs(footer, data["footer"] or f'{data["title"]} · {data["person"]}', size=8, color=MUTED, plain=True)
    props = doc.core_properties
    props.title, props.author, props.comments = f'{data["title"]} - {data["person"]}', "", ""
    doc.save(str(out_path))


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("plan_json")
    ap.add_argument("out_pdf")
    ap.add_argument("--docx", help="also write a DOCX copy - the one to copy texts from")
    ap.add_argument("--preview", help="directory for PNG page previews")
    ap.add_argument("--page-size", help="a4 (default) or letter")
    ap.add_argument("--font", nargs=2, metavar=("REGULAR", "BOLD"), help="TrueType font files to embed")
    args = ap.parse_args()

    try:
        raw = json.loads(Path(args.plan_json).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        fail(f"file not found: {args.plan_json}")
    except UnicodeDecodeError:
        fail(f"{args.plan_json} is not UTF-8 - save it as UTF-8")
    except json.JSONDecodeError as exc:
        fail(f"{args.plan_json} is not valid JSON: {exc}")
    data = validate(clean(raw))

    too_long = [f'"{b.get("label") or "paste"}" in "{s["heading"]}": {len(b["text"]):,} characters, '
                f'limit {b["limit"]:,}' for s, b in paste_blocks(data)
                if b.get("limit") and len(b["text"]) > b["limit"]]
    if too_long:
        fail("texts longer than their LinkedIn field (shorten them):\n  " + "\n  ".join(too_long))

    size = str(args.page_size or data["meta"].get("page_size") or "a4").strip().lower()
    if size not in ("a4", "letter"):
        fail(f'page size must be "a4" or "letter", got "{size}"')
    fonts = find_fonts(args.font)

    Path(args.out_pdf).resolve().parent.mkdir(parents=True, exist_ok=True)
    build_pdf(data, args.out_pdf, size, fonts)
    print(f"pdf: {args.out_pdf} (font: {fonts[0]}, page: {size})")
    if args.docx:
        Path(args.docx).resolve().parent.mkdir(parents=True, exist_ok=True)
        build_docx(data, args.docx, size)
        print(f"docx: {args.docx}")
    if args.preview:
        import pypdfium2 as pdfium
        out = Path(args.preview)
        out.mkdir(parents=True, exist_ok=True)
        pdf = pdfium.PdfDocument(str(args.out_pdf))
        for i in range(len(pdf)):
            pdf[i].render(scale=1.4).to_pil().save(out / f"plan_page_{i + 1}.png")
        print(f"previews: {out} ({len(pdf)} page(s))")

    print("paste blocks:")
    for sec, block in paste_blocks(data):
        print(f"  {sec['heading']} | {count_label(block, LABELS)}")
    holes = sorted({m for _, b in paste_blocks(data) for m in PLACEHOLDER.findall(b["text"])})
    print(f"placeholders for the person to fill or delete: {', '.join(holes) if holes else 'none'}")


if __name__ == "__main__":
    main()
