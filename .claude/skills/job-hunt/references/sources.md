# Job boards - search patterns and quirks

URL parameters are the fastest way to apply filters, but boards change them. Treat
each pattern as a starting point: after loading, confirm on the page that the filters
are really applied (remote, date, sort). If a parameter stopped working, set the
filter through the page UI and note the new URL in the run notes.

`<q>` = URL-encoded query, for example `Product%20Designer`.

Public boards (readable without the user's session, also through a plain web fetch or
RSS): DOU and Djinni. LinkedIn needs the signed-in session; Indeed works without one
but shows security checks more often.

## LinkedIn (needs the user's signed-in session)

Checked live in November 2026: job search runs on a new page with "AI search". The
old `/jobs/search/` address still opens but redirects and silently drops `location`,
`f_WT` and `sortBy`.

- Search: `https://www.linkedin.com/jobs/search-results/?keywords=<q>&geoId=<geo>&f_TPR=r604800`
  - `geoId`: the location. Ukraine `102264497`, EMEA `91000007`. For any other place
    choose it in the location dropdown next to the result count and copy the `geoId`
    the site puts in the address.
  - `f_TPR=r604800` last 7 days (`r86400` 24 h, `r1209600` 14 days, `r2592000` 30).
  - Remote: click the "Remote" chip once and reuse the parameter the site adds to the
    address (observed: `f_SAL=f_SA_id_225001%3A272001`). `f_WT=2` no longer works.
  - There is no sort parameter; the time window does the job.
- Always read the header line "N results <place>" and the active chips: they show
  whether location, date and Remote were really applied.
- The result list is plain text: title, company, location, age. **Cards carry no job
  ID and no link.** The ID appears only for the opened card - as `currentJobId` in
  the address and as a `/jobs/view/<id>/` link in the detail pane. To open one
  specific card without clicking through the list, search for its title plus company
  (`keywords=<title> <company>`): it comes up first and is opened automatically.
- Below the exact matches LinkedIn adds "more results that may not be exact matches"
  - judge those by title as usual.
- The location line ("Ukraine (Remote)", "Brno (Remote)") is the employer's
  eligibility scope: remote *within that place*. A regional scope such as EMEA mostly
  returns single-country remote roles.
- "Reposted" means an older vacancy - keep it but say so.
- Do not use Easy Apply, Save, or follow buttons.

## Indeed (session optional; country sites differ)

- Search: `https://<cc>.indeed.com/jobs?q=<q>&l=<location or Remote>&fromage=7&sort=date`
  - `<cc>`: `www` (US), `uk`, `de`, `nl`, `ca`, `ie`, ... Pick the sites that match
    the candidate's eligibility and exclusions in `candidate.md`.
  - `fromage=7` last 7 days (1, 3, 7, 14).
  - Remote filter: the "Remote" chip in the UI (it adds an `sc=` parameter that is
    not stable - click the chip rather than hard-coding it).
- Job ID: `jk=<16 hex chars>` in card links; canonical link
  `https://<cc>.indeed.com/viewjob?jk=<jk>`.
- Opening `viewjob` pages often triggers a Cloudflare check. Read descriptions in
  the search page's side pane instead: click the card (URL gets `vjk=<jk>`), then
  read the pane's text.
- If the whole site shows "additional verification", skip it this run and note it;
  it usually works after the user passes the check once by hand.
- "Remote in <city>" means remote within that area. US postings are typically W2 /
  US-authorization only unless they say otherwise.
- Boolean `OR` is unreliable - run separate queries.
- Ignore sponsored cards with placeholder-looking keys.

## DOU (jobs.dou.ua - public, Ukrainian market)

- List: `https://jobs.dou.ua/vacancies/?category=<Category>&exp=<exp>&remote`
  - categories as in the site's dropdown (e.g. `Design`, `Project Manager`, `.NET`,
    `Front End`, `DevOps`, `AI/ML`, `QA`); `exp`: `0-1`, `1-3`, `3-5`, `5plus`;
    `remote` flag = remote; `city=<City>` for offices.
  - Free-text: `https://jobs.dou.ua/vacancies/?search=<q>`
- The list loads ~20 items with a "more vacancies" button ("Більше вакансій"); items are newest first
  with a date on each card. Stop when dates fall outside the window.
- The card date is the date of the latest re-publication. Vacancy IDs grow over time,
  so an ID far below its neighbours is an old vacancy that was bumped - keep it, but
  mark it "republished".
- Job ID: the number at the end of `/companies/<company>/vacancies/<id>/`.
- RSS for a quick first pass (if a fetch tool is available):
  `https://jobs.dou.ua/vacancies/feeds/?category=<Category>&remote`
- Postings are in Ukrainian or English; salary is shown when the employer gives it.
  The company page on DOU has reviews and size - useful for the "company type".

## Djinni (djinni.co - Ukrainian market, salary-transparent; public)

- Search: `https://djinni.co/jobs/?primary_keyword=<Category>&employment=remote&exp_level=<exp>`
  - `primary_keyword`: the site's own category key. Keys are not always the visible
    label, and an unknown key is **silently ignored** - the site then returns the
    unfiltered list. Pick the specialization in the page's filter once, copy the
    value the site puts in the URL, and reuse it (repeat the parameter for several
    categories).
  - `exp_level`: `no_exp`, `1y`, `2y`, `3y`, `5y`, ... - an **exact** value ("5
    years required"), not "at least": for an experienced candidate leave it out and
    read the experience from the card, otherwise most roles disappear;
  - `employment=remote`; `english_level=`; `salary=<min USD>`;
  - location scope: `region=` with `UKR`, `eu`, `other` or `worldwide`; a specific
    country through `country=`;
  - free text: `all_keywords=<q>` (underscore), or the search box.
- After loading, compare the result count and the active filter chips with what was
  asked for. A count in the thousands means a parameter was ignored.
- There is no date filter. The list is newest first: read down and stop at the first
  card older than the freshness window.
- Job ID: the number in `/jobs/<id>-<slug>/`. A vacancy page does **not** open by ID
  alone (`/jobs/<id>/` returns 404) - take the full link from the card.
- Observed category keys: `QA Automation` works as written; `QA` means "QA Manual".
- Cards show salary range, experience, English level, company type (product /
  outsource / outstaff / agency), views and applications - capture salary and type.
- Some details and salary filters may need the user's signed-in candidate account;
  if a login wall appears, read what is public and note it.
- RSS: `https://djinni.co/jobs/rss/?primary_keyword=<Category>`
- Do not press "Apply" ("Відгукнутись").

## Reading pages with the browser tools

- Take every card's own link while reading the result list; several boards cannot be
  opened from an ID.
- Check `seen.json` before opening a description, not after.
- A page script returns only about 1 KB per call and refuses output that looks like a
  URL query string, so it suits compact card lists. For a description that may be
  recommended, use the page-text tool, which returns the whole posting.
- Avoid scroll actions that return a screenshot each time; load lazy lists with a
  script or the page-text tool.

## Building queries for any board

- Use standard titles recruiters post under, not internal ones. Cover synonyms in
  separate queries (e.g. "Product Designer", "UX Designer", "UI/UX Designer").
- Add 1-2 skill- or niche-based queries from the candidate's differentiators and
  interest domains - they find well-matched roles under unusual titles.
- On category-based boards (DOU, Djinni) the category + experience + remote filters
  do most of the work; free-text queries are a supplement.
- Note queries that return nothing useful several runs in a row and drop them.
