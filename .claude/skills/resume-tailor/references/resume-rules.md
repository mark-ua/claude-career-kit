# Resume rules: ATS-safe, short, readable

## How resumes are actually screened (why these rules exist)

This section is the durable baseline. When `career/trends.md` has a newer, sourced
note on ATS or AI screening, that note wins.

1. **Parsing.** The ATS (Workday, Greenhouse, Lever, Ashby, iCIMS, SmartRecruiters,
   Teamtailor...) extracts text into fields. Tables, columns, text boxes, icons and
   headers/footers get scrambled or dropped. The builder script already produces a
   safe layout - do not work around it.
2. **Knock-out questions and filters.** Location, work authorization, years of
   experience, salary. These reject automatically; the resume cannot fix them, so
   check eligibility before writing.
3. **Search and ranking.** Recruiters search and filter by job title and hard skills;
   newer systems add AI match scores that compare the resume with the posting
   semantically. Exact terms for titles and tools still matter most; repeating a word
   ten times does not help and reads as spam to the human.
4. **Human skim.** 6-10 seconds on the top third of page one: headline, summary, the
   latest job's title and first bullets. If the match is not obvious there, the rest
   is not read.

So: make the match obvious at the top, use the posting's exact terms where they are
true, keep it short, and prove claims with numbers.

## Keywords - mirror, do not stuff

- Use the posting's exact wording for things the candidate really has: if they write
  "Stakeholder Management", do not write "working with stakeholders". Give acronym
  and full form once: "Search Engine Optimization (SEO)".
- Each important keyword appears where it carries the most weight: once in the
  summary or headline if central, once in Skills, and in an experience bullet **of a
  job where the master resume shows it was used**. If the master file does not tie
  the skill to any job, it goes in Skills only - do not invent the context. Two or
  three natural mentions are enough.
- The job title in the headline may match the posting's title only when the
  candidate has held that title or did that whole job under another title. Real
  titles in the Experience section are not altered.
- Never: hidden or white text, keywords in the file's metadata, a pasted copy of the
  job description, a keyword block with skills the candidate does not have, invented
  tools/metrics/certificates, "currently learning X" unless `candidate.md` says so.
- A missing must-have keyword is information for the user, not a defect to patch.
  There is no coverage percentage to reach.

## Structure and order

1. Name, headline, contact line (city + country + time zone, e-mail, phone, LinkedIn;
   add the work arrangement the candidate wants, such as "Open to remote", when relevant)
2. Summary - 3-4 lines
3. Skills - 3-5 labeled groups, most relevant group first
4. Professional Experience - reverse chronological
5. Projects - only if they add proof the jobs do not
6. Education, Certifications, Languages

No photo, date of birth, marital status, full street address, "References available
on request", or objective statement.

## Summary (3-4 lines)

Formula: *who you are in their terms* + *years and scope* + *2 strongest proofs that
match their top requirements* + *what you bring to this kind of company*. Written
without "I". No adjectives that cannot be checked ("passionate", "results-driven").

## Experience bullets

- Pattern: **action verb + what + how/with what + measurable result**.
  "Cut release regression from 3 days to 6 hours by automating 400 API checks in CI."
- Order bullets by relevance to this vacancy, not by chronology or pride.
- Latest/most relevant role: 5-7 bullets. Previous: 3-4. Older than ~8-10 years or
  irrelevant: a single line or title + dates only.
- One or two lines per bullet. One idea per bullet.
- Prefer numbers the candidate has already approved in the master file. Never
  round up or create new metrics. If a number is needed and missing, ask.
- Vary the verbs; avoid "responsible for", "helped with", "worked on".
- Follow the candidate's style preferences in `candidate.md` (for example, which
  numbers they prefer to show).

## Length and readability

- 1 page for up to ~7 years of experience; 2 pages maximum for senior profiles.
  A second page must be at least one-third full - otherwise cut to one page.
- Cut in this order: irrelevant skills → old roles' bullets → duplicate proofs →
  nice-to-have details. Never cut the proof of a must-have requirement.
- Plain words, short sentences, consistent tense (present for the current role, past
  for earlier ones), consistent date format "Mon YYYY – Mon YYYY".
- Text that sounds machine-written lowers trust in 2026: avoid stock phrases
  ("leveraged cutting-edge", "spearheaded synergies"), em-dash chains, and empty
  triads. Concrete nouns and numbers read as human.

## File

- PDF from the builder (text-based) is the default; DOCX only when asked for.
- File name: `First_Last_Role_Company.pdf` - recruiters download dozens of
  "resume.pdf".
- US/Canada: Letter size and "resume"; elsewhere A4; the word "CV" is fine in
  Europe.

## Final checks

- [ ] Checker: no structural problems, sections in order, both parsers agree
- [ ] Preview looked at: no orphan lines, no job split awkwardly across pages
- [ ] Top third of page one shows the match with this vacancy
- [ ] Every must-have requirement the candidate meets is visibly proven
- [ ] Titles, employers, dates identical to the master file / LinkedIn
- [ ] Truth pass done: nothing that is not in the master files
- [ ] Disclosure rules respected
- [ ] Spelling checked; no leftover text about a different company
