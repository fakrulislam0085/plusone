# AI on Campus: full challenge brief (Reply Student Tech Clash 2026)

Sources: https://studentclash.reply.com/challenges/AI_on_Campus_IT.html (all sections) and `ExtraMaterials.pdf` (Reply's slides). This brief does not assume any particular idea.

## 1. The mission
Pick a **real problem in learning, teaching or assessment** at your university and design an AI-based solution. "Start with the problem, not the tool."

**Out of scope:** administration and logistics (enrolment, fees, timetables, room booking, campus services, transport).

### Three suggested directions (other ideas are also allowed)
| Direction | Framing from Reply | Example ideas they give |
|---|---|---|
| **Teaching** | Understand what students haven't grasped, adapt explanations, create materials. Risk: replacing human judgement. | Instant Q&A on lecture content after class (the questions nobody asks in a 200-person hall); turn last year's slides into a first draft of the updated course; a "digital twin" lecturer available 24/7 |
| **Learning** | Understand mistakes, build resilient mental models, know what you truly know. AI can support this or short-circuit it. | Practice questions that adapt to what you keep getting wrong; an oral-exam simulator that pushes back when your reasoning is shaky |
| **Assessment** | Reveal what you actually know, not what you could find or generate. AI could make assessment more honest or easier to game. | Essay feedback that explains *why* the argument fails; a pre-exam readiness check that shows which gaps still matter |

### Level 1 pro tips
- **Start from your own experience:** a course where you got stuck, an exam you under-prepared for.
- **Be specific:** one course, one exam, one precise moment.
- **Would it still work without AI?** If yes, you probably don't need AI. If no, that's your argument, so make it.
- **Name the risks:** Who owns the student data? What if the tool goes down the night before the exam? Which students lack reliable access?

## 2. Structure and what is required
| Level | Status | What it is |
|---|---|---|
| 1 · Design | **Required** | Problem + AI idea + 60-second pitch |
| 2 · Build | **Required** | A working AI agent showing the core idea (no-code or code) |
| 3 · Extra | Optional | Multi-agent system / knowledge graph / launch campaign: any number of these, partial work counts |

"You can win by focusing on Levels 1 and 2." Level 3 is a bonus.

## 3. Evaluation
**Criteria:** Creativity & Innovation **40%** · Impact 20% · Technical 20% · Effective Presentation 20%.

**The three judge questions, applied at every level:**
1. Is it genuinely new, or just faster? ("AI that changes what's possible is the goal.")
2. Does it help someone think, or does it think for them?
3. Who benefits, and who might be left out?

**Presentation format:**
- **Stage 1 (everyone):** a 60-second elevator pitch with **no slides**. Cover the problem (who experiences it and when), the solution and the impact. Goal: listeners can repeat your idea in their own words. Expect to be challenged.
- **Stage 2 (top 3 only):** a slide presentation of up to 5 minutes covering problem → idea → how it works → impact. Expect to defend your choices.

**Hand-in:** the presentation is **required**. Also share the materials you produced (agent, documents, prototype files) if you can.

## 4. Level 2: the agent must
1. **Work with real material:** lecture notes, slides, syllabus, exam regulations, past papers.
2. **Do something, not just say something:** take at least one action beyond replying, e.g. generate and score a quiz, track what a student keeps getting wrong, flag a question for the lecturer, update a study plan.
3. **Know its limits:** stay on the line between helping someone think and thinking for them. Know when to guide, when to ask for clarification, and when it cannot give a reliable answer.

**Test cases Reply suggests (PDF p.29):** a normal request, an incomplete request, and a case where the agent should recognise its limits.

### Reference architecture (coding path)
- UI (chat / Telegram / Streamlit)
- Orchestrator loop: plan → act → observe, with step budget, state and routing. When the budget runs out or the agent is unsure, it **hands over to a human**.
- LLM for reasoning and tool choice
- System prompt (role · goal · rules · procedure · output format), **versioned in git**
- Tools, e.g. `search_notes` (RAG), `generate_exercise`, `grade_answer`, `schedule_review`, `notify`. The model decides *when* to use a tool; your code decides *what* it can do.
- Memory: a structured learner profile (JSON/SQLite) plus history
- Guardrails **in code**, not only in the prompt ("a prompt can be talked around; a check in code cannot")
- Logs of every step, which serve as debugging and testing evidence

