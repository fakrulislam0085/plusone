# Matteo: Reply Student Tech Clash 2026 (AI on Campus), PoliTO

Hackathon TODAY (Sat 7 Nov 2026). The first jury evaluation is around **15:00–16:00**, so we need to be **demo-ready by 14:30**. Speed and a demo that never breaks matter more than elegance. Full challenge brief: `docs/challenge-brief.md`. Team-facing idea page: `docs/idea-overview.html`.

## The challenge (Reply brief, short)
- Mission: pick a real problem in learning/teaching/assessment and design an AI-based solution. Out of scope: admin/logistics.
- Level 1 (required): idea + 60-second pitch (no slides). Level 2 (required): a working agent that DOES something beyond replying and holds its boundary (helps the student think, never thinks for them).
- Level 3 (optional): Knowledge Graph (path B) + Launch campaign (path C). We do NOT build Reply's Problem-Identifier/Solver multi-agent spec.
- Scoring: Creativity & Innovation 40%, Impact 20%, Technical 20%, Presentation 20%. Judge questions: new or just faster? Helps think or thinks for them? Who benefits / who is left out?

## The idea: Matteo (app name = the AI classmate's name)
Students learn Physics I by **teaching Matteo**, a confused AI freshman (*matricola*). They teach him alone or **as a study group** (Matteo is the "+1" member).
- Matteo asks naive questions, plants real misconceptions (only from our catalogue), and NEVER gives answers. If asked for the answer: "I don't know, that's why I'm asking you!" In group mode he turns the question back to the peers ("Bea, do you agree with Alex?").
- The **Examiner** silently scores each explanation against the Physics I concept graph, updates that student's mastery, and the code traces the root cause through prerequisites ("You struggle with the 3rd law because it requires force-as-interaction, and your free-body explanation was shaky", with a source).
- **Professor in the loop:** the professor provides the material and approves the topic. Concepts students fail are flagged (anonymized) to the professor, whose view shows where the class breaks.
- No overclaiming: a weak concept is a *hypothesis (needs confirmation)* until there is a second piece of evidence. Never report "X% mastery" or ability labels. No grouping by grades.
- Scope: ONE course, ONE topic: **Physics I, Newton's laws** (first law, net force, second law, third-law pairs, free-body diagrams, friction, simple incline). About 13 concepts.
- Demo language: English (Matteo replies in the student's language: Italian or English).

## Material (`materials/physics1_newton/`)
- Original demo pack aligned with **OpenStax University Physics Vol. 1, Ch. 5 (CC BY 4.0)**. It is NOT official PoliTO notes: say so honestly.
- `course_manifest.json` holds the learning outcomes LO1–LO6, the 12 misconception IDs (e.g. `MOTION_NEEDS_FORCE`, `THIRD_LAW_UNEQUAL`) and the source references OS-5.1…OS-5.7.
- `handout_for_rag.md` is the student-safe content. `group_discussion_prompts.json` has G01–G03. `synthetic_group_demo.json` has Alex/Bea/Chris/Dani (synthetic: label it).
- **Retrieval segregation:** `quiz_instructor_key.json` and `03_Instructor_Key_*.pdf` must NEVER reach Matteo's context. Only deterministic code (scoring a check question) may read the key.

## Tech stack (keep it simple)
- Python 3.13, Streamlit UI, single repo, `.venv`. Run: `.venv\Scripts\streamlit run app/main.py`.
- LLM: all calls go through `app/llm.py` (`chat(system, messages, json=False, effort=...)`). Provider is Anthropic, model from env `MODEL` (default `claude-opus-5-5`), effort `medium` by default. Thinking is always on in Opus 5.5 (do not send `budget_tokens` or `disabled`). Server-side refusal fallback is enabled. It must stay swappable to another provider by editing only `llm.py`.
- Key in `.env` (`ANTHROPIC_API_KEY`, no BOM), loaded with python-dotenv from the repo root. `.env` is in `.gitignore`.
- Graph: `data/graph.json` loaded into networkx, visualised with pyvis via `streamlit.components.v1.html`.
- Memory: `data/students/<student_id>.json` (mastery per concept with status, misconceptions seen, history summary).
- Lecturer flags: `data/lecturer_flags.json`.
- Logs: every step appended to `logs/session.jsonl` (timestamp, step, input, output). These are our testing evidence.

## Architecture (matches Reply's reference: orchestrator + LLM + tools + memory + guardrails + logs)
Per student turn, `app/orchestrator.py`:
1. Examiner call (`prompts/examiner.md`) returns strict JSON (validated with pydantic; retry once on invalid JSON). The schema in `prompts/examiner.md` is the source of truth. The Examiner does NOT compute the root cause; code does it from `struggling_concept_id`.
2. Tools (plain Python functions, the agent's actions):
   - `update_mastery(student_id, concept_id, score, evidence)` writes the memory file.
   - `trace_root_cause(student_id, concept_id)` walks `requires` edges in networkx to the weakest prerequisite and returns the path + source citations. The graph decides, not the LLM.
   - `flag_for_lecturer(concept_id, reason)` appends an anonymized flag (no student id, no raw text).
3. Matteo call (`prompts/matteo.md`), given the student's message, the speaker's name (group mode) and the Examiner's `next_probe`.
4. Guardrail IN CODE on Matteo's draft: reject it if it contains a full explanation or solution (rules: ~80-word cap; a blocklist like "the answer is", "the correct answer", "net force is", "Newton's law states", "you should"; worked calculations). On reject, regenerate once with a stricter reminder; if still bad, fall back to a safe canned confused question.
5. Step budget: max 2 LLM retries per turn. If the Examiner is unsure (no matching concept in the graph), it says so explicitly; never invent graph facts.

## UI (Streamlit, two tabs)
- **"Teach Matteo":** chat on the left with a "Who's speaking?" picker (solo or group: Alex/Bea/Chris/Dani). On the right: the live knowledge graph (grey = untested, red = 0–1, yellow = 2, green = 3) and a "Why am I stuck?" card with the root-cause path and its sources.
- **"Professor":** flagged concepts with an approve/reject summary, plus a class heatmap seeded with ~30 synthetic students from `scripts/seed_demo.py` (clearly labelled synthetic).
- Text input is always available (accessibility: no voice required).

## Repo layout
```
app/        main.py (streamlit), orchestrator.py, llm.py, tools.py, graph.py, guardrails.py, models.py, log.py
prompts/    matteo.md, examiner.md   (versioned in git: these are deliverables)
data/       graph.json, students/, lecturer_flags.json
materials/  physics1_newton/ (the demo pack)
scripts/    seed_demo.py, smoke.py
docs/       challenge-brief.md, idea-overview.html, design-choices.md, example-interactions.md, graph-validation.md, risks.md, campaign.md
logs/
README.md   (required deliverable: how to run, models/libraries, custom logic, architecture)
```

## graph.json format
```json
{"nodes":[{"id":"newton_third_law","name":"Newton's third law","description":"...","source":"OpenStax UP1 §5.5; handout core idea 3","misconceptions":["THIRD_LAW_UNEQUAL"]}],
 "edges":[{"from":"newton_third_law","to":"force_interaction","type":"requires"}]}
```
Every node MUST carry a `source`. Keep it small and correct.

## Milestones (do them in order, demo-able after each)
1. Skeleton: llm.py, log.py, a Streamlit chat with Matteo only (Physics I prompt). Run it.
2. Graph: Physics I `data/graph.json` (~13 concepts, `requires` edges, sources, misconception IDs), pyvis render in the right panel.
3. Examiner + tools + memory + live node colouring + root-cause card.
4. Guardrails + group mode + boundary test + "graph doesn't know" test → record the backup video.
5. Professor tab + seed script + flags (+ an optional individual check question scored from the key).
6. README + docs deliverables + 3+ example interactions (incl. the boundary case and a "graph doesn't know" case).
After Milestone 4 we must have a reliable demo. Milestones 5–6 only if time allows.

## Rules for Claude Code
- Build the smallest thing that demos well. No auth, no database, no Docker, no tests beyond a quick smoke script.
- Run the app after each milestone and fix errors before moving on.
- Never hardcode keys. Never log raw student text to lecturer flags. Never put the instructor key in Matteo's context.
- Prefer boring, reliable libraries. If a library fights you for more than 10 minutes, swap it.
- Commit after each milestone with a clear message.
