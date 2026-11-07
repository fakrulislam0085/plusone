# Spiegamelo — Reply Student Tech Clash 2026 (AI on Campus), PoliTO

Hackathon TODAY (Sat 7 Nov 2026). Hard feature freeze at 16:00. Speed and a demo that never breaks matter more than elegance.

## The challenge (Reply brief)
- Mission: pick a real problem in learning/teaching/assessment at our university, design an AI-based solution. Out of scope: admin/logistics.
- Level 1 (required): idea + 60-second pitch.
- Level 2 (required): a working AI agent showing the core idea. It must DO something beyond replying (e.g. track what a student keeps getting wrong, flag a question for the lecturer) and must hold its boundary (help the student think, never think for them).
- Level 3 (optional): we do Knowledge Graph (path B) + Launch campaign (path C). Multi-agent: we only mention our 2 agents, we do NOT build Reply's Problem-Identifier/Solver spec.
- Scoring: Creativity & Innovation 40%, Impact 20%, Technical 20%, Presentation 20%.
- Judges ask: genuinely new or just faster? Helps think or thinks for them? Who benefits / who is left out?
- Top 3 teams give a 5-minute slide presentation and must defend choices.

## The idea
Spiegamelo ("explain it to me"): you learn a course by TEACHING Matteo, a confused AI freshman ("matricola").
- Matteo asks naive questions, sometimes plants a plausible misconception, and NEVER gives answers. If asked for the answer: "I don't know, that's why I'm asking you!"
- The Examiner agent silently scores each explanation against the course knowledge graph, updates the student's mastery per concept, and explains WHY the student is stuck by tracing prerequisites ("You struggle with L'Hôpital because it requires derivatives, and your explanation of derivatives was shaky").
- Action: concepts the student fails get flagged (anonymized) to the lecturer. Lecturer view shows where the whole class breaks.
- Scope: ONE course, ONE topic — Analisi Matematica I, limits and the concepts around them. ~12–15 concepts.

## Tech stack (keep it simple)
- Python 3.11+, Streamlit UI, single repo.
- LLM: all calls go through `app/llm.py` (one function `chat(system, messages, json=False)`). Default provider Anthropic (`anthropic` SDK, model from env `MODEL`, default `claude-sonnet-5-5`). Must be swappable to another provider (e.g. Gemini or a Reply-provided API) by editing only `llm.py`.
- Key in `.env` (`ANTHROPIC_API_KEY`), loaded with python-dotenv. `.env` in `.gitignore`.
- Graph: `data/graph.json` loaded into networkx. Visualisation with pyvis embedded via `streamlit.components.v1.html`.
- Memory: `data/students/<student_id>.json` (mastery per concept, misconceptions seen, history summary).
- Lecturer flags: `data/lecturer_flags.json`.
- Logs: every step appended to `logs/session.jsonl` (timestamp, step, input, output). These are our testing evidence.

## Architecture (matches Reply's reference: orchestrator + LLM + tools + memory + guardrails + logs)
Per student turn, `app/orchestrator.py`:
1. Examiner call (`prompts/examiner.md`), returns strict JSON (validated with pydantic; retry once on invalid JSON):
   `{concepts_touched:[{id, score 0-3, evidence}], misconceptions:[{concept_id, description, not_in_graph}], struggling_concept_id | null, flag_for_lecturer:{concept_id, reason} | null, next_probe:{concept_id, question_idea, planted_misconception | null}}`
   The schema in `prompts/examiner.md` is the source of truth. The Examiner does NOT compute the root cause; code does it from `struggling_concept_id` (step 2).
2. Tools (plain Python functions, the agent's actions):
   - `update_mastery(student_id, concept_id, score, evidence)` → memory file
   - `trace_root_cause(student_id, concept_id)` → walks `requires` edges in networkx to the weakest prerequisite; returns path + source citations. The graph decides, not the LLM.
   - `flag_for_lecturer(concept_id, reason)` → appends anonymized flag (no student id, no raw text)
3. Matteo call (`prompts/matteo.md`), given the student's message + the Examiner's `next_probe`.
4. Guardrail IN CODE on Matteo's draft: reject if it contains a full explanation/solution (rules: length cap ~80 words, blocklist like "the answer is", "the definition is", "you should", formulas solved step by step). On reject, regenerate once with a stricter reminder; if still bad, fall back to a safe canned confused question.
5. Step budget: max 2 LLM retries per turn. If the Examiner is unsure (graph has no matching concept), it says so explicitly; never invent graph facts.

## UI (Streamlit, two tabs)
- "Teach Matteo": chat on the left; on the right the live knowledge graph (nodes coloured grey=untested, red=0-1, yellow=2, green=3) and a "Why am I stuck?" card showing the root-cause path with sources.
- "Lecturer view": class heatmap of concepts (aggregate mastery across students) + list of flagged concepts. Seed with ~30 synthetic students from `scripts/seed_demo.py` so it looks real.
- Text input always available (accessibility: no voice required). Matteo replies in the student's language (Italian or English).

## Repo layout
```
app/        main.py (streamlit), orchestrator.py, llm.py, tools.py, graph.py, guardrails.py, models.py
prompts/    matteo.md, examiner.md   (versioned in git: these are deliverables)
data/       graph.json, students/, lecturer_flags.json
materials/  lecture PDFs (source for the graph)
scripts/    extract_graph.py, seed_demo.py
docs/       design-choices.md, example-interactions.md, graph-validation.md, risks.md, campaign.md
logs/
README.md   (required deliverable: how to run, models/libraries, custom logic, architecture)
```

## graph.json format
```json
{"nodes":[{"id":"limit","name":"Limit of a function","description":"...","source":"Analisi I slides, L5 p.12"}],
 "edges":[{"from":"lhopital","to":"derivative","type":"requires"}]}
```
Every node MUST carry a `source`. Keep it small and correct.

## Milestones (do them in order, demo-able after each)
1. Skeleton: repo, requirements.txt, llm.py, .env.example, a Streamlit chat with Matteo only. Run it.
2. Graph: placeholder `data/graph.json` (~12 Analisi I limit concepts with `requires` edges and sources), pyvis render in the right panel.
3. Examiner + tools + memory + live node colouring + root-cause card.
4. Guardrails + logs + boundary test.
5. Lecturer tab + seed script + flags.
6. README + docs deliverables + 3+ example interactions (incl. the boundary case and a "graph doesn't know" case).
After milestone 4 we must have a reliable demo. Milestones 5-6 only if time allows before 16:00.

## Rules for Claude Code
- Build the smallest thing that demos well. No auth, no database, no Docker, no tests beyond a quick smoke script.
- Run the app after each milestone and fix errors before moving on.
- Never hardcode keys. Never log raw student text to lecturer flags.
- Prefer boring, reliable libraries. If a library fights you for more than 10 minutes, swap it.
- Commit after each milestone with a clear message.
