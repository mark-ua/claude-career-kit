#!/usr/bin/env python3
"""ATS and truth check for a built resume PDF.

Structural checks (what a parser will "see"): page count, text extraction with two
independent parsers, unreadable glyphs, embedded fonts, section headings and their
order, unusual characters, an e-mail address, no keyword metadata, no [placeholder]
left over from a template or a profile review plan, no "(unconfirmed)" marker.
Truth checks: forbidden terms (things the candidate must not claim or disclose) and
job titles / employers / dates identical to the master resume.
Information only: keyword coverage against the vacancy.

Usage (run with the kit's venv interpreter):
    python check_resume.py resume.pdf
        [--keywords keywords.json] [--forbid forbid.json]
        [--resume resume.json] [--master master-resume.json]
        [--max-pages 2] [--preview DIR] [--no-email-ok] [--json]

keywords.json: ["term", ...] or {"must": [...], "nice": [...]}. "A|B" lists true
synonyms of the same thing ("CI/CD|continuous integration"), never two different tools.
forbid.json:   ["term", ...] (or an object of such lists) - any occurrence fails the
               check. Write bare terms; an entry with a note ("Acme (NDA)", "X - not
               claimable") or a list ("Acme, Globex") is also checked by its bare parts.
--resume:      the JSON the PDF was built from (gives custom section labels and the
               experience list for the --master comparison). In a translated resume each
               job keeps the master's title/company/dates in "original", and the name in
               meta.original_name; those are compared instead of the printed text.

Missing keywords are reported, not failed: a keyword the candidate cannot honestly
claim must stay missing. Exit code 1 on structural or truth problems.
Side effect: writes <resume>.extracted.txt next to the PDF.
"""
import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):          # Windows consoles are often cp1252/cp866
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass

LABELS = {"summary": "Summary", "skills": "Skills", "experience": "Professional Experience",
          "projects": "Projects", "education": "Education", "certifications": "Certifications",
          "languages": "Languages"}
REQUIRED = ("skills", "experience")
ALLOWED_SYMBOLS = set("•–—‘’“”…€£№·™®©°×§")
TRANSLATE = str.maketrans({"–": "-", "—": "-", "‑": "-", "‐": "-",
                           "‘": "'", "’": "'", "“": '"', "”": '"', " ": " "})


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        sys.exit(f"error: file not found: {path}")
    except (ValueError, UnicodeDecodeError) as exc:
        sys.exit(f"error: {path} is not valid UTF-8 JSON: {exc}")


def term_groups(value, path):
    """keywords.json / forbid.json: a list of terms, one term as text, or an object of such
    lists ({"must": [...], "nice": [...]}). Anything else is refused, never ignored."""
    groups = value if isinstance(value, dict) else {"must": value}
    out = {}
    for group, words in groups.items():
        words = [words] if isinstance(words, str) else words
        if not isinstance(words, list) or not all(isinstance(w, str) for w in words):
            sys.exit(f'error: {path} must be a list of terms such as ["Figma", "Design Systems"], '
                     "or an object of such lists")
        out[group] = words
    return out


def bare_parts(term):
    """A forbidden entry plus its bare parts: "Acme (NDA client)", "Acme - client" and
    "Acme, Globex" are also checked as "Acme" and "Globex"."""
    plain = re.sub(r"\([^)]*\)", " ", term.split(" # ")[0])
    out = []
    for part in (term, plain, *re.split(r"[,;]|\s+[-–—]\s+", plain)):
        part = part.strip()
        if part and part not in out:
            out.append(part)
    return out


def norm(text):
    """Unify dashes/quotes and collapse whitespace. Case is kept: short terms are case-sensitive."""
    return re.sub(r"\s+", " ", text.translate(TRANSLATE))


def term_regex(term, plural=True):
    """Regex for one keyword alternative.

    - spaces and hyphens are interchangeable ("end-to-end" = "end to end");
    - neighbours may not be letters, digits, "#" or "+", so "Java" does not match
      "JavaScript" and "C" does not match "C#" or "C++";
    - a term that starts with a symbol (".NET") may follow a word ("ASP.NET");
    - terms of up to 3 letters/digits are case-sensitive ("Go" is not "go/no-go");
    - an English plural ending is accepted ("design system" = "design systems").
    """
    term = norm(term).strip()
    if not term:
        return None
    tokens = [re.escape(t) for t in re.split(r"[\s-]+", term) if t]
    body = r"[\s-]+".join(tokens)
    left = r"(?<![\w#+])" if (term[0].isalnum() or term[0] == "_") else ""
    ends_word = term[-1].isalnum() or term[-1] == "_"
    tail = (r"(?:e?s)?" if plural and term[-1].isalpha() else "") + (r"(?![\w#+])" if ends_word else "")
    short = len(re.sub(r"[\W_]", "", term)) <= 3
    return re.compile(left + body + tail, 0 if short else re.I)


