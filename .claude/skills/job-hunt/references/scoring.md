# Filtering and scoring

Two stages: **hard filters** decide whether a vacancy is shown at all; the **score**
ranks what is left. Keep them separate - a perfect stack match the candidate cannot
legally take is not an 80, it is excluded.

## Stage 1 - hard filters (from `candidate.md`)

Exclude, with a short reason, when the posting clearly states any of:

- location or work-authorization requirements the candidate does not meet
  (single-country remote, citizenship/clearance, "EU residents only", required
  relocation, hybrid/on-site when the candidate is remote-only);
- an employer, country, market or industry on the candidate's exclusion list. Judge
  this by the employer itself, not only by what the posting says: take the company's
  country from the card, its company page on the board, or one quick lookup, and
  exclude when it is on the list. If the country cannot be established, show the
  vacancy under "Needs checking" and say so;
- a required language the candidate does not have at the needed level;
- seniority far from target (internship/junior for a senior, or the reverse);
- pay stated and clearly below the candidate's floor;
- not actually the candidate's profession (same keyword, different field);
- closed, expired, or older than the freshness window; duplicates.

If the text is **silent or ambiguous** about eligibility ("Remote", no countries),
do not exclude and do not assume: put it under "Needs checking" and cap the score at
69. Say exactly what must be clarified (for example "contractors outside the EU?").

Exception - national boards. A posting on a job board of the candidate's own country
(for a candidate in Ukraine: DOU and Djinni) that names no location restriction is
taken as open to that country: no cap, no "needs checking" for eligibility.

Apply the candidate's preferences exactly as written in `candidate.md`, including
the ones that widen the search rather than narrow it.

## Stage 2 - score (0-100)

| Component | Points | How to judge |
|---|---|---|
| Role and seniority | 25 | Title and responsibilities match a target role at the right level (25); adjacent role or one level off (12-18); stretch (≤10) |
| Stack and requirements | 30 | Share of **must-have** requirements covered by the candidate's *confirmed* skills. All: 30. Each missing must-have: −5 to −8 depending on how central it is. Nice-to-haves add up to +3, never above 30 |
| Eligibility and terms | 20 | Explicitly open to the candidate's country and contract type (10); employment type and schedule fit preferences (5); pay stated and at/above target (5), not stated (2), below target but above floor (1) |
| Domain | 10 | One of the candidate's interest domains or a domain they have worked in (8-10); neutral (5); a domain they would rather avoid (0-2) |
| Edge | 15 | The role wants the candidate's differentiators (from `candidate.md`), offers growth they are looking for, or the company quality is evidently high (product, funded, good reviews). Evidence required for each point |

Rules:

- Count a skill as covered only if it is in the confirmed skills of the master
  files. Skills on the "do not claim" list count as missing even if related.
- Years-of-experience requirements: within 1 year short is fine; more is a
  missing must-have.
- Do not reward keyword overlap by itself; a posting that lists 30 technologies is
  judged on its real must-haves.
- Stay calibrated: most postings land between 40 and 75. A score above 85 means
  "apply today".

## Labels

| Score | Label | Where it goes |
|---|---|---|
| 85-100 | strong | Recommended |
| 70-84 | good | Recommended |
| 55-69 | worth a look | Recommended (lower part) or Needs checking |
| < 55 | weak | Screened out, one line |

## One-line rationale

For each recommended vacancy write: the two strongest matches, then the main gap or
risk. Example: "Senior role on a B2B product, design-system ownership · needs
motion design (gap), salary not stated".
