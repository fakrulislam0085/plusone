# Matteo: learn Physics I by teaching a confused AI

**Reply Student Tech Clash 2026 · AI on Campus · Politecnico di Torino**

Students learn **Newton's laws** by teaching **Matteo**, an AI freshman who is confused on purpose. They teach him alone or **as a study group**, with Matteo as the "+1" member. Matteo is built not to give answers (his role plus a guardrail in code that blocks tutor-style replies). He asks, plants real first-year misconceptions and hands questions back to the peers ("Bea, do you agree with Alex?"). Behind him, a silent **Examiner** scores every explanation against a **course knowledge graph**. The code points to a **possible gap to check** by walking the prerequisites, down to the source. It's a hypothesis to investigate, not a diagnosis. The **professor** sees anonymized flags and approves or rejects them.

> *"Possible gap to check: Newton's third law builds on **Force as an interaction**, and your explanation of Force as an interaction was weak. Check that first."* (app card; a hypothesis, not a diagnosis)

**Student flow:** ① Start (alone or as a group) → ② **today's session quiz** (graded in code; the answers stay locked) → ③ **teach Matteo** the topic you missed (the next step stays locked until you've explained something) → ④ **final check on your own**: a new question on that topic, graded by code (MCQ) or against the professor's criteria (written) → ⑤ summary (answers unlock, what to review, 🔥 participation streak +1).
**Professor:** topics to review (approve/reject) · today's quiz results per topic (no names) · **create a quiz from lecture PDFs** (AI draft → edit → publish) · class streak · class map.
**AI teaching audit (professor only, the MVP for teachers):** from the anonymous class evidence (levels per topic, quiz % correct, flags the professor approved, weak prerequisites), an AI coach (`prompts/coach.md`, validated in `app/audit.py`) drafts **what to recap in the next lecture and how**: a headline, the top 3 topics with evidence (numbers only from the data), the misconception to address, "may be rooted in" prerequisites, a 3-step active recap, a check question and a matching group task from the course pack. Shown as a **mind map** plus recap cards with *Add to next lecture*, *Tell students* (posts an announcement) and *Download recap plan*. No student names reach the coach; if the AI is unavailable, a rule-based draft is shown; a student who opens it gets "professor only".
The quiz and streak features were integrated from teammates' prototypes (`quiz_feature`, `StreakTA`): see `app/quiz.py`, `app/streaks.py`, `prompts/quizmaster.md`.

---

## Run it (Windows, ~2 minutes)

```powershell
git clone https://github.com/fakrulislam0085/plusone.git; cd plusone
python -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env          # then put your Anthropic API key in .env (no quotes)
.\.venv\Scripts\python scripts\seed_demo.py      # synthetic class for the professor view
.\.venv\Scripts\streamlit run app/main.py        # opens http://localhost:8501
```
On macOS/Linux, use `source .venv/bin/activate` and `cp`. **Before a demo, click 🧹 Reset demo data in the sidebar.**

Checks:

| Command | What it proves | Cost |
|---|---|---|
| `python scripts/test_guardrails.py` | The code guardrail blocks 13/13 tutor-style drafts (incl. the numeric-result leak found by an audit) and wrongly blocks 0/5 Matteo-style ones. These are tested patterns, not a guarantee | free |
| `python scripts/validate_graph.py` | Graph integrity vs the material pack (9 checks) | free |
| `python scripts/smoke.py` | Model reachable; normal + boundary reply | ~1 cent |
| `python scripts/scenarios.py` | 5 live scenarios → regenerates `docs/example-interactions.md` | ~$0.50 |

## Models and libraries
- **LLM:** Anthropic **Claude Opus 5.5** (`claude-opus-5-5`) through the official `anthropic` Python SDK, with the server-side refusal fallback (`fallbacks: "default"`) enabled. Effort: Examiner `low` (measured: same verdicts as `medium`, ~1.5 s faster), Matteo `medium` (at `low` he sometimes stopped asking questions). Configurable through `MODEL`, `EXAMINER_EFFORT` and `MATTEO_EFFORT` in `.env`.
- **Provider-swappable:** every LLM call goes through `app/llm.py` → `chat(system, messages, json, effort)`. To use another provider (e.g. a Reply-provided key), edit only that file.
- **Libraries:** Streamlit (UI), networkx (graph reasoning), pyvis (graph rendering), pydantic (schema validation), Altair/pandas (professor heatmap), python-dotenv.
- **Nothing is trained.** The value is in the agent design: prompts, tools, graph and guardrails.

## Architecture

