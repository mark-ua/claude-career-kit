# LinkedIn - mechanics and audit checklist

LinkedIn changes its UI and limits often. Treat the numbers and paths here as "true
when written"; if the page disagrees, trust the page and note the difference in the
changelog.

## Contents
1. How recruiters find profiles
2. Sections, limits, weight
3. Audit checklist
4. Adding items (field lists)
5. Edit paths
6. UI quirks
7. Things only the user can do

## 1. How recruiters find profiles

- Recruiter search filters and ranks mainly on: **job titles** (current and past),
  **skills**, **location**, years of experience, **Open to Work** status, and how
  likely the person is to respond (activity, recent updates).
- Keyword search reads the headline, About, experience titles and descriptions,
  skills, projects and certifications. Titles and skills weigh more than free text.
- AI-assisted recruiter search (natural-language queries, automated shortlists) reads
  the profile semantically. It rewards clear statements of *what was done, with what,
  at what scale* and skills that are attached to specific positions - not keyword
  lists.
- In search results the recruiter sees only: photo, name, headline, current title and
  company, location, and a snippet. That line decides the click.

## 2. Sections, limits, weight

| Section | Limit (approx.) | Notes |
|---|---|---|
| Headline | 220 chars | Highest-weight free text. First ~60-70 chars show in search results and on mobile |
| About | 2,600 chars | First ~3 lines visible before "see more"; put the value statement there |
| Position title | 100 chars | Matched against recruiter title filters; standard titles are found, creative ones are not |
| Position description | 2,000 chars | Bullets with numbers; first two lines visible by default |
| Skills | up to 100 | Up to 5 pinned in About ("Top skills"); each skill can be linked to positions, projects, certificates |
| Projects | description 2,000 | Good carrier for keywords and proofs; can be associated with a position |
| Licenses & certifications | - | Name, issuer, dates, credential ID/URL, linked skills |
| Featured | - | For conversion (proof for a human), not ranking |
| Recommendations | - | Trust signal; 2-3 recent ones from manager/peer/report |
| Custom URL | 3-100 chars | Short, name-based |

## 3. Audit checklist (score each 0-5)

**Search**
- Headline contains the target job title in its standard form and 2-3 core hard
  skills; the most important words are in the first 60 characters.
- Current position title uses a standard, searchable title (a slash can carry two
  real variants: "Delivery Lead / Engineering Manager"). Official titles are not falsified.
- Every target keyword from `candidate.md` appears in at least two of: headline,
  About, experience, skills. No keyword walls.
- Skills: every skill the candidate can back up for the target role (for an
  experienced specialist that is usually a few dozen - never padded to reach a
  number), named the way LinkedIn's catalog and job postings name them; the 5 pinned
  ones match the target role; each key skill is linked to at least one position or
  project where it was really used; outdated/irrelevant skills removed (keep
  well-endorsed ones unless the user agrees).
- Location is set to a real, searchable city/region; industry is set.
- Open to Work: configured with target titles (up to 5), work types (remote etc.),
  locations, start date. For someone employed, "Recruiters only" visibility is the
  usual choice - confirm with the user, never switch on the public photo frame
  without asking. Tell them LinkedIn tries to hide this status from recruiters at
  their current company but does not guarantee it.
- Profile language matches the target market; a second-language profile only if the
  user targets that market.

**Skim**
- Photo and banner present and professional (assessable only visually; ask the user
  if unsure).
- About: opens with who/what/for whom in two lines; then proofs with numbers; ends
  with what the person is open to and how to reach them. Short paragraphs or bullets.
- Each recent role: one line of context (product, team size) + 3-6 bullets with
  measurable results. Old roles short.
- No leftover jargon, typos, or text that sounds machine-written.

**Trust**
- Titles, employers and dates match the resume in `master-resume.json`.
- Certificates with credential links; education filled.
- At least 2 recommendations in the last 2-3 years.
- Identity/workplace verification badge if available in the user's country.
- Contact info: e-mail visible to recruiters; custom URL set.
- Some recent activity (a post or thoughtful comments in the last month).

## 4. Adding items - what to collect

