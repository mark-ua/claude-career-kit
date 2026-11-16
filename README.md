# Claude Career Kit

Claude Code skills for a job search. They help you get a profile recruiters can find,
fresh vacancies ranked by real fit, a resume tailored to each job, and interview prep.
Everything works from one private folder of facts about you.

The kit works in any language. Claude answers in the language you write in, and
English is the default.

## What's inside

| Skill | What it does | Try saying |
|---|---|---|
| `career-setup` | Collects your facts from a resume, your LinkedIn or a short interview into a private `career/` folder. All the other skills read from it | "Set up the career kit for me" |
| `profile-upgrade` | Audits your LinkedIn and Indeed profiles for recruiter and ATS search, proposes changes, and applies the ones you approve in your own browser | "Check my LinkedIn" |
| `job-hunt` | Searches LinkedIn, Indeed, DOU and Djinni for fresh vacancies and ranks them by fit. Each result has a link, score, stack, domain and risks | "Find fresh jobs for me" |
| `resume-tailor` | From a vacancy link, builds an ATS-safe PDF resume, a cover letter, a study list and a brief on the company and its CEO. Runs a mock interview on request | "Tailor my resume to this job: <link>" |
| `profile-review` | Helps someone else. From their LinkedIn PDF it makes a personal update plan with ready-to-paste texts, plus an ATS-safe resume. It works offline and never touches their account | "Make an update plan and a resume from this LinkedIn PDF" |
| `career-kit-share` | Packages a clean copy of the kit for a friend and checks that none of your personal data is in it | "Prepare a copy of the kit for a colleague" |

## How it works

```
your kit folder/
├── README.md, CLAUDE.md
├── .claude/skills/          the skills (no personal data)
└── career/                  YOUR data: stored only on your computer, ignored by git
    ├── candidate.md             goals, preferences, what may and may not be said
    ├── master-resume.json       every job, bullet and skill: the "truth bank"
    ├── trends.md                current hiring trends, refreshed about monthly
    ├── resume/                  your general resume
    ├── profiles/<platform>/     profile snapshots, change log, metrics
    ├── job-search/              search reports, saved postings, jobs already seen
    ├── applications/<date>_<company>_<role>/   resume, letter and prep for one job
    └── reviews/<date>_<name>/   profile reviews you made for other people
```

Every skill reads the same two files. A tailored resume, a profile edit and a job
score therefore all rest on the same facts.

Tailoring selects, orders and words what you have really done. It never invents
experience: a skill you don't have goes on your study list, not into the resume.

## Quick start

1. Install **Claude Code** (desktop app or CLI). For the browser skills, also install
   the **Claude in Chrome** extension. In the CLI, connect Chrome by starting
   `claude --chrome` or with the `/chrome` command.
2. Get the kit:

   ```bash
   git clone https://github.com/mark-ua/claude-career-kit.git
   ```

   Or download the ZIP from the green **Code** button and unzip it.
3. In Claude Code, open **the folder that contains this README**. The skills live in
   the hidden `.claude` folder next to it, so opening a folder one level up won't
   find them.
4. Say **"set up the career kit for me"** or run `/career-setup`. Claude asks for
   your resume or LinkedIn and a few questions: target roles, where you can work,
   pay, exclusions, and what must stay confidential. Then it creates your `career/`
   files.
5. Use it. For example:
   - "check my LinkedIn" (or `/profile-upgrade linkedin`)
   - "find fresh jobs for me" (or `/job-hunt`)
   - "tailor my resume to https://..." (or `/resume-tailor <link>`)
   - "run a mock interview for that job"

To update the kit later, run `git pull` in the cloned folder, or download the ZIP
again and unzip it over the old one. Neither touches your `career/` folder.

## Requirements

- **Claude Code**, desktop app or CLI. It needs a Claude subscription or an API
  account.
- **Claude in Chrome extension**, for `profile-upgrade`, `job-hunt`, and
  `resume-tailor` when a posting is behind a login. Claude works in your Chrome, in
  sessions you are already signed in to. It doesn't type passwords or pass "I am not
  a robot" checks; you do those.
- **Python 3.10 or newer**, to build the PDF resumes and plans (`python3` on
  macOS/Linux, `py -3` on Windows). Setup installs the dependencies after you agree.
  On a Mac, the `python3` that comes with Apple's developer tools can be 3.9: install
  a current Python from python.org or Homebrew. On Windows, if `py` is not found, use
  `python`.
- **On Linux**, one of these fonts: Liberation Sans, DejaVu Sans, Noto Sans or Arimo.

## Know this before you start

- **Account risk.** LinkedIn's terms prohibit software that automates activity on the
  site, and Indeed and job boards have similar rules. The skills work at low volume,
  one page at a time, with no bulk actions. It is still automation, though, and an
  account restriction can't be ruled out, so using the browser skills is your
  decision. Some uses don't need your accounts on these sites at all:
  `profile-review`, `resume-tailor` with a pasted posting (it still searches the
  public web about the company), and `career-setup` from a resume file.
- **Your data is stored locally.** `career/` is in `.gitignore`. Claude reads these
  files while it works, so their content goes to Claude like the rest of the
  conversation. If the kit folder sits in iCloud Drive, OneDrive or Dropbox (including
  a synced "Documents" folder), that cloud gets a copy too. Keep the kit somewhere
  else if you don't want that.
- **Nothing is published without your yes.** Before a profile edit, Claude shows the
  before and after and waits for you. Afterwards it rereads the page to verify.
- **Nothing is sent.** Claude doesn't send applications, messages or e-mails.
- **Truth only.** No invented skills, titles, dates or numbers.

## Helping someone else

`profile-review` is for helping a friend, colleague or follower. Ask them for:

1. their LinkedIn profile as a PDF. On their own profile page it's under
   **Resources** or **More** → **Save to PDF** (the button name varies);
2. the role they are aiming for, and where and how they want to work;
3. anything that must not be mentioned, for example because their current employer
   can see the profile.

Tell them that Claude, an AI assistant, will read what they send.

Claude makes two files in `career/reviews/<date>_<name>/`:

- **a LinkedIn update plan**: what to change, where to find it in LinkedIn, and
  ready-to-paste texts with character counts. It comes as a PDF to read and a DOCX to
  copy from;
- **an ATS-safe resume** built from their profile.

Facts that are unknown are left as [placeholders] for the person to fill in or
delete, so nothing is made up. You send the files yourself, and you can delete the
folder when you're done.

## FAQ

**Do I need LinkedIn Premium?** No.

**Does it work for other professions and countries?** Yes. Roles, keywords, work
format and exclusions come from your `candidate.md`. Search patterns are ready for
LinkedIn, Indeed, DOU and Djinni. For other boards, Claude uses their own filters.

**Which language does it speak?** The one you write in, with English as the default.
Resumes and profile texts are in English unless a posting or profile is in another
language.

**How do I add a new fact about myself?** Tell Claude, for example "remember that I
have experience with X" or "add certificate Y to my profiles".

**How do I share the kit?** Send the GitHub link. Or say "prepare a copy of the kit"
to get a zip without your data.

## License

MIT, see [LICENSE](LICENSE). This project is not affiliated with LinkedIn, Indeed,
DOU, Djinni or Anthropic.
