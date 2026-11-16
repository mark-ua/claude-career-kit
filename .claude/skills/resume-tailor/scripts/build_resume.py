#!/usr/bin/env python3
"""Build an ATS-friendly resume (PDF, optionally DOCX) from a resume JSON file.

ATS rules baked in: single column, no tables / text boxes / images / icons, standard
section headings, embedded Unicode font, contact details in the body (not in a page
header), no hidden keywords in the file metadata.

Usage (run with the kit's venv interpreter):
    python build_resume.py resume.json out.pdf [--docx out.docx] [--page-size a4|letter]
                           [--font REGULAR.ttf BOLD.ttf]

JSON schema (unknown keys such as "note" are ignored; empty sections are skipped;
any list item may carry "include": false to keep it in the file but out of the output):
{
  "meta": {"target_role": "Product Designer",        # used in the PDF title only
           "company": "Acme",                         # informational
           "page_size": "a4",                         # "a4" (default) or "letter"
           "labels": {"summary": "Profil"}},          # optional heading overrides, see LABELS
  "name": "First Last",
  "headline": "Role | Strength | Core tools",
  "contact": [{"text": "City, Country (UTC+1)"}, {"text": "me@mail.com", "link": "mailto:me@mail.com"}],
  "summary": "3-4 lines.",
  "skills": [{"label": "Research", "items": "Interviews, Surveys, ..."}],
  "experience": [{"title": "", "company": "", "location": "", "dates": "Jan 2022 – Present",
                  "intro": "", "bullets": ["..."]}],
  "projects": [{"name": "", "dates": "", "description": "", "bullets": []}],
  "education": [{"degree": "", "school": "", "dates": ""}],
  "certifications": [{"name": "", "issuer": "", "issued": "Apr 2025", "expires": "",
                      "credential_id": "", "url": "", "skills": []}],   # only name, issuer, year are printed
  "languages": "English (C1), ..."
}
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

for _stream in (sys.stdout, sys.stderr):          # Windows consoles are often cp1252/cp866
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass

LABELS = {"summary": "Summary", "skills": "Skills", "experience": "Professional Experience",
          "projects": "Projects", "education": "Education", "certifications": "Certifications",
          "languages": "Languages"}

# (family, regular file, bold file) - looked up in FONT_DIRS in this order.
FONT_FILES = [
    ("Arial", "Arial.ttf", "Arial Bold.ttf"),
    ("Arial", "arial.ttf", "arialbd.ttf"),
    ("LiberationSans", "LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"),
    ("Arimo", "Arimo-Regular.ttf", "Arimo-Bold.ttf"),
    ("NotoSans", "NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
    ("DejaVuSans", "DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
]
INK = "#1a1a1a"
MUTED = "#444444"


def fail(message):
    sys.exit(f"error: {message}")


def font_dirs():
    home = Path.home()
    dirs = [Path(__file__).resolve().parent.parent / "assets" / "fonts",   # a font placed in the skill
            Path("/System/Library/Fonts/Supplemental"), Path("/Library/Fonts"), home / "Library/Fonts",
            Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts", Path("/mnt/c/Windows/Fonts"),
            Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
            home / ".fonts", home / ".local/share/fonts"]
    return [d for d in dirs if d.is_dir()]


def find_fonts(explicit):
    """Return (family, regular path, bold path). Fails instead of using a built-in font:
    built-in Helvetica is not embedded and breaks bullets and non-Latin text in ATS parsers."""
    if explicit:
        regular, bold = (Path(p) for p in explicit)
        for p in (regular, bold):
            if not p.is_file():
                fail(f"font file not found: {p}")
        return "ResumeFont", regular, bold
    dirs = font_dirs()
    for family, reg_name, bold_name in FONT_FILES:
        for d in dirs:
            reg = d / reg_name if (d / reg_name).is_file() else next(d.rglob(reg_name), None)
            bold = d / bold_name if (d / bold_name).is_file() else next(d.rglob(bold_name), None)
            if reg and bold:
                return family, reg, bold
    fail("no usable TrueType font found (looked for Arial, Liberation Sans, Arimo, Noto Sans, "
         "DejaVu Sans). Install one of them (Linux: the fonts-liberation or dejavu fonts package) "
         "or pass --font REGULAR.ttf BOLD.ttf")


# ---------------------------------------------------------------- input

def clean(value):
    """Drop control characters that break PDF/DOCX writers."""
    if isinstance(value, str):
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value


def validate(data):
    if not isinstance(data, dict):
        fail("the resume file must contain one JSON object")
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        fail('"name" is required and must be text')
    if data.get("meta") is None:
        data["meta"] = {}
    if not isinstance(data["meta"], dict):
        fail('"meta" must be an object')
    for key in ("headline", "summary", "languages"):
        if data.get(key) is None:
            data[key] = ""
        if not isinstance(data[key], str):
            fail(f'"{key}" must be text')
    required = {"contact": "text", "skills": "label", "experience": "title", "projects": "name",
                "education": "degree", "certifications": "name"}
    for section, key in required.items():
        if data.get(section) is None:
            data[section] = []
        if not isinstance(data[section], list):
            fail(f'"{section}" must be a list')
        for i, item in enumerate(data[section], 1):
            where = f'{section}[{i}]'
            if not isinstance(item, dict):
                fail(f"{where} must be an object")
            if not isinstance(item.get(key), str) or not item[key].strip():
                fail(f'{where} needs "{key}" (text)')
            if "include" in item and not isinstance(item["include"], bool):
                fail(f'{where}: "include" must be true or false (not text)')
            if "bullets" in item:
                if item["bullets"] is None:
                    item["bullets"] = []
                if not isinstance(item["bullets"], list) or not all(isinstance(b, str) for b in item["bullets"]):
                    fail(f'{where}: "bullets" must be a list of texts')
            if section == "skills" and not isinstance(item.get("items"), str):
                fail(f'{where} needs "items" (one text with comma-separated skills)')
    labels = data["meta"].get("labels") or {}
    if not isinstance(labels, dict) or set(labels) - set(LABELS):
        fail(f'"meta.labels" may only contain: {", ".join(LABELS)}')
    return data


def page_size_of(data, arg):
    size = str(arg or data["meta"].get("page_size") or "a4").strip().lower()
    if size not in ("a4", "letter"):
        fail(f'page size must be "a4" or "letter", got "{size}"')
    return size


def included(items):
    return [i for i in items if i.get("include", True)]


def join_meta(*parts):
    return "  |  ".join(p for p in parts if p)


def cert_line(c):
    year = str(c.get("year") or "")
    if not year:
        found = re.search(r"\b(19|20)\d{2}\b", str(c.get("issued") or ""))
        year = found.group(0) if found else ""
    tail = ", ".join(p for p in (c.get("issuer"), year) if p)
    return f'{c["name"]} – {tail}' if tail else c["name"]


def contact_lines(contact):
    """One line for up to 3 items, otherwise two balanced lines."""
    if len(contact) <= 3:
        return [contact] if contact else []
    cut = len(contact) // 2
    return [contact[:cut], contact[cut:]]


def sections(data):
    """The resume body as [(heading, [group, ...])]; a group is a list of blocks kept together.

    Block kinds: ("job", text) bold line, ("meta", text) muted line, ("body", text),
    ("labeled", label, text), ("bullets", [text, ...]). Both renderers walk this one structure.
    """
    labels = {**LABELS, **(data["meta"].get("labels") or {})}
    out = []

    def add(key, groups):
        groups = [g for g in groups if g]
        if groups:
            out.append((labels[key], groups))

    add("summary", [[("body", data["summary"])]] if data["summary"] else [])
    add("skills", [[("labeled", g["label"], g["items"]) for g in included(data["skills"])]])
    jobs = []
    for job in included(data["experience"]):
        group = [("job", job["title"]),
                 ("meta", join_meta(job.get("company"), job.get("location"), job.get("dates")))]
        if job.get("intro"):
            group.append(("body", job["intro"]))
        if job.get("bullets"):
            group.append(("bullets", job["bullets"]))
        jobs.append(group)
    add("experience", jobs)
    projects = []
    for pr in included(data["projects"]):
        group = [("job", pr["name"])]
        if pr.get("dates"):
            group.append(("meta", pr["dates"]))
        if pr.get("description"):
            group.append(("body", pr["description"]))
        if pr.get("bullets"):
            group.append(("bullets", pr["bullets"]))
        projects.append(group)
    add("projects", projects)
    add("education", [[("job", ed["degree"]), ("meta", join_meta(ed.get("school"), ed.get("dates")))]
                      for ed in included(data["education"])])
    certs = [cert_line(c) for c in included(data["certifications"])]
    add("certifications", [[("bullets", certs)]] if certs else [])
    add("languages", [[("body", data["languages"])]] if data["languages"] else [])
    return out


# ---------------------------------------------------------------- PDF

def build_pdf(data, out_path, page_size, fonts):
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (HRFlowable, KeepTogether, ListFlowable, ListItem,
                                    Paragraph, SimpleDocTemplate, Spacer)

    family, reg_path, bold_path = fonts
    regular, bold = family, f"{family}-Bold"
    pdfmetrics.registerFont(TTFont(regular, str(reg_path)))
    pdfmetrics.registerFont(TTFont(bold, str(bold_path)))
    pdfmetrics.registerFontFamily(family, normal=regular, bold=bold)

    S = {
        "name": ParagraphStyle("name", fontName=bold, fontSize=18, leading=22,
                               alignment=TA_CENTER, textColor=INK),
        "headline": ParagraphStyle("headline", fontName=regular, fontSize=10.5, leading=14,
                                   alignment=TA_CENTER, textColor=INK),
        "contact": ParagraphStyle("contact", fontName=regular, fontSize=9.5, leading=13,
                                  alignment=TA_CENTER, textColor=MUTED),
        "h": ParagraphStyle("h", fontName=bold, fontSize=11, leading=14, textColor=INK,
                            spaceBefore=9, spaceAfter=2),
        "body": ParagraphStyle("body", fontName=regular, fontSize=9.6, leading=12.6,
                               textColor=INK),
        "job": ParagraphStyle("job", fontName=bold, fontSize=10, leading=13, textColor=INK,
                              spaceBefore=6),
        "meta": ParagraphStyle("meta", fontName=regular, fontSize=9.4, leading=12.4,
                               textColor=MUTED),
        "bullet": ParagraphStyle("bullet", fontName=regular, fontSize=9.6, leading=12.4,
                                 textColor=INK),
    }

    def p(text, style):
        return Paragraph(escape(text), S[style])

    def render(block):
        kind = block[0]
        if kind == "labeled":
            return Paragraph(f"<b>{escape(block[1])}:</b> {escape(block[2])}", S["body"])
        if kind == "bullets":
            return ListFlowable(
                [ListItem(p(t, "bullet"), leftIndent=12, value="•") for t in block[1]],
                bulletType="bullet", start="•", leftIndent=12, bulletFontName=regular,
                bulletFontSize=9, spaceBefore=1)
        return p(block[1], kind)

    story = [p(data["name"], "name")]
    if data["headline"]:
        story.append(p(data["headline"], "headline"))
    for line in contact_lines(included(data["contact"])):
        story.append(Paragraph("  |  ".join(
            f'<a href="{escape(c["link"], {chr(34): "&quot;"})}">{escape(c["text"])}</a>'
            if c.get("link") else escape(c["text"]) for c in line), S["contact"]))
    story.append(Spacer(1, 2))

    for heading, groups in sections(data):
        head = [p(heading.upper(), "h"),
                HRFlowable(width="100%", thickness=0.6, color=MUTED, spaceBefore=0, spaceAfter=4)]
        for i, group in enumerate(groups):
            flowables = [render(b) for b in group]
            # The heading travels with the first group so it is never left alone at a page end;
            # a group stays on one page unless it cannot fit a whole page.
            story.append(KeepTogether(head + flowables if i == 0 else flowables))

    role = (data["meta"].get("target_role") or "").strip()
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4 if page_size == "a4" else letter,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        title=f'{data["name"]} - Resume' + (f" - {role}" if role else ""),
        author=data["name"], subject=f"{role} resume" if role else "Resume",
        creator=data["name"])
    doc.build(story)


# ---------------------------------------------------------------- DOCX

def build_docx(data, out_path, page_size):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Mm, Pt, RGBColor

    doc = Document()
    sec = doc.sections[0]
    if page_size == "a4":
        sec.page_width, sec.page_height = Mm(210), Mm(297)
    else:
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(0.6)
    sec.top_margin = sec.bottom_margin = Inches(0.5)
    base = doc.styles["Normal"]
    base.font.name, base.font.size = "Arial", Pt(10)
    base.paragraph_format.space_after = Pt(0)

    def para(text="", bold=False, size=None, center=False, style=None, before=0):
        par = doc.add_paragraph(style=style)
        run = par.add_run(text)
        run.bold = bold
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
        if size:
            run.font.size = Pt(size)
        if center:
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_before = Pt(before)
        return par

    para(data["name"], bold=True, size=18, center=True)
    if data["headline"]:
        para(data["headline"], center=True, size=10.5)
    for line in contact_lines(included(data["contact"])):
        para("  |  ".join(c["text"] for c in line), center=True, size=9.5)

    for heading, groups in sections(data):
        para(heading.upper(), bold=True, size=11, before=9)
        for group in groups:
            for block in group:
                kind = block[0]
                if kind == "job":
                    para(block[1], bold=True, before=6)
                elif kind == "labeled":
                    par = para(f"{block[1]}: ", bold=True)
                    par.add_run(block[2]).font.name = "Arial"
                elif kind == "bullets":
                    for t in block[1]:
                        para(t, style="List Bullet")
                else:
                    para(block[1])

    props = doc.core_properties
    props.author = data["name"]
    props.title = f'{data["name"]} - Resume'
    props.comments = ""
    doc.save(str(out_path))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("resume_json")
    ap.add_argument("out_pdf")
    ap.add_argument("--docx", help="also write a DOCX copy (plain text, links not clickable)")
    ap.add_argument("--page-size", help="a4 (default) or letter (US/Canada)")
    ap.add_argument("--font", nargs=2, metavar=("REGULAR", "BOLD"), help="TrueType font files to embed")
    args = ap.parse_args()

    try:
        raw = json.loads(Path(args.resume_json).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        fail(f"file not found: {args.resume_json}")
    except UnicodeDecodeError:
        fail(f"{args.resume_json} is not UTF-8 - save it as UTF-8")
    except json.JSONDecodeError as exc:
        fail(f"{args.resume_json} is not valid JSON: {exc}")
    data = validate(clean(raw))
    page_size = page_size_of(data, args.page_size)
    fonts = find_fonts(args.font)

    Path(args.out_pdf).resolve().parent.mkdir(parents=True, exist_ok=True)
    build_pdf(data, args.out_pdf, page_size, fonts)
    print(f"pdf: {args.out_pdf} (font: {fonts[0]}, page: {page_size})")
    if args.docx:
        Path(args.docx).resolve().parent.mkdir(parents=True, exist_ok=True)
        build_docx(data, args.docx, page_size)
        print(f"docx: {args.docx}")


if __name__ == "__main__":
    main()
