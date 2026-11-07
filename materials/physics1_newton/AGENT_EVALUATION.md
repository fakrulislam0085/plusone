# PlusOne minimum live-agent acceptance checks

1. **Grounding:** Select one Newton's Law question and identify the correct OpenStax section or demo handout passage used. Do not invent citations.
2. **Real action:** After a student's response, execute a structured action such as `record_misconception_hypothesis(student, concept, evidence_turns, status)` and show the resulting state, not just a chatbot message.
3. **Peer facilitation:** On the four-person synthetic transcript, address at least two human participants and ask them to examine each other's reasoning.
4. **Boundary:** When Dani asks for the direct answer, avoid giving the completed solution. Provide a productive prompt that returns the reasoning to the group.
5. **No premature diagnosis:** If a student gives a short or ambiguous explanation, label an observation as `needs_confirmation`; do not assert 90% knowledge or infer a stable ability trait.
6. **Transfer:** After discussion, ask a *different* individually answered transfer problem (e.g., T01/T03). Record it as evidence, not proof of durable learning.
7. **Teacher review:** Produce a compact summary with claim, cited student turns, uncertainty and recommended follow-up. Let teacher reject or edit.
8. **Failure path:** If source material does not support a question, say there is insufficient grounding and request professor review.

### Suggested deterministic tools

`score_single_select(question_id, option_id)` retrieves the instructor-only answer key and emits correct/incorrect plus tagged misconceptions.
`record_misconception_hypothesis(student_id, concept_id, evidence_turns, status)` writes structured state; do not label confidence as quantified mastery.
`propose_peer_prompt(group_id, concept_id, evidence_turns)` records a teacher-visible proposed intervention.
`assign_transfer_question(student_id, question_id)` selects an item linked to the relevant learning outcome.

**Important:** Hard-coded fixtures can seed the demo, but the model should make at least one meaningful decision on a fresh input with a visible trace.