def found(term, text, plural=True):
    return any((rx := term_regex(alt, plural)) and rx.search(text) for alt in term.split("|"))


def odd_characters(text):
    return sorted({c for c in text if not (c.isalnum() or c.isspace() or 32 <= ord(c) < 127
                                           or c in ALLOWED_SYMBOLS)})


def unembedded_fonts(reader):
    bad = set()
    for page in reader.pages:
        resources = page.get("/Resources")
        fonts = (resources.get_object() if resources is not None else {}).get("/Font")
        for ref in (fonts.get_object().values() if fonts is not None else []):
            font = ref.get_object()
            holder = font
            if font.get("/Subtype") == "/Type0" and font.get("/DescendantFonts"):
                holder = font["/DescendantFonts"][0].get_object()
            desc = holder.get("/FontDescriptor")
            desc = desc.get_object() if desc is not None else {}
            if not any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                bad.add(str(font.get("/BaseFont", "?")).lstrip("/"))
    return sorted(bad)


def section_report(text, labels):
    pos = {}
    for key, label in labels.items():
        m = re.search(rf"^[ \t]*{re.escape(label.upper())}[ \t]*$", text, re.M)   # a heading is a whole line
        if m:
            pos[key] = m.start()
    present = [k for k in labels if k in pos]
    in_order = all(pos[a] < pos[b] for a, b in zip(present, present[1:]))
    return present, in_order, [labels[k] for k in REQUIRED if k not in pos]


