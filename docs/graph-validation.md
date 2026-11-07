# Knowledge graph: ontology, sources and validation (Level 3, path B)

## Ontology (kept small on purpose: every part exists because the use scenario needs it)

| Element | What it is | Why PlusOne needs it |
|---|---|---|
| **Concept** (class) | A Newton's-laws idea a student must be able to explain (13 nodes) | The Examiner scores explanations per concept; the graph is coloured per concept |
| **requires** (relationship, Concept → Concept) | A is impossible to explain well without B | The root cause is a walk through `requires`: "you struggle with A because it requires B" |
| **Misconception** (class, 12 IDs from the pack) | A catalogued wrong belief, e.g. `THIRD_LAW_UNEQUAL` | Matteo may only plant these (no invented physics); the professor sees which ones recur |
| **hasMisconception** (Concept → Misconception) | Where a misconception lives | Lets the Examiner tag an error and the flag carry it |
| **LearningOutcome** (LO1–LO6) | The course objectives from the manifest | Ties concepts back to what the professor teaches |
| **QuizItem** (Q01–Q10) | Diagnostic questions in the pack | Suggested check question for the professor ("confirm with Q07") |
| **source** (property, required on every node) | OpenStax section and/or handout core idea | Provenance: every answer cites where the fact comes from |

Format: `data/graph.json` (nodes + edges); loaded into networkx (`app/graph.py`) and rendered with pyvis.

## Sources
- *PlusOne Physics I Newton's Laws demo pack* (`materials/physics1_newton/`), written by our team: original handout, diagnostic quiz, instructor key, group tasks.
- Aligned with **OpenStax University Physics Vol. 1, Chapter 5** (CC BY 4.0): §5.1 Forces, §5.2 First law, §5.3 Second law, §5.5 Third law, §5.6 Common forces, §5.7 Free-body diagrams. URLs are in `course_manifest.json`.
- **Not official Politecnico di Torino material.** We say so in the app and in the pitch.

## How the graph was built
1. Concepts are taken from the pack's scope and learning outcomes (manifest + handout core ideas 1–6).
2. Each node's `description` paraphrases the handout or the OpenStax section it cites.
3. `requires` edges were written by hand, from the order the handout and OpenStax introduce ideas (e.g. the third law requires force-as-interaction and choosing the body).
4. Misconception and quiz links come from the pack: the misconception catalogue, plus each quiz item's learning outcomes, sources and distractor tags.

## Validation (what we checked and what we corrected)
**Automatic checks**: `scripts/validate_graph.py` (re-run any time; no API):

| Check | Result |
|---|---|
| Graph loads; every node has a `source`; edges reference real nodes; no cycles | PASS: 13 nodes, 20 edges |
| Every misconception ID on a node exists in the pack manifest | PASS |
| All 12 pack misconceptions are attached to some concept | PASS |
| Every OpenStax section cited is in the pack's reference list | PASS |
| Every learning-outcome and quiz ID on a node exists | PASS |
| Each quiz item's distractor misconceptions sit on a node linked to that item | **FAIL → fixed** (see below) |
| Prerequisite chains are short enough to explain (≤ 4 hops) | PASS: static friction → FBD → 3rd law → system → force |

**Correction made:** the cross-check found that Q01's wrong answers are tagged `FORCE_CAUSES_SPEED`, which lives on *Velocity vs acceleration*, but that node did not link Q01. We added Q01 to it. All checks now pass.

**Manual review:** we read every node description against its cited handout idea, and checked the direction of each `requires` edge by asking "could a student explain A correctly without B?".

**Runtime safety (the agent can't corrupt the graph):** the Examiner's output is filtered in code. Concept or misconception IDs that aren't in the graph or catalogue are dropped, and topics outside the graph are reported as *not in graph* instead of being invented (live example: momentum and kinetic energy in scenario 4).

## Graph-grounded agent
- The **Examiner** judges only against node descriptions and the catalogue (`prompts/examiner.md`, rules 5–6).
- **Code**, not the LLM, computes the reasoning path (`tools.trace_root_cause`) and shows it with sources on the "Why am I stuck?" card.
- Example interactions with answer, path and sources, including the case where the graph doesn't know: `docs/example-interactions.md`.
