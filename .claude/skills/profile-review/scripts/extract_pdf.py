#!/usr/bin/env python3
"""Extract the text of a LinkedIn "Save to PDF" export (or any PDF profile/resume) to Markdown.

LinkedIn's export has a narrow left column (contact, top skills, languages,
certifications) next to the main column (name, headline, About, experience,
education). A plain text extraction interleaves the two line by line, so each page is
split at the widest empty vertical strip between 15% and 50% of the page width when
there is text on both sides of it. Pages without such a strip are read whole.

Usage (run with the kit's venv interpreter):
    python extract_pdf.py profile.pdf out.md
"""
import argparse
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):          # Windows consoles are often cp1252/cp866
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass

MIN_GUTTER = 8                                    # points of empty space that count as a gutter


def split_columns(page):
    """Return [(name, cropped page), ...] - two columns when a gutter is found, else the page."""
    words = page.extract_words()
    width = int(page.width)
    if not words or width <= 0:
        return [("page", page)]
    covered = [False] * (width + 1)
    for w in words:
        for x in range(max(0, int(w["x0"])), min(width, int(w["x1"])) + 1):
            covered[x] = True
    best, start = None, None
    for x in range(int(width * 0.15), int(width * 0.5) + 1):
        if covered[x]:
            start = None
            continue
        start = x if start is None else start
        if best is None or x - start > best[1] - best[0]:
            best = (start, x)
    if best and best[1] - best[0] >= MIN_GUTTER:
        cut = (best[0] + best[1]) / 2
        left = [w for w in words if w["x1"] <= cut]
        right = [w for w in words if w["x0"] >= cut]
        if len(left) >= 3 and len(right) >= 3:
            return [("left column", page.crop((0, 0, cut, page.height))),
                    ("main column", page.crop((cut, 0, page.width, page.height)))]
    return [("page", page)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf")
    ap.add_argument("out_md")
    args = ap.parse_args()

    import pdfplumber

    src = Path(args.pdf)
    if not src.is_file():
        sys.exit(f"error: file not found: {src}")
    parts, total = [f"# Extracted from {src.name}", ""], 0
    with pdfplumber.open(src) as pdf:
        for number, page in enumerate(pdf.pages, 1):
            for name, region in split_columns(page):
                text = (region.extract_text() or "").strip()
                total += len(text)
                parts += [f"## Page {number} - {name}", "", text or "(no text)", ""]
    out = Path(args.out_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"text: {out} ({total} characters from {len(pdf.pages)} page(s))")
    if total < 300:
        print("warning: almost no text - the PDF may be a scan or an image; ask for the "
              "LinkedIn export or a text resume instead")


if __name__ == "__main__":
    main()
