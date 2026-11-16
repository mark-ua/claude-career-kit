# Trends: durable baseline + how to refresh

Recruiting tools change every few months, so advice is split in two:

- **This file** - principles that have held for years and are unlikely to flip.
- **`career/trends.md`** - a dated, sourced note of what is current *right now*,
  refreshed by web research at most once every 30 days. `profile-upgrade` and
  `resume-tailor` both read it and either may refresh it with the procedure below;
  `profile-review` reads only its general sections and never writes it (the file is
  about the user's own search); `job-hunt` does not use it.

## Refreshing `career/trends.md`

Do this when the file is missing, older than 30 days, or the user asks for the latest.

1. Run 4-6 focused web searches for the current year, for example:
   - LinkedIn Recruiter search / ranking changes, new profile features, Open to Work,
     verification, skills
   - Indeed employer resume search / Smart Sourcing / matching changes
   - ATS parsing and AI screening changes (Workday, Greenhouse, Lever, Ashby, iCIMS,
     SmartRecruiters), resume format guidance
   - recruiter surveys: what they look at first, attitudes to AI-written profiles
     and resumes
   - hiring demand in the candidate's field (skills in demand for the target roles
     in `candidate.md`)
2. Prefer primary sources: LinkedIn Help / Talent Blog / Engineering Blog, Indeed
   employer help and product pages, ATS vendor documentation and release notes,
   original surveys. SEO blogs and "resume scanner" vendors exaggerate (the claim
   that "75% of resumes are rejected by ATS before a human sees them" has no solid
   source) - use them only as leads, and label unverified claims as unverified.
3. Write `career/trends.md`:

```markdown
# Recruiting trends - refreshed <YYYY-MM-DD>

## What changed since the last refresh
- ...

## LinkedIn
- claim - source URL (date) - confidence: high / medium / unverified

## Indeed
## ATS and AI screening
## What recruiters respond to
## In-demand skills for <target roles>

## Implications for this candidate
- 3-6 concrete actions
```

4. Keep it under ~80 lines. Replace the file each time; do not let it grow.

If web search is unavailable, say so, use this baseline, and tell the user that the
trend check was skipped.

## Durable baseline

**Findability**
- Search is title- and skill-driven. Standard job titles and hard skills, named the
  way postings name them, in the highest-weight fields.
- Skills-first hiring keeps growing: structured skills (LinkedIn skills linked to
  positions, Indeed matching data) are filtered on directly. Skills only mentioned
  in prose are weaker.
- Completeness and recency are ranking inputs on both platforms. Recency should come
  from real additions (a result, a skill, a certificate, a project, a post) every few
  weeks; the headline and job titles stay stable unless the target role changes.
- Availability signals (Open to Work for recruiters, Indeed preferences) put the
  profile into more searches and raise outreach.
- AI-assisted sourcing reads meaning, not just strings: clear statements of scope,
  tools and outcomes are matched better than keyword lists. Stuffing does not help
  and hurts the human read.

**ATS reality**
- Most ATS do not auto-reject on a "score"; people search, filter and skim parsed
  data, and knock-out questions do the automatic rejecting. AI ranking is spreading,
  so both exact terms and clear context matter.
- Parseable format wins: single column, standard headings, text-based PDF or DOCX,
  no tables/columns/text boxes/images, contact info in the body, consistent dates.
- Spell out an acronym once next to its abbreviation so either search term matches.

**Human response**
- A recruiter decides in seconds from the top of the profile/resume. The match with
  the target role must be visible there.
- Numbers and scope (team size, volumes, percentages, time saved) are what get
  quoted to hiring managers.
- Consistency across LinkedIn, Indeed and the resume is checked; mismatched dates or
  titles are a red flag.
- Trust signals carry more weight as fake and AI-generated profiles multiply:
  verification, credential links, recommendations, a real activity trail, and
  specific, human-sounding text.
- Demonstrated AI fluency (what was built or automated with AI, the result, and how
  a human stays in control) is a strong differentiator in most tech roles.

**Do not**
- Hide keywords, list skills the person lacks, use fancy Unicode fonts or emoji
  walls, copy the job description into the profile, or change titles to ones never
  held.