```
student message ──► Examiner (LLM, strict JSON) ──► validate IDs in code ──► TOOLS (plain Python)
   (solo or [Name] in group)                                                 ├─ update_mastery     → data/students/<id>.json
                                                                             ├─ trace_root_cause   → walks graph prerequisites
                                                                             └─ flag_for_lecturer  → data/lecturer_flags.json (anonymized)
                     ┌──────────────────────── next_probe (concept, question idea, planted misconception, ask_peer)
                     ▼
            Matteo (LLM) ──► GUARDRAIL in code ──ok──► reply
                                 │ reject → regenerate once with a stricter reminder → still bad → canned safe question
every step ──► logs/session.jsonl (testing evidence)
```

| | |
|---|---|
| **Input** | The student's message, the speaker name (group mode), the conversation, the speaker's mastery memory |
| **Knowledge** | `data/graph.json`: 13 concepts and 20 `requires` edges. Every node has a source (OpenStax University Physics Vol. 1, Ch. 5, plus the demo handout), learning outcomes, linked quiz items and misconception IDs from the pack's catalogue of 12 |
| **Tools / actions** | `update_mastery`, `trace_root_cause`, `flag_for_lecturer` (`app/tools.py`); the professor's `set_flag_status` (approve/reject); `generate_quiz` (AI draft from PDF), `grade_quiz` (deterministic, no LLM), streak updates (`app/quiz.py`, `app/streaks.py`) |
| **Decisions** | The Examiner decides scores, misconceptions and the next probe. **Code** decides the root cause (the graph, not the LLM), what counts as "confirmed" (two consistent observations), whether a draft is allowed (the guardrail) and what is anonymized |
| **Output** | Matteo's question; live graph colours; the "Possible gap to check" card with path and sources; the agent-trace panel; anonymized professor flags with claim, uncertainty and a suggested follow-up from the pack |

### Custom logic worth knowing
- **Never trust model IDs** (`orchestrator._validate_ids`). Concept IDs not in the graph, misconception IDs not in the catalogue, invented peers and unknown planted misconceptions are all dropped. Out-of-scope topics are marked `not_in_graph`, and Matteo says "not sure that's in today's lecture".
- **No overclaiming.** A weak spot is a *hypothesis (needs confirmation)* until two consistent observations; unconfirmed topics are drawn **pale** with a dashed border, so solid green means confirmed. The final check adds an independent observation. Professor flags count **distinct students** (pseudonymous keys), not events. No root cause is traced for a student who was never scored on that concept. There is no "% mastery" and no grouping by grades.
- **Root cause.** The weakest tested prerequisite wins, with ties going to the closest. If a weak concept depends on the one the student is struggling with, the trace starts from that dependent, which produces "X builds on Y, and Y was weak: check Y first". This is a pedagogical dependency, not proof of the cause.
- **Step budget.** At most 2 LLM retries per turn: 1 Examiner retry on invalid JSON, 1 Matteo regeneration. If the API fails, Matteo falls back to a safe canned question (tested live when the account hit its spend limit: no crash).
- **Retrieval segregation.** The instructor answer key is never in Matteo's context.

## Repository map
```
app/        main.py (UI) · orchestrator.py · llm.py · tools.py · graph.py · guardrails.py · models.py · professor.py · style.py · log.py
prompts/    matteo.md · examiner.md          (ROLE/GOAL/KNOWLEDGE/RULES/PROCEDURE/MEMORY; versioned deliverables)
data/       graph.json · class_seed.json (synthetic) · students/ · lecturer_flags.json (runtime)
materials/  physics1_newton/                 (demo pack: handout, quiz, key, group tasks, synthetic transcript)
scripts/    seed_demo.py · smoke.py · scenarios.py · test_guardrails.py · validate_graph.py
docs/       example-interactions.md · design-choices.md · graph-validation.md · risks.md · campaign.md · challenge-brief.md · idea-overview.html
```

## Honest limitations
- The course material is an **original demo pack aligned with OpenStax** (CC BY 4.0), **not official PoliTO notes**. Real slides can be dropped in by rebuilding `data/graph.json`.
- Group names and the professor heatmap's 30 students are **synthetic**. No learning gains are claimed: that needs a real trial.
- Scores come from short chat explanations and can be wrong, which is why the professor approves or rejects every flag.
- A turn takes about 5–8 s (two sequential Opus calls). Running them in parallel would cut that to about 4 s, at the cost of Matteo using the previous turn's probe.

## Level 3
- **Knowledge graph (path B):** ontology, populated graph, graph-grounded agent and validation are in `docs/graph-validation.md`; examples with path and sources, including a "graph doesn't know" case, are in `docs/example-interactions.md`.
- **Launch campaign (path C):** `docs/campaign.md`.
