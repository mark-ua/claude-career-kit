#!/usr/bin/env python3
"""Package the career kit skills into a shareable zip or folder, without personal data.

The script is a safety net, not a guarantee: it catches the owner's known identifiers
(name, e-mail, phone, handles, profile URLs and domains, employers, schools, the names
of people reviewed with profile-review, and the "Export check terms" list in
career/candidate.md). It cannot recognise a personal fact that was paraphrased into an
"example" - that needs the read-through described in SKILL.md.

It fails closed. Nothing is written when:
  * a private term appears in a file's text or in a file/folder name;
  * a file is not a known text type and is not listed in kit.json "binary_files";
  * a text file is not valid UTF-8 (a .json file: not valid JSON), or a path is a symlink;
  * career/ is set up only halfway (candidate.md or master-resume.json missing or unreadable);
  * no private terms could be collected (unless --allow-empty-terms).

Usage (from the project root; use `py -3` instead of `python3` on Windows):
    python3 .claude/skills/career-kit-share/scripts/export_kit.py
        [--project ROOT] [--out PATH.zip] [--to-dir FOLDER]
        [--extra-term TEXT ...] [--allow TERM ...] [--allow-empty-terms]
        [--mark-reviewed] [--show-terms]

--to-dir writes the kit into a folder (for example a git checkout) instead of a zip.
The folder must be new, empty (a .git folder alone is fine) or hold a copy of the kit.
The kit's own skill folders (those in its kit.json) and root files are replaced, the
kit's rules are added to .gitignore, and everything else (.git, other skills, a career/
folder with someone's data) is left alone. Add --out for a zip too.

"Changed since the last read-through" compares with the last run that had
--mark-reviewed - pass it only after the listed files were read through.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
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
SKILL_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
ALNUM = r"[^\W_]"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
HANDLE = re.compile(r"(?<![\w.@/])@([A-Za-z0-9_][A-Za-z0-9_.]{2,})")   # @name, not an e-mail
PHONE = re.compile(r"\+?\d[\d\s().-]{5,}\d")
URLISH = re.compile(r"(https?://)?(www\.)?[\w-]+(\.[\w-]+)*\.[a-z]{2,}(/\S*)?", re.I)
PLATFORMS = {"linkedin.com", "github.com", "gitlab.com", "indeed.com", "djinni.co", "dou.ua",
             "behance.net", "dribbble.com", "medium.com", "t.me", "x.com", "twitter.com",
             "facebook.com", "instagram.com", "youtube.com", "stackoverflow.com", "upwork.com"}
CREDENTIALS = re.compile(r"(ph\.?d\.?|mba|pmp|cpa|cfa|msc|bsc|jr\.?|sr\.?|ii|iii|iv|esq\.?)", re.I)
CONFUSABLE = str.maketrans("аеорсухіјѕ", "aeopcyxijs")   # Cyrillic letters that look Latin
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
    """Comparable form of a text: case, width and accents are folded, and invisible
    characters (zero-width space, soft hyphen) and Cyrillic look-alikes of Latin letters
    cannot hide a term."""
    text = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", text).casefold())
    return "".join(c for c in text if unicodedata.category(c) not in ("Mn", "Cf")).translate(CONFUSABLE)


def is_platform(domain):
    """linkedin.com, and its subdomains such as profile.indeed.com - not a personal domain."""
    domain = domain.lower()
    return any(domain == p or domain.endswith("." + p) for p in PLATFORMS)


def collapse(text):
    """Folded text with every whitespace run as one space, so line wraps cannot hide a term."""
    return re.sub(r"\s+", " ", fold(text))


def is_junk(rel):
    return any(part in JUNK_NAMES or part.endswith(SKIP_DIR_SUFFIX) or part.startswith(("~$", "._"))
               or part.endswith("~") for part in rel.parts) or rel.suffix.lower() in JUNK_SUFFIXES


# ---------------------------------------------------------------- private terms

def name_terms(name):
    """A person's name as written and without a suffix ("Jane Doe, PhD", "Jane Doe (she/her)"),
    plus the surname and longer middle parts. A first name alone is too common to check."""
    name = str(name or "").strip()
    parts = re.split(r"\s*[,(|/]", name)[0].split()
    while len(parts) > 1 and CREDENTIALS.fullmatch(parts[-1]):
        parts.pop()
    terms = {name, " ".join(parts)}
    if len(parts) > 1:
        terms.add(parts[-1])
        terms.update(p for p in parts[1:-1] if len(p) >= 4)
    return terms


def contact_terms(text, link, phones):
    """E-mails, handles, personal pages and domains of one contact; phone digits go to phones."""
    terms, both = set(), f"{text} {link}"
    for mail in EMAIL.findall(both):
        terms.add(mail)
        if len(mail.split("@")[0]) >= 4:          # "me@..." alone would hit every text
            terms.add(mail.split("@")[0])
    terms.update("@" + h.rstrip(".") for h in HANDLE.findall(both))
    dial = link[4:] if link.startswith("tel:") else ""
    plain = "" if "@" in text or URLISH.fullmatch(text.strip()) else text
    for run in PHONE.findall(f"{plain} {dial}"):  # "+1 415 555 0142 (Telegram)", "Phone: ..."
        digits = re.sub(r"\D", "", run)
        if len(digits) >= 7:
            phones.add(digits)
            if len(digits) >= 10:
                phones.add(digits[-9:])           # national part: "+380 93…" vs "093…"
    for url in (text.strip(), link.strip()):
        if url.startswith(("mailto:", "tel:")) or "@" in url or not URLISH.fullmatch(url):
            continue
        bare = re.sub(r"^(https?://)?(www\.)?", "", url, flags=re.I).strip("/")
        if "/" in bare:                           # a personal page: linkedin.com/in/<slug>
            terms.add(bare)
            terms.add("/" + bare.split("/", 1)[1])
        elif not is_platform(bare):               # a personal domain: janedoe.dev
            terms.add(bare)
    return terms


def entry_terms(entry):
    """One "Export check terms" line. Its bare parts are checked too - without (notes) and
    split at "," and ";" - so "Acme (NDA client)" and "Acme, Globex" also catch "Acme"."""
    entry = entry.split(" # ")[0].strip().strip("`").strip()
    plain = re.sub(r"\([^)]*\)", " ", entry)
    return {entry, plain, *re.split(r"[,;]", plain)}


def collect_terms(project, extra):
    """Return (terms, phones, problems). Terms are matched as text, phones by digits."""
    terms, phones, problems = set(extra), set(), []
    career = project / "career"
    master, cand = career / "master-resume.json", career / "candidate.md"
    if master.exists() != cand.exists():
        missing = cand if master.exists() else master
        problems.append(f"career/{missing.name} is missing - finish career-setup first, so that names, "
                        "contacts and confidential terms can all be checked")

    if master.exists():
        try:
            data = json.loads(master.read_text(encoding="utf-8-sig"))
        except (ValueError, UnicodeDecodeError) as exc:
            problems.append(f"career/master-resume.json cannot be read ({exc}) - fix it and rerun")
            data = {}
        data = data if isinstance(data, dict) else {}
        terms |= name_terms(data.get("name"))
        for c in data.get("contact") or []:
            if isinstance(c, dict):
                terms |= contact_terms(str(c.get("text") or ""), str(c.get("link") or ""), phones)
        for job in data.get("experience") or []:
            if isinstance(job, dict):
                terms.add(str(job.get("company") or ""))
        for ed in data.get("education") or []:
            if isinstance(ed, dict):
                terms.add(str(ed.get("school") or "").split(",")[0])

    if cand.exists():
        try:
            text = cand.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            problems.append("career/candidate.md is not UTF-8 - save it as UTF-8 and rerun")
            text = ""
        name = re.search(r"^\s*[-*]\s*Name:[ \t]*(\S.*)$", text, re.M)
        if name:
            terms |= name_terms(name.group(1))
        heading = TERMS_HEADING.search(text)
        if not heading:
            problems.append('career/candidate.md has no "## Export check terms" section - '
                            "add it (it may be empty) so confidential names are checked")
        else:
            body = text[heading.end():]
            nxt = re.search(r"^#{1,3}\s", body, re.M)
            body = re.sub(r"<!--.*?-->", "", body[:nxt.start()] if nxt else body, flags=re.S)
            for line in body.splitlines():
                m = re.match(r"\s*(?:[-*+]|\d+[.)])\s+(.*)", line)
                if m:
                    terms |= entry_terms(m.group(1))
        profiles = re.search(r"^## Profiles\b(.*?)(?=^## |\Z)", text, re.S | re.M)
        for token in re.split(r"[\s,;]+", profiles.group(1) if profiles else ""):
            token = token.strip("()<>.")
            terms.update(EMAIL.findall(token))
            terms.update("@" + h.rstrip(".") for h in HANDLE.findall(token))
            if "@" in token or not URLISH.fullmatch(token):
                continue
            bare = re.sub(r"^(https?://)?(www\.)?", "", token, flags=re.I).strip("/")
            if "/" in bare or not is_platform(bare):           # a profile page or a personal domain
                terms.add(bare)

    reviews = career / "reviews"                  # people helped with profile-review
    for folder in sorted(reviews.glob("*_*")) if reviews.is_dir() else []:
        if folder.is_dir():
            slug = folder.name.split("_", 1)[1]   # <date>_<first-last>
            parts = [p for p in re.split(r"[-_]", slug) if p]
            terms.add(slug)
            if len(parts) > 1 and len(parts[-1]) >= 4:
                terms.add(parts[-1])

    terms = sorted({t for t in (t.strip().strip("`\"'").strip() for t in terms) if len(t) >= 2})
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
        if not isinstance(skill, str) or not SKILL_NAME.fullmatch(skill):
            problems.append(f"kit.json: {skill!r} is not a skill folder name")
            continue
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
    hits, problems, seen = [], [], set()

    def check(where, text):
        flat = collapse(text)
        for term, pat in patterns:
            m = pat.search(flat)
            if m and (where, term) not in seen:
                seen.add((where, term))
                hits.append((where, term, flat[max(0, m.start() - 40):m.end() + 40]))
        digits = re.sub(r"\D", "", text)
        for phone in phones:
            if phone in digits and "phone" not in allow and (where, "phone") not in seen:
                seen.add((where, "phone"))
                hits.append((where, "phone number", f"digits …{phone[-4:]}"))

    for src, rel, kind in files:
        check(f"{rel.as_posix()} (file name)", rel.as_posix())
        if kind != "text":
            continue
        try:
            text = src.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            problems.append(f"not valid UTF-8 (cannot be scanned): {rel.as_posix()}")
            continue
        check(rel.as_posix(), text)
        if src.suffix.lower() == ".json":         # "Acme" in a JSON file is "Acme" once loaded
            try:
                check(rel.as_posix(), json.dumps(json.loads(text), ensure_ascii=False))
            except ValueError:
                problems.append(f"not valid JSON (escaped text cannot be scanned): {rel.as_posix()}")
    return hits, problems


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def same_place(a, b):
    """True when a and b are the same folder - also on case-insensitive disks (macOS,
    Windows), where "~/documents/kit" and "~/Documents/kit" differ as text."""
    try:
        return a.resolve() == b.resolve() or os.path.samefile(a, b)
    except OSError:
        return False


def within(path, folder):
    """True when path is folder itself or anywhere below it."""
    return any(same_place(p, folder) for p in (path, *path.parents))


def check_target(target, project, skills_dir):
    """Refuse a folder where writing the kit would destroy the source, someone's skills or files."""
    if within(project, target):
        return "--to-dir must not be the project itself or a folder that contains it"
    if within(target, project / "career") or within(target, skills_dir):
        return "--to-dir must not be inside career/ or .claude/skills/"
    if target.exists() and not target.is_dir():
        return f"{target} is a file, not a folder"
    managed = target / ".claude" / "skills"
    if managed.is_symlink() or managed.parent.is_symlink():
        return f"{managed} or its .claude folder is a symlink - not touching it"
    if within(managed, skills_dir):
        return f"{managed} is this project's own skills folder - not touching it"
    if (managed / "career-kit-share" / "kit.json").is_file():
        return None                               # an earlier copy of the kit: update it
    if managed.exists():
        return f"{managed} exists but does not hold a career kit - not touching it"
    others = sorted(p.name for p in target.iterdir() if p.name not in (".git", ".DS_Store")) \
        if target.exists() else []
    if others:
        return (f"{target} is not empty and holds no copy of the kit ({', '.join(others[:5])}"
                f"{', …' if len(others) > 5 else ''}) - use a new or empty folder, or a clone of the kit")
    return None


