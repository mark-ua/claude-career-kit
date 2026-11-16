# Mock interview

Run only when the user asks. Base it on the application folder for that vacancy
(`vacancy.md`, `fit-analysis.md`, `resume.json`, `prep.md`). If the request does not
name the vacancy, list the folders in `career/applications/` and ask which one. If
the folder or any of these four files is missing, run the main workflow first
(steps 1-6) - the interview is built on all of them.

Ask (or infer from the request) which format the user wants:

## Format A - prepared sheet (`interview.md`)

A question bank with model answers the candidate can rehearse.

- 20-30 questions grouped by stage:
  1. Recruiter screen - motivation, why this company, why this move now,
     location and contract, salary, availability
  2. Technical - from the posting's must-haves and the stack; include 3-5 questions
     on the candidate's gaps, because those are the ones that hurt
  3. Practical - a scenario or case typical for the role (design an approach for X,
     diagnose Y, review this solution), with a worked solution outline
  4. Behavioral / leadership - conflict, failure, prioritization, influence
  5. Resume probes - questions a careful interviewer would ask about this exact
     resume: big numbers, short tenures, title changes, gaps
  6. Their questions to the company
- For each question:
  - **Why they ask** - one line
  - **Model answer** - in the first person, built only from the candidate's real
    experience (STAR for behavioral: situation, task, action, result), 60-120 seconds
    when spoken
  - **Watch out** - a common trap or the disclosure rule that applies
- For gap questions, give an honest answer pattern: what the candidate knows that is
  adjacent, how they would close the gap, and never a bluff.
- Mark the 8-10 most probable questions with a star.

Write it in the interview language (the posting's language); add short notes in the
user's language where helpful.

## Format B - live session

Play the interviewer for a specific stage (ask which; default: technical with the
hiring manager).

- Introduce yourself in role in one line and state the stage and length
  (default 8-10 questions).
- Ask **one question at a time** and wait for the answer. Do not show the model
  answer first.
- After each answer, give feedback in a compact block:
  - what worked;
  - what was missing or risky (accuracy, structure, length, a claim beyond the
    resume);
  - a stronger version of the answer using the candidate's own facts;
  - a score 1-5.
  Then ask one realistic follow-up if the answer invites it, or move on.
- Mix difficulty: start easy, include at least two gap questions and one resume probe.
- If the user wants a no-interruptions run, hold feedback until the end.
- Finish with a debrief: overall score, the three strongest answers, the three topics
  to work on (link to the "Learn"/"Refresh" items in `prep.md`), and filler habits
  noticed (too long, no numbers, vague "we").
- Offer to save the transcript with feedback to `interview-session-<date>.md` in the
  application folder.

## Rules for both formats

- Answers use only real facts from the master files; the disclosure rules apply to
  spoken answers too - prepare a polite line for "which client was that?".
- Be a realistic interviewer, not a cheerleader: honest scores help more than praise.
- Salary questions: use the target from `candidate.md`; rehearse one clear sentence
  and one fallback.
