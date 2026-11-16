---
name: career-kit-share
description: Prepare a clean, shareable copy of the career skills kit (career-setup, profile-upgrade, resume-tailor, job-hunt, profile-review) - as a zip for colleagues or friends, or written into a folder such as a git checkout for publishing - with the owner's personal data left out and a leak check run first. Use whenever the user asks to share, export, copy, package or publish the career/job-search skills - "prepare a copy of the kit for a colleague", "export the career kit", "update the GitHub copy of the kit" - in any language.
---

# Share the career kit

The kit is built so that the skills hold **no personal data**: everything about the
owner lives in `career/`. Sharing is a copy of the skills plus the kit's root files
(README, CLAUDE.md, LICENSE, .gitignore), after two checks that nothing personal
slipped into a skill file:

- the **script** catches known identifiers (name, e-mail, phone, profile URLs,
  employers, schools, and the "Export check terms" list in `career/candidate.md`);
- a **read-through** catches what no word list can: a personal fact rewritten as an
  "example" (a preference, a situation, a gap that is recognisably the owner's).

Both are needed. A clean script run alone is not proof that the kit is safe to send -
say so if the read-through was skipped.

Talk to the user in the language they write in (English when it is unclear). The kit
itself is written in English.

## Steps

1. Run the export script from the project root:

   ```bash
   python3 .claude/skills/career-kit-share/scripts/export_kit.py
   ```

   On Windows use `py -3` in place of `python3`. Options:
   - `--out <path.zip>` (default `dist/career-kit_<YYYY-MM-DD>.zip`)
   - `--to-dir <folder>` - write the clean kit into a folder (for example a git
     checkout) instead of a zip. It replaces that folder's `.claude/skills/` and the
     kit's root files and leaves everything else, such as `.git`, alone. Add `--out`
     to get a zip as well.
   - `--project <root>` (default: current directory)
   - `--extra-term "<text>"` (repeatable) - extra terms for this run, for example the
     names of people whose profiles were reviewed with `profile-review`
   - `--allow "<term>"` (repeatable) - skip one term, see step 2
   - `--allow-empty-terms` - only when `career/` holds no personal data yet

   The script blocks the export and writes nothing when it finds a private term in a
   file's text or in a file name, a file of an unknown type, a file that is not
   UTF-8, a symlink, or no private terms to check against.

2. **If the export is blocked**, do not work around it.
   - Leak hit: open the file, replace the personal detail with a neutral example (or
     move the fact into `career/`), rerun.
   - Unknown file type: remove the file from the skill folder if it does not belong
     to the kit. Only a file that is a real part of the kit (for example a font) may
     be added to `kit.json` → `binary_files`, after opening it and confirming it
     carries no personal data.
   - False positive (a common word that equals a private term): tell the user which
     term matched and where, and rerun with `--allow "<term>"` only on their say-so.
     Never allow a name, e-mail, employer or client.

3. **Read-through.** The script prints the files changed since the last export (all
   files on the first export). Read each of them and compare the examples and
   wording with `career/candidate.md`: no example may mirror the owner's own
   situation, preferences, exclusions, gaps, stack or employers - or the details of
   anyone whose profile was reviewed. Rewrite anything that does and rerun the
   script. Report to the user that this was done and what, if anything, was changed.

4. **Report** the zip path or folder, the skills included with the kit version, and
   what is *not* included (`career/` - personal data, resumes, applications, search
   history, profile reviews). Remind the user that the recipient needs Claude Code
   (desktop app or CLI), the Claude in Chrome extension for the browser skills, and
   Python 3.10+.

5. Do not send the zip anywhere yourself (e-mail, chat, upload), and do not commit,
   push or publish the folder, unless the user asks for that step and names where it
   goes. For a public repository, also check the commit author e-mail before the
   first push: a work or personal address in `git config` becomes public with the
   commits (GitHub's `<id>+<login>@users.noreply.github.com` address avoids that).

## When a new skill is added to the kit

Add its folder name to `kit.json` and bump `version`. Keep personal examples out of
skill files - use neutral ones from a different profession than the owner's.

## What the recipient does

Unzip (or clone), open **the folder that contains `README.md`** in Claude Code, and
say "set up the career kit for me" (or `/career-setup`) in any language. The README
inside explains the rest.
