#!/usr/bin/env python3
"""Package the career kit skills into a shareable zip or folder, without personal data.

The script is a safety net, not a guarantee: it catches the owner's known identifiers
(name, e-mail, phone, profile URLs, employers, schools and the "Export check terms"
list in career/candidate.md). It cannot recognise a personal fact that was paraphrased
into an "example" - that needs the read-through described in SKILL.md.

It fails closed. Nothing is written when:
  * a private term appears in a file's text or in a file/folder name;
  * a file is not a known text type and is not listed in kit.json "binary_files";
  * a text file is not valid UTF-8, or a path is a symlink;
  * no private terms could be collected (unless --allow-empty-terms).

Usage (from the project root; use `py -3` instead of `python3` on Windows):
    python3 .claude/skills/career-kit-share/scripts/export_kit.py
        [--project ROOT] [--out PATH.zip] [--to-dir FOLDER]
        [--extra-term TEXT ...] [--allow TERM ...] [--allow-empty-terms]

--to-dir writes the kit into a folder (for example a git checkout) instead of a zip:
the folder's .claude/skills/ and the kit's root files are replaced, everything else
(.git, a career/ folder with someone's data) is left alone. Add --out for a zip too.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):          # Windows consoles are often cp1252/cp866
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass

TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".yaml", ".yml"}
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", "__pycache__", ".venv", "node_modules"}
JUNK_SUFFIXES = {".pyc", ".bak", ".orig", ".tmp", ".swp"}
SKIP_DIR_SUFFIX = "-workspace"                    # skill-creator eval workspaces
ALNUM = r"[^\W_]"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
TERMS_HEADING = re.compile(r"^#{2,3}\s*(export[- ]check terms|private terms)\b.*$", re.I | re.M)
DEFAULT_ROOT_FILES = {"README.md": "career-kit-share/assets/README.md"}
GITIGNORE = """# Personal data - never commit or share
career/*
!career/.gitkeep
dist/

# Local tooling
.venv/
__pycache__/
*.pyc
.DS_Store
.claude/settings.local.json
"""


def fold(text):
    return unicodedata.normalize("NFKC", text).casefold()


def collapse(text):
    """Folded text with every whitespace run as one space, so line wraps cannot hide a term."""
    return re.sub(r"\s+", " ", fold(text))


def is_junk(rel):
    return any(part in JUNK_NAMES or part.endswith(SKIP_DIR_SUFFIX) or part.startswith("~$")
               or part.endswith("~") for part in rel.parts) or rel.suffix.lower() in JUNK_SUFFIXES


# ---------------------------------------------------------------- private terms

def collect_terms(project, extra):
    """Return (terms, phones, problems). Terms are matched as text, phones by digits."""
    terms, phones, problems = set(extra), set(), []
    career = project / "career"

    master = career / "master-resume.json"
    if master.exists():
        data = json.loads(master.read_text(encoding="utf-8-sig"))
        name = data.get("name", "")
        terms.add(name)
        parts = name.split()
        if len(parts) > 1:
            terms.add(parts[-1])                      # surname; first names are too common
        for c in data.get("contact", []):
            text, link = c.get("text", ""), c.get("link", "")
            for mail in EMAIL.findall(f"{text} {link}"):
                terms.add(mail)
                terms.add(mail.split("@")[0])
            digits = re.sub(r"\D", "", text)
            if len(digits) >= 7 and re.fullmatch(r"[+\d\s().-]+", text.strip()):
                phones.add(digits)
                if len(digits) >= 10:
                    phones.add(digits[-9:])           # national part: "+380 93…" vs "093…"
            for url in (text, link):
                if url.startswith("mailto:") or "@" in url:
                    continue
                bare = re.sub(r"^https?://(www\.)?", "", url).strip("/")
                if "/" in bare and " " not in bare:   # has a path: a personal page, not a domain
                    terms.add(bare)
                    terms.add("/" + bare.split("/", 1)[1])
        for job in data.get("experience", []):
            terms.add(job.get("company", ""))
        for ed in data.get("education", []):
            terms.add(ed.get("school", "").split(",")[0])

    cand = career / "candidate.md"
    if cand.exists():
        text = cand.read_text(encoding="utf-8-sig")
        heading = TERMS_HEADING.search(text)
        if not heading:
            problems.append('career/candidate.md has no "## Export check terms" section - '
                            "add it (it may be empty) so confidential names are checked")
        else:
            body = text[heading.end():]
            nxt = re.search(r"^#{1,3}\s", body, re.M)
            body = re.sub(r"<!--.*?-->", "", body[:nxt.start()] if nxt else body, flags=re.S)
            for line in body.splitlines():
                m = re.match(r"\s*[-*+]\s+(.*)", line)
                if m:
                    terms.add(m.group(1).split(" # ")[0].strip().strip("`").strip())
        profiles = re.search(r"^## Profiles\b(.*?)(?=^## |\Z)", text, re.S | re.M)
        for url in re.findall(r"https?://\S+", profiles.group(1) if profiles else ""):
            bare = re.sub(r"^https?://(www\.)?", "", url).strip("/.,)")
            if "/" in bare:
                terms.add(bare)

    terms = sorted(t for t in (t.strip() for t in terms) if len(t) >= 2)
    return terms, sorted(phones), problems


def term_regex(term):
    """Tokens of the term in order, with any separators (or none) between them.

    "Acme Corp" also matches "AcmeCorp", "acme-corp" and "Acme\\nCorp". Short terms
    must stand alone as a word so that a 3-letter employer does not hit every text.
    """
    tokens = re.findall(ALNUM + "+", fold(term))
    if not tokens:
        return None
    body = r"[\W_]*".join(re.escape(t) for t in tokens)
    if sum(len(t) for t in tokens) < 8:
        body = f"(?<!{ALNUM}){body}(?!{ALNUM})"
    return re.compile(body)


# ---------------------------------------------------------------- files

def kit_files(skills_dir, kit):
    """Return (files to ship, junk not shipped, blocking problems)."""
    binary = {Path(p).as_posix() for p in kit.get("binary_files", [])}
    ship, junk, problems = [], [], []
    for skill in kit["skills"]:
        root = skills_dir / skill
        if root.is_symlink() or not root.is_dir():
            problems.append(f"skill folder missing or a symlink: {skill}")
            continue
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(skills_dir)
            if is_junk(rel):
                if path.is_file():
                    junk.append(rel.as_posix())
                continue
            if path.is_symlink():
                problems.append(f"symlink (not allowed): {rel.as_posix()}")
            elif path.is_file():
                kind = ("text" if path.suffix.lower() in TEXT_SUFFIXES else
                        "binary" if rel.as_posix() in binary else None)
                if kind is None:
                    problems.append(f"unknown file type (not scanned, so not shipped): {rel.as_posix()}"
                                    ' - remove it, or list it in kit.json "binary_files" after checking it')
                else:
                    ship.append((path, Path(".claude/skills") / rel, kind))
    return ship, junk, problems


def scan(files, terms, phones, allow):
    allow = {fold(a) for a in allow}
    patterns = [(t, term_regex(t)) for t in terms if fold(t) not in allow]
    patterns = [(t, p) for t, p in patterns if p]
    hits, problems = [], []

    def check(where, text):
        flat = collapse(text)
        for term, pat in patterns:
            m = pat.search(flat)
            if m:
                hits.append((where, term, flat[max(0, m.start() - 40):m.end() + 40]))
        digits = re.sub(r"\D", "", text)
        for phone in phones:
            if phone in digits and "phone" not in allow:
                hits.append((where, "phone number", f"digits …{phone[-4:]}"))

    for src, rel, kind in files:
        check(f"{rel.as_posix()} (file name)", rel.as_posix())
        if kind != "text":
            continue
        try:
            check(rel.as_posix(), src.read_text(encoding="utf-8-sig"))
        except UnicodeDecodeError:
            problems.append(f"not valid UTF-8 (cannot be scanned): {rel.as_posix()}")
    return hits, problems


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_target(target, project, skills_dir):
    """Refuse folders where replacing .claude/skills/ would destroy the source or someone's skills."""
    if target == project or project.is_relative_to(target):
        return "--to-dir must not be the project itself or a folder that contains it"
    if target.is_relative_to(project / "career") or target.is_relative_to(skills_dir):
        return "--to-dir must not be inside career/ or .claude/skills/"
    managed = target / ".claude" / "skills"
    if managed.is_symlink():
        return f"{managed} is a symlink - not touching it"
    if managed.exists() and not (managed / "career-kit-share" / "kit.json").is_file():
        return f"{managed} exists but does not hold a career kit - not touching it"
    return None


def write_dir(target, files):
    managed = target / ".claude" / "skills"
    if managed.exists():
        shutil.rmtree(managed)                    # skills removed from the kit must disappear too
    for src, rel, _ in files:
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    (target / "career").mkdir(parents=True, exist_ok=True)
    (target / "career" / ".gitkeep").touch()
    (target / ".gitignore").write_text(GITIGNORE, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--project", default=".")
    ap.add_argument("--out", help="zip to write (default dist/career-kit_<date>.zip; "
                                  "with --to-dir a zip is written only when --out is given)")
    ap.add_argument("--to-dir", help="write the kit into this folder (for example a git checkout)")
    ap.add_argument("--extra-term", action="append", default=[],
                    help="additional private term for this run (repeatable)")
    ap.add_argument("--allow", action="append", default=[],
                    help='term to exclude from the check after the owner confirmed a false positive; '
                         '"phone" disables the phone-number check')
    ap.add_argument("--allow-empty-terms", action="store_true",
                    help="export even though no private terms exist (kit not set up yet)")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    skills_dir = project / ".claude" / "skills"
    share_dir = skills_dir / "career-kit-share"
    if not (share_dir / "kit.json").exists():
        sys.exit(f"error: {share_dir / 'kit.json'} not found - run from the project root or pass --project")
    kit = json.loads((share_dir / "kit.json").read_text(encoding="utf-8-sig"))

    files, junk, problems = kit_files(skills_dir, kit)
    for dest, src in kit.get("root_files", DEFAULT_ROOT_FILES).items():
        path = skills_dir / src
        if path.is_symlink() or not path.is_file():
            problems.append(f"root file missing or a symlink: {src}")
        else:
            files.append((path, Path(dest), "text"))

    target = Path(args.to_dir).expanduser().resolve() if args.to_dir else None
    if target:
        problem = check_target(target, project, skills_dir)
        if problem:
            problems.append(problem)

    terms, phones, term_problems = collect_terms(project, args.extra_term)
    problems += term_problems
    if not terms and not args.allow_empty_terms:
        problems.append("no private terms found (is career/ set up?) - the check would compare "
                        "against nothing; pass --allow-empty-terms only if the kit holds no personal data yet")

    hits, scan_problems = scan(files, terms, phones, args.allow)
    problems += scan_problems

    print(f"private terms checked ({len(terms)} + {len(phones)} phone pattern(s)): " + "; ".join(terms))
    if args.allow:
        print("excluded from the check by --allow: " + "; ".join(args.allow))
    if problems or hits:
        print(f"\nEXPORT BLOCKED - nothing was written ({len(hits)} leak hit(s), {len(problems)} problem(s)):\n")
        for where, term, excerpt in hits:
            print(f"  LEAK  {where}  [{term}]  …{excerpt}…")
        for p in problems:
            print(f"  STOP  {p}")
        print("\nReplace personal details with neutral examples (or move the fact into career/) and rerun.")
        sys.exit(1)

    out = None
    if args.out or not target:
        out = Path(args.out) if args.out else project / "dist" / f"career-kit_{dt.date.today()}.zip"
        out.parent.mkdir(parents=True, exist_ok=True)
    manifest = {rel.as_posix(): sha256(src) for src, rel, _ in files}
    manifest_path = project / "dist" / "last-export.json"
    previous = {}
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", {})

    if out:
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for src, rel, _ in files:                 # flat layout: the unzipped folder IS the project
                z.write(src, rel.as_posix())
            z.writestr("career/.gitkeep", "")
            z.writestr(".gitignore", GITIGNORE)
    if target:
        write_dir(target, files)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(
        {"kit": kit["name"], "version": kit["version"], "date": str(dt.date.today()), "files": manifest},
        indent=2), encoding="utf-8")

    changed = sorted(p for p, h in manifest.items() if previous.get(p) != h)
    print(f"kit: {kit['name']} v{kit['version']}")
    print(f"skills: {', '.join(kit['skills'])}")
    print(f"files shipped: {len(files)}  leak hits: 0")
    if junk:
        print(f"not shipped (junk): {', '.join(junk)}")
    if previous:
        print("changed since the last export (read these through before sending): "
              + (", ".join(changed) if changed else "nothing"))
    else:
        print("first export: every file is new - read all of them through before sending")
    if out:
        print(f"zip: {out}")
    if target:
        print(f"folder: {target}")


if __name__ == "__main__":
    main()