Minimum viable agent = orchestrator + LLM + one tool + memory.

### Deliverables: coding path
- [ ] README: how to run, models, libraries, frameworks, custom logic
- [ ] Working script / notebook / repo
- [ ] Architecture description: input, knowledge, tools, decisions, output
- [ ] Example interactions with different users and situations, **including one where the agent holds its boundary**
- [ ] (Optional) UI or demo video

### Deliverables: no-code path
- [ ] Agent instructions written as a spec with sections ROLE / GOAL / KNOWLEDGE / RULES / PROCEDURE / MEMORY, plus a design-choices note
- [ ] Description of the material used and the actions the agent takes
- [ ] Example interactions, including the boundary case
- [ ] Screenshots or an export of the setup
- [ ] (Optional) demo video

## 5. Level 3 paths
### A. Multi-agent system (Reply's spec is fixed)
- **Problem Identifier Agent:** interviews the user with adaptive follow-up questions and outputs a structured **Problem Brief**.
- **≥2 Solver Agents** with distinct roles (e.g. learning design, technical feasibility, inclusion/risk/governance), all receiving the same brief.
- Each Solver writes a proposal covering approach, user value, required info/tools, risks, assumptions and implementation.
- **Orchestration/selection:** the proposals are compared, combined or selected by an orchestrator, an evaluator, transparent criteria or a human decision point, with an explanation of why the result fits.
- **Clarification loop:** if the brief is vague or conflicting, a Solver sends a targeted question back before continuing.
- **Human review:** the points where a person validates, reviews, approves or stops the workflow. Uncertainty stays visible.

### B. Knowledge graph
- "A university is already a graph": prerequisites, criteria, courses → skills.
- Benefits: **explainability** ("You struggle with B because it requires A, and your last attempts on A failed"), **controllability** (lecturers fix facts directly in the graph) and **accountability** (provenance on every fact).
- Steps:
  1. Design a small ontology (classes, relationships, key properties).
  2. Populate it with real or realistic data via LLM extraction, then **validate** it (manual review, sampling, rules). A small, correct graph beats a large, noisy one.
  3. Build a graph-grounded agent that shows its reasoning path, cites sources, and **says when the graph doesn't contain the answer**.
- Tools: Protégé/OWL/RDF; Neo4j, GraphDB, Fuseki, RDFLib, NetworkX; LangChain/LlamaIndex; Streamlit/Gradio/Neo4j Bloom.
- Deliver:
  - Ontology plus the reason each part exists
  - A visualisation or export of the graph, plus sources and validation notes
  - The agent and its README
  - ≥3 example interactions, each with answer + path + sources, **at least one where the graph doesn't know**
  - (Optional) video

### C. Launch campaign
- Design a name (easy to remember), a tagline (captures the value), channels (social, classrooms, email, word of mouth, faculty) and timing built around the academic year. Justify each choice by who you want to engage.
- Goal: **one month after launch, target users know the tool and have tried it at least once.**

## 6. Practical info from ExtraMaterials.pdf
- Reply **recommends OpenCode** (opencode.ai, open source, desktop or terminal). Its project files are `AGENTS.md`, `opencode.jsonc`, `.opencode/agents/*.md` and `.opencode/commands/*.md`. Other tools are allowed, so Claude Code is fine.
- Models: the free DeepSeek V4.1 Flash is suggested. **The organisers hand out OpenAI API keys on request.** That makes the `llm.py` provider swap a real fallback.
- LlamaIndex sample: an agent answering over your own docs (SimpleDirectoryReader → VectorStoreIndex → query engine as a tool → FunctionAgent).
- Prompting techniques worth naming in the pitch: clarity/precision, context and constraints, role-based prompting, chain-of-thought, prompt chaining, self-consistency, least-to-most.
- Closing line: "The goal is not to produce as much code as possible. It is to build an agent … whose behaviour you can understand, test and explain."

## 7. Reusable checklist for any idea
- [ ] Problem: what it is and who experiences it
- [ ] Idea in plain language
- [ ] Use scenario in a real moment (course, week, exam)
- [ ] Target user and context
- [ ] Success measures
- [ ] 60-second pitch rehearsed out loud
- [ ] Agent uses real material
- [ ] Agent performs ≥1 action
- [ ] Boundary holds (help think, don't think for them), with a guardrail in code
- [ ] Answers to the 3 judge questions + named risks (data ownership, downtime, access)
