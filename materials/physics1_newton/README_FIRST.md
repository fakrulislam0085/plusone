# PlusOne | Physics I Newton's Laws demo content

This is **educational content**, not a finished PlusOne application. It is an original teaching sample supported by real textbook sections, intended for the AI-on-Campus case study. **Not an official Politecnico di Torino handout.**

## Open these first

1. `01_Newtons_Laws_Student_Handout.pdf` - short course material with original diagrams and one worked example.
2. `02_Newtons_Laws_Diagnostic_Quiz.pdf` - student-facing diagnostic (8 MCQ + 2 written questions).
3. `03_Instructor_Key_and_Facilitation.pdf` - correct answers, misconception flags, discussion questions, transfer checks. **Do not expose to student-side retrieval.**
4. `course_manifest.json` - source references, outcomes and misconceptions.
5. `quiz_student.json` - quiz content with no answers.
6. `quiz_instructor_key.json` - instructor-only answers and criterion-based written-response checks.
7. `group_discussion_prompts.json` - three short collaborative-learning tasks.
8. `synthetic_group_demo.json` - four synthetic students and a PlusOne agent boundary scenario.
9. `AGENT_EVALUATION.md` - minimum acceptance checks for the live demo.

## Suggested PlusOne demo flow

Professor loads the **student handout and a real source section**. Student individually answers Q01 and Q07. Agent stores a tentative misconception signal (not a definitive diagnosis), triggers G01 or G02 group discussion, asks peers to reason, and records which turn supports the teacher-facing summary. Students then take T01 or T03 individually.

## Grounding and disclosure

- Written examples and diagrams in this pack are original. Underlying first-year concepts and source section links come from OpenStax University Physics Volume 1, Chapter 5 (CC BY 4.0), listed in `course_manifest.json`.
- Do not describe this as actual Polito professor-provided lecture notes. If you can obtain course slides or exercises with permission, load those as additional first-party university material.
- The group transcript is **synthetic demonstration data**. Do not pass it off as genuine students or empirical results.
- Do not expose the answer key to the student chat agent before independent attempts, and never claim learning improvement from one quiz.

## Retrieval segregation

`student_documents = [student handout, quiz_student.json, group_discussion_prompts.json]`

`instructor_documents = [quiz_instructor_key.json, instructor PDF]`

## Physics assumptions

SI units; g = 9.81 m/s², inertial frame, negligible air resistance when stated. All 8 MCQ keys were independently checked and open-response criteria include reasoning rather than keyword matching.
