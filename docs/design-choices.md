# Key design choices (and why)

| Choice | Why | Alternative we rejected |
|---|---|---|
| **The student teaches; the AI is the confused one** | Explaining is how you find out what you really know (learning by teaching). An AI that *can't* give the answer can't think for you | An AI tutor that explains: faster, but it thinks *for* the student |
| **Matteo plants only catalogued misconceptions** | Grounded and safe: he never invents fake physics, and every planted error maps to something the professor recognises | Free-form "be confused": unpredictable, and can teach wrong ideas that nobody tracks |
| **Group mode: Matteo hands questions to peers** | Takes PlusOne's peer-learning idea while avoiding its main risk: students asking the AI instead of each other. Matteo has no answer to give | AI as a knowledgeable fifth team member: becomes the answer machine |
| **Two agents with split roles** (Matteo talks, the Examiner judges silently) | The judge never talks and the talker never judges, so assessment can't leak into the conversation | One agent that both chats and scores |
| **The graph decides the root cause, not the LLM** | Explainable and checkable; a professor can fix an edge without touching a prompt | Asking the LLM "why is the student stuck?" |
| **Guardrail in code**, not only in the prompt | "A prompt can be talked around; a check in code cannot." Blocklist, 80-word cap and a calculation detector; regenerate once, then a canned question | Prompt-only refusal |
| **Hypotheses, not grades** | Short chat answers are weak evidence. A weak spot needs two consistent observations; no % mastery, no ability labels | Dashboards with "student understands 80%" |
| **Professor approves or rejects every flag** | Human in the loop; the AI proposes, a person decides. Rejections are logged | Automatic reports to the professor |
| **Anonymized flags** (no names, no quotes) | Students must feel safe being wrong; the professor needs patterns, not people | Per-student reports |
| **No grouping by grades** (cut from PlusOne v1) | Labels students and excludes them, which is exactly the judges' "who is left out?" question | AI-formed groups from grades |
| **Text-first, IT/EN** | Works for shy students and without voice; Matteo answers in the student's language | Voice-only |
| **Opus 5.5, Examiner at low effort, Matteo at medium** | Measured: low gives the Examiner the same verdicts, faster; Matteo at low sometimes stopped asking questions | Sonnet (cheaper, but we prioritised quality for a live demo) |
| **Streamlit, local, JSON files** | A working demo by 14:30 beats a perfect architecture; no login, no database | A full web stack |

## Prompts (deliverables, versioned in git)
`prompts/matteo.md` and `prompts/examiner.md` follow Reply's structure: **ROLE · GOAL · KNOWLEDGE · RULES · PROCEDURE · MEMORY**. Each turn, code appends a hidden brief to Matteo's prompt: the probe, the planted misconception, the peer to ask, and whether the student asked for the answer or went off-topic.