def kit_skills(managed):
    """The skill folders that an existing copy of the kit owns, from its kit.json."""
    try:
        data = json.loads((managed / "career-kit-share" / "kit.json").read_text(encoding="utf-8-sig"))
        return {s for s in data.get("skills", []) if isinstance(s, str) and SKILL_NAME.fullmatch(s)}
    except (OSError, ValueError, AttributeError):
        return set()


def merge_gitignore(path):
    """Add the kit's rules to .gitignore and keep every line that is already there."""
    old = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
    have = {line.strip() for line in old.splitlines()}
    missing = [line for line in GITIGNORE.splitlines()
               if line.strip() and not line.startswith("#") and line.strip() not in have]
    if not old.strip():
        path.write_text(GITIGNORE, encoding="utf-8")
    elif missing:
        path.write_text(old.rstrip("\n") + "\n\n# Career kit\n" + "\n".join(missing) + "\n", encoding="utf-8")


def write_dir(target, files, kit):
    """Replace the kit's own skill folders and root files. Return (removed files, other skills kept)."""
    managed = target / ".claude" / "skills"
    owned = kit_skills(managed) | set(kit["skills"])   # skills dropped from the kit disappear too
    shipped = {target / rel for _, rel, _ in files}
    removed = []
    for name in sorted(owned):
        folder = managed / name
        if folder.is_dir():
            removed += [p.relative_to(target).as_posix() for p in sorted(folder.rglob("*"))
                        if p.is_file() and p not in shipped and not is_junk(p.relative_to(managed))]
            shutil.rmtree(folder)
    for src, rel, _ in files:
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    (target / "career").mkdir(parents=True, exist_ok=True)
    (target / "career" / ".gitkeep").touch()
    merge_gitignore(target / ".gitignore")
    kept = sorted(p.name for p in managed.iterdir() if p.is_dir() and p.name not in owned)
    return removed, kept


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
    ap.add_argument("--mark-reviewed", action="store_true",
                    help="record this export as read through: later runs list only what changes after it")
    ap.add_argument("--show-terms", action="store_true", help="print the private terms that were checked")
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

    print(f"private terms checked: {len(terms)} + {len(phones)} phone pattern(s)"
          + (":\n  " + "\n  ".join(terms) if args.show_terms else " (--show-terms lists them)"))
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
        out = Path(args.out).expanduser() if args.out else project / "dist" / f"career-kit_{dt.date.today()}.zip"
        out.parent.mkdir(parents=True, exist_ok=True)
    manifest = {rel.as_posix(): sha256(src) for src, rel, _ in files}
    manifest_path = project / "dist" / "last-export.json"   # the last export that was read through
    previous = {}
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", {})
        except (ValueError, AttributeError):
            previous = {}

    if out:
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for src, rel, _ in files:                 # flat layout: the unzipped folder IS the project
                z.write(src, rel.as_posix())
            z.writestr("career/.gitkeep", "")
            z.writestr(".gitignore", GITIGNORE)
    removed, kept = write_dir(target, files, kit) if target else ([], [])

    changed = sorted(p for p, h in manifest.items() if previous.get(p) != h)
    gone = sorted(set(previous) - set(manifest))
    print(f"kit: {kit['name']} v{kit['version']}")
    print(f"skills: {', '.join(kit['skills'])}")
    print(f"files shipped: {len(files)}  leak hits: 0")
    if junk:
        print(f"not shipped (junk): {', '.join(junk)}")
    if previous:
        print("changed since the last read-through (read these before sending): "
              + (", ".join(changed) if changed else "nothing"))
        if gone:
            print("no longer in the kit: " + ", ".join(gone))
    else:
        print("no read-through recorded yet: every file is new - read all of them before sending")
    if args.mark_reviewed:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(
            {"kit": kit["name"], "version": kit["version"], "date": str(dt.date.today()), "files": manifest},
            indent=2), encoding="utf-8")
        print("recorded as read through: the next run lists only what changes after this one")
    else:
        print("after the read-through, rerun with --mark-reviewed")
    if out:
        print(f"zip: {out}")
    if target:
        print(f"folder: {target}")
        if removed:
            print("removed from the folder (no longer in the kit): " + ", ".join(removed))
        if kept:
            print("other skills in the folder, left alone: " + ", ".join(kept))


if __name__ == "__main__":
    main()
