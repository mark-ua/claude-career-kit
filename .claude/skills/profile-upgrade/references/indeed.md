# Indeed - mechanics and audit checklist

Indeed's pages differ by country site and change often. Treat paths and labels here
as "true when written"; if the page disagrees, trust the page and note it in the
changelog.

## 1. How employers find people on Indeed

- Employers search the resume database (Indeed Smart Sourcing / resume search) by
  **job title, skills, location**, and filter by recent activity, work authorization,
  years of experience and education. Matching features also recommend candidates to
  employers automatically based on the same data.
- Only profiles with a **searchable resume** ("Employers can find you") appear.
- Recency matters: recently updated and recently active profiles are shown first, and
  "ready to work"/availability signals push a profile up.
- Job **preferences** (titles, pay, schedule, remote, relocation) drive both which
  jobs are recommended to the candidate and which employers see them as a match.
- "Matching data" - skills, certifications and licenses Indeed infers or the user
  confirms - is used directly in matching. Wrong inferred skills attract wrong jobs.

## 2. Profile structure

- **Profile home** `https://profile.indeed.com/` - contact info, headline, summary,
  resume(s), "Employers can find you" switch, ready-to-work/availability.
- **Indeed Resume** (built in the editor): summary, work experience, education,
  skills, certifications/licenses, languages, links, additional information. This is
  the structured data that search uses.
- **Uploaded resume file** (PDF/DOCX): what the employer downloads. Can coexist with
  the Indeed Resume; keep both consistent with the master resume.
- **Preferences**: job titles (normalized list - pick from suggestions), job types,
  work schedule, minimum pay, remote/relocation, work area.
- **Qualifications / matching data**: skills, credentials (catalog only), education.
- **Work authorization** per country.
- **Demographics**: sensitive - never touch; it is the user's decision.
- Account country sets the site (`www`, `uk`, `de`, ...) and currency.

## 3. Audit checklist (score each 0-5)

**Search**
- Resume is searchable; the "Employers can find you" switch is on (if the user wants
  to be found) and contact details are current.
- Headline: target title + core stack + years, in plain words.
- Preferences: up to the allowed number of desired job titles, covering the standard
  variants of the target role (use Indeed's normalized titles); job types; remote
  setting; minimum pay consistent with `candidate.md`; relocation.
- Skills in the Indeed Resume: complete and named as in job postings; inferred skills
  that do not fit are removed from matching data.
- Work authorization filled for the countries the user can really work in; blank
  where the answer would be "no" or needs sponsorship, unless the user decides
  otherwise.
- Profile updated in the last 30 days (recency) - a real improvement, not a fake
  edit.

**Skim**
- Summary: 3-5 lines, same message as the resume summary, numbers included.
- Work experience: same titles/dates as the master resume; 3-6 bullets for recent
  roles; no walls of text.
- Uploaded resume file is the current ATS-safe PDF with a descriptive file name.

**Trust**
- Indeed Resume, uploaded file and LinkedIn tell the same story (titles, dates).
- Certifications listed (in the resume's certifications section when the credential
  catalog does not have them), education, languages with levels.
- A link to LinkedIn or portfolio in the resume's Links section.

## 4. Adding items - what to collect

- **Certification / license:** name, issuer, issue and expiry dates. The
  "Credentials" page accepts only items from Indeed's catalog; courses and vendor
  certificates that are not in it go into the Indeed Resume → Certifications and
  licenses section instead. Say which place was used.
- **Work experience:** title, company, location, from/to (month/year), currently
  working, description.
- **Skill:** name (choose the suggestion), optionally years of experience.
- **Education, language (with level), link, additional information.**
- After a significant change, the uploaded resume **file** is outdated too: offer to
  rebuild the general resume with `/resume-tailor base` (it applies the disclosure
  rules and the length limit and writes to `career/resume/`), show it to the user,
  and replace the file on Indeed only after their yes.

## 5. UI quirks

- Edit forms are dialogs. **Escape closes the whole dialog and loses the edit** -
  do not use Escape to dismiss an autocomplete list; click elsewhere inside the form.
- Inputs are React-controlled: setting the value programmatically needs a real input
  event, otherwise the form saves the old value. Verify after saving.
- Month/year pickers are button + option lists, not native selects. Later months are
  below the fold of the list - scroll the option into view before clicking it.
- Built resume editor: profile home → the "Indeed Resume" item → "Edit resume" →
  section list on the left. A certification is added at
  `/resume/certifications/add`: name (free text; follow the naming already used in
  the section, for example "Name (Issuer)"), issued month and year, "Does not expire"
  (hides the expiry fields) and a description line. After typing the name, click a
  neutral spot in the form to close the suggestion list before opening a picker.
- After each save the section list shows the new entry first; the reliable check is
  to reload the section page and read all entries back.
- The headline is edited on the "About you" form (the Edit control next to the name on
  the profile home, `/edit/contact`), together with name, phone and location. Change
  only the headline. The form has a box "Show my number on Indeed" tied to a consent
  to calls and messages: read its state, never tick it, and tell the user it is there.
- A work experience entry is edited from the resume editor's "Work experience"
  section; the form also has a Delete button next to Save - click Save by its label.
- File upload: the file input appears only after the upload control is activated.
  Activate it from a page script rather than a real click (a real click opens the
  native file picker, which cannot be operated); then give the file to that input
  with the extension's file upload.
- Replacing the uploaded file: the file's options menu → "Replace file" → a
  confirmation that the current file will be deleted → the file input appears → after
  the upload a "Review your resume" page shows the parsed text → "Save resume". The
  old file stays until the new one is saved. Read the review page before saving: it
  must show the new content.
- Job titles and skills must be picked from suggestions; titles that are not in the
  normalized list cannot be added (choose the closest standard title and tell the
  user).
- Cloudflare / "additional verification" pages appear, especially on job pages
  (`viewjob`). Do not try to pass them; ask the user to pass the check in the tab,
  or use the search page's side pane (`vjk=`) to read a description.
- Boolean `OR` queries in job search are unreliable; run separate searches.

## 6. Things only the user can do

Demographic questions, phone/e-mail verification codes, security checks, deciding
whether to be visible to employers and whether to show "ready to work".