def compare_with_master(resume, master):
    """Titles, employers and dates must come from the master file unchanged. A translated
    job is compared through its "original" (the master's title, company and dates)."""
    known = {(j.get("title"), j.get("company"), j.get("dates"))
             for j in master.get("experience", []) if isinstance(j, dict)}
    problems = []
    for i, job in enumerate(resume.get("experience", []), 1):
        if not job.get("include", True):
            continue
        src = job["original"] if isinstance(job.get("original"), dict) else job
        key = (src.get("title"), src.get("company"), src.get("dates"))
        if key not in known:
            problems.append(f'experience[{i}] "{src.get("title")}" at "{src.get("company")}" '
                            f'({src.get("dates")}) does not match any job in the master resume '
                            "(title, employer and dates must stay identical)")
    name = (resume.get("meta") or {}).get("original_name") or resume.get("name")
    if name != master.get("name"):
        problems.append("name differs from the master resume")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf")
    ap.add_argument("--keywords")
    ap.add_argument("--forbid")
    ap.add_argument("--resume")
    ap.add_argument("--master")
    ap.add_argument("--max-pages", type=int, default=2)
    ap.add_argument("--preview", help="directory for PNG page previews")
    ap.add_argument("--no-email-ok", action="store_true",
                    help="do not fail on a missing e-mail (only when the person gave none)")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args()

    import pdfplumber
    from pypdf import PdfReader

    pdf_path = Path(args.pdf)
    resume = load_json(args.resume) if args.resume else None
    labels = {**LABELS, **(((resume or {}).get("meta") or {}).get("labels") or {})}

    reader = PdfReader(pdf_path)
    texts = {"pypdf": "\n".join(pg.extract_text() or "" for pg in reader.pages)}
    with pdfplumber.open(pdf_path) as pdf:
        texts["pdfplumber"] = "\n".join(pg.extract_text() or "" for pg in pdf.pages)
        used_fonts = {c.get("fontname", "") for pg in pdf.pages for c in pg.chars}

    problems = []
    meta = {k.lstrip("/"): str(v) for k, v in (reader.metadata or {}).items()
            if k in ("/Title", "/Author", "/Subject", "/Keywords")}
    report = {"file": str(pdf_path), "pages": len(reader.pages),
              "size_kb": pdf_path.stat().st_size // 1024, "metadata": meta, "parsers": {}}
    if report["pages"] > args.max_pages:
        problems.append(f"{report['pages']} pages (max {args.max_pages})")
    if meta.get("Keywords"):
        problems.append("the PDF carries keyword metadata - keywords belong in the visible text only")

    # A PDF may declare a built-in font it never draws with; only fonts that set text count.
    not_embedded = [f for f in unembedded_fonts(reader)
                    if any(u == f or u.endswith("+" + f) for u in used_fonts)]
    if not_embedded:
        problems.append(f"fonts not embedded: {not_embedded} - text may be unreadable for an ATS; "
                        "rebuild with a TrueType font")

    for name, text in texts.items():
        present, in_order, missing = section_report(text, labels)
        odd = odd_characters(text)
        unreadable = len(re.findall(r"\(cid:\d+\)", text)) + text.count("\x00") + text.count("�")
        report["parsers"][name] = {"chars": len(text), "sections": present,
                                   "sections_in_order": in_order, "odd_chars": odd,
                                   "unreadable_glyphs": unreadable}
        if len(text) < 500:
            problems.append(f"{name}: almost no text extracted - the PDF is not machine-readable")
        if unreadable:
            problems.append(f"{name}: {unreadable} characters cannot be extracted (font problem) - "
                            "an ATS will see garbage there")
        if not in_order:
            problems.append(f"{name}: sections are extracted out of order")
        if missing:
            problems.append(f"{name}: missing section headings {missing}")
        if odd:
            problems.append(f"{name}: unusual characters {odd} (may turn into garbage in an ATS)")

    a, b = (len(t) for t in texts.values())
    if min(a, b) < 0.9 * max(a, b):
        problems.append("the two parsers disagree by more than 10% - layout is fragile")

    text = norm(texts["pdfplumber"])
    report["has_email"] = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text))
    if not report["has_email"] and not args.no_email_ok:
        problems.append("no e-mail address found in the extracted text")
    placeholders = sorted(set(re.findall(r"\[[^\[\]\n]{1,40}\]", text)))
    if placeholders:
        problems.append(f"unfilled placeholders {placeholders} - a resume must not contain [brackets]: "
                        "use a confirmed fact or drop the phrase")
    if re.search(r"\(\s*unconfirmed\s*\)", text, re.I):
        problems.append('"(unconfirmed)" is in the text - confirm the fact with the user, or leave it out')

    if args.forbid:
        entries = [t for words in term_groups(load_json(args.forbid), args.forbid).values() for t in words]
        hits = []
        for entry in entries:
            hits += [p for p in bare_parts(entry) if p not in hits and found(p, text, plural=False)]
        report["forbidden_found"] = hits
        if hits:
            problems.append(f"forbidden terms present: {hits} - remove them (not claimable or confidential)")

    if args.master:
        if not resume:
            sys.exit("error: --master needs --resume (the JSON the PDF was built from)")
        mismatches = compare_with_master(resume, load_json(args.master))
        report["master_mismatches"] = mismatches
        problems += mismatches

    if args.keywords:
        report["keywords"] = {}
        for group, words in term_groups(load_json(args.keywords), args.keywords).items():
            missing = [w for w in words if not found(w, text)]
            total = len(words)
            report["keywords"][group] = {
                "covered": total - len(missing), "total": total,
                "coverage_pct": round(100 * (total - len(missing)) / total) if total else None,
                "missing": missing}

    if args.preview:
        import pypdfium2 as pdfium
        out = Path(args.preview)
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("page_*.png"):            # a shorter rebuild must not leave stale pages
            old.unlink()
        doc = pdfium.PdfDocument(str(pdf_path))
        for i in range(len(doc)):
            doc[i].render(scale=1.6).to_pil().save(out / f"page_{i + 1}.png")
        report["previews"] = str(out)

    pdf_path.with_suffix(".extracted.txt").write_text(texts["pdfplumber"], encoding="utf-8")
    report["problems"] = problems
    report["ok"] = not problems

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"pages: {report['pages']}  size: {report['size_kb']} KB  metadata: {meta}")
        for name, r in report["parsers"].items():
            print(f"[{name}] chars={r['chars']} sections_in_order={r['sections_in_order']} "
                  f"unreadable={r['unreadable_glyphs']} odd_chars={r['odd_chars']}")
        for group, r in report.get("keywords", {}).items():
            print(f"keywords[{group}]: {r['covered']}/{r['total']} ({r['coverage_pct']}%)"
                  f"  missing: {r['missing']}")
        if "forbidden_found" in report:
            print(f"forbidden terms found: {report['forbidden_found']}")
        if report.get("previews"):
            print(f"previews: {report['previews']}")
        print("OK" if report["ok"] else "PROBLEMS:\n- " + "\n- ".join(problems))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