- **Certification:** name (exact), issuing organization (pick the company page from
  the dropdown), issue month + year, expiration (or none), credential ID, credential
  URL, skills to link (up to the form's limit).
- **Position:** title, employment type, company (from the dropdown), start/end,
  location and location type (on-site/hybrid/remote), description, skills,
  "currently working here". Ending a position and adding a new one are separate
  edits. Ask whether to update the headline.
- **Skill:** exact catalog name; where it was used (link to positions/projects).
- **Project:** name, dates, description, associated position, skills, link.
- **Course / education / language / volunteering:** as the form asks.

Every add/edit form has a **"Notify network" / "Share with network"** toggle. Turn
it off unless the user wants the announcement - and ask when the fact is worth
announcing (a new certification or job often is).

## 5. Edit paths

`<slug>` is the part after `/in/` in the profile URL.

- Profile: `https://www.linkedin.com/in/<slug>/`
- Detail pages: `/in/<slug>/details/experience/`, `/details/skills/`,
  `/details/certifications/`, `/details/projects/`, `/details/education/`,
  `/details/recommendations/`
- Edit forms open as overlays from the pencil / "+" icons on those pages. Direct
  form URLs exist (for example `/in/<slug>/edit/forms/certification/new/`) but
  change over time - if one does not open, use the "+" on the detail page or
  "Add profile section" on the profile.
- Open to Work: the "Open to" button under the headline → "Finding a new job".
- Analytics: `https://www.linkedin.com/analytics/profile-views/` and
  `/analytics/search-appearances/`, or the Analytics block on the profile.
- Public profile & URL settings: `https://www.linkedin.com/public-profile/settings`.

## 6. UI quirks

- Typed text sometimes loses characters in LinkedIn's editors. After saving, read the
  field back from the reloaded page and compare with the approved text.
- Type short fields normally. For a long text (About, a position description), if
  typing loses characters, set that one field's value in a single operation and then
  type and delete a space so the Save button activates. This is a fallback for one
  field at a time, never a loop over several fields or pages.
- Line breaks: use plain newlines; LinkedIn strips formatting. Simple "•" or "-"
  bullets survive; fancy Unicode fonts hurt search and screen readers.
- Dropdown fields (company, issuer, skills) need a choice from the suggestions; free
  text creates an unlinked entry without a logo.
- Headline, name, location and industry are on the "Edit intro" form
  (`/in/<slug>/edit/intro/`). The headline is an editable text block, not an input:
  click into it, select all, type, then read the focused element's text back before
  pressing Save. Leave the other fields alone.
- A skill is added at `/in/<slug>/skills/edit/forms/new/`: type the name, pick the
  exact entry from the suggestion list, then Save. The form ticks "Follow this
  skill" by default - untick it unless the user wants to follow the topic - and
  offers "where you used this skill" boxes: tick only what the user confirmed. After
  saving LinkedIn offers to add another skill; open the form again for the next one.
  Newly added skills appear first on the skills page, which makes them easy to verify.
- Lists that load while scrolling (skills, certifications) load the next chunk only
  on a real scroll of the page, not on a scripted one; each chunk is about ten items.
- On the profile page the sections below Activity (experience, education,
  certifications, projects, skills) may not be rendered until they are scrolled into
  view. Read them from their detail pages instead.
- Skill reordering and pinning are drag-or-menu actions on the skills detail page.
- The skills detail page loads in chunks while scrolling. Keep loading until the
  spinner at the bottom is gone, and say in the snapshot if the list may be
  incomplete - do not report a skill as missing from a partial list.
- Open to Work, seen on one's own profile: when it is on, a card with the chosen
  titles sits under the headline; when only the "Open to" button is there, it is off.
  Read this from the profile; do not open the dialog just to check.
- Overlays occasionally fail to load; reload the page once before concluding
  something is wrong.
- If a "premium" upsell or a security check appears, stop and tell the user.

## 7. Things only the user can do

Requesting recommendations, identity verification, choosing a photo, writing posts in
their own voice (drafts can be offered), deciding on the public Open to Work frame,
accepting any new terms.
