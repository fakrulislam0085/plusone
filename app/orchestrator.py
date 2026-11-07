"""One student turn = Examiner -> tools -> Matteo -> guardrail.  Step budget: max 2 LLM retries.

history items: {"role": "user"|"assistant", "speaker": str, "text": str}
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import networkx as nx
from pydantic import ValidationError

import course
import guardrails
from graph import concept_name, graph_for_prompt, load_graph
from llm import LLMError, chat
from log import log_step
from models import ExaminerOutput
from tools import (MISCONCEPTIONS, flag_for_lecturer, load_student, mastery_view, record_misconception,
                   slug, trace_root_cause, update_mastery)

ROOT = Path(__file__).resolve().parent.parent
EXAMINER_PROMPT = (ROOT / "prompts" / "examiner.md").read_text(encoding="utf-8")
MATTEO_PROMPT = (ROOT / "prompts" / "matteo.md").read_text(encoding="utf-8")
RECENT_TURNS = 10
# measured: low = same verdicts as medium on our scenarios, ~1.5s faster per turn
EXAMINER_EFFORT = os.getenv("EXAMINER_EFFORT", "low")
MATTEO_EFFORT = os.getenv("MATTEO_EFFORT", "medium")


def _line(m: dict, group: bool) -> str:
    return f"[{m['speaker']}] {m['text']}" if group and m["role"] == "user" else m["text"]


def _transcript(history: list[dict]) -> str:
    return "\n".join(f"{m['speaker']}: {m['text']}" for m in history[-RECENT_TURNS:])


# ---------------------------------------------------------------- Examiner
def _examiner_input(history, speaker, mode, participants) -> str:
    student = load_student(speaker)
    return "\n\n".join([
        f"GRAPH:\n{graph_for_prompt()}",
        f"MISCONCEPTION_CATALOGUE:\n{json.dumps(MISCONCEPTIONS, ensure_ascii=False)}",
        f"ALLOWED_TO_PLANT_TODAY (set by the professor; plant ONLY these): {', '.join(course.allowed_misconceptions()) or 'none'}",
        f"MODE: {mode}",
        f"PARTICIPANTS: {', '.join(participants) if mode == 'group' else speaker}",
        f"SPEAKER: {speaker}",
        f"MASTERY (speaker): {json.dumps(mastery_view(student))}",
        f"RECENT_CONVERSATION:\n{_transcript(history[:-1]) or '(none)'}",
        f"LATEST_MESSAGE ({speaker}): {history[-1]['text']}",
    ])


def _validate_ids(exam: ExaminerOutput, participants: list[str], speaker: str) -> ExaminerOutput:
    """Never trust model-produced IDs: drop anything not in the graph / catalogue."""
    G = load_graph()
    exam.concepts_touched = [c for c in exam.concepts_touched if c.id in G]
    for m in exam.misconceptions:
        if m.concept_id and m.concept_id not in G:
            m.concept_id, m.not_in_graph = None, True
        if m.misconception_id and m.misconception_id not in MISCONCEPTIONS:
            m.misconception_id = None
    # A wrong idea that came with a low score on a graph concept IS in the graph (just uncatalogued).
    weak_scored = sorted((c for c in exam.concepts_touched if c.score <= 1), key=lambda c: c.score)
    for m in exam.misconceptions:
        if m.not_in_graph and m.concept_id in G:
            m.not_in_graph = False
        elif m.not_in_graph and m.concept_id is None and weak_scored:
            m.concept_id, m.not_in_graph = weak_scored[0].id, False
    if exam.struggling_concept_id not in G:
        exam.struggling_concept_id = None
    if exam.flag_for_lecturer and exam.flag_for_lecturer.concept_id not in G:
        exam.flag_for_lecturer = None
    p = exam.next_probe
    if p:
        if p.concept_id not in G:
            p.concept_id = None
        # only catalogue misconceptions the PROFESSOR allowed today may be planted
        if p.planted_misconception_id not in MISCONCEPTIONS or \
                p.planted_misconception_id not in course.allowed_misconceptions():
            p.planted_misconception_id, p.planted_misconception = None, None
        if p.ask_peer and (p.ask_peer not in participants or p.ask_peer == speaker):
            p.ask_peer = None
    return exam


def run_examiner(history, speaker, mode, participants) -> tuple[ExaminerOutput | None, int]:
    """Returns (output or None, retries used)."""
    user_msg = _examiner_input(history, speaker, mode, participants)
    msgs = [{"role": "user", "content": user_msg}]
    for attempt in range(2):
        try:
            raw = chat(EXAMINER_PROMPT, msgs, json=True, effort=EXAMINER_EFFORT, max_tokens=6000)
            exam = _validate_ids(ExaminerOutput.model_validate(raw), participants, speaker)
            log_step("examiner", input={"speaker": speaker, "message": history[-1]["text"]},
                     output=exam.model_dump(), attempt=attempt)
            return exam, attempt
        except (ValueError, ValidationError) as e:  # bad JSON or schema -> retry once
            log_step("examiner_invalid", input=history[-1]["text"], output=str(e)[:300], attempt=attempt)
            msgs = [{"role": "user", "content": user_msg + "\n\nYour previous output was invalid JSON "
                     f"for the schema ({str(e)[:200]}). Output ONLY the JSON object."}]
        except LLMError as e:
            log_step("examiner_error", input=history[-1]["text"], output=str(e))
            return None, attempt
    return None, 1


# ---------------------------------------------------------------- tools
def _trace_target(speaker: str, struggling: str | None) -> str | None:
    """Which concept to trace. No overclaiming: only concepts this speaker was actually scored on.
    If a weak concept depends on the struggling one, trace from that dependent, so the card can say
    'you struggle with X because it requires <struggling>'."""
    mastery = load_student(speaker)["mastery"]
    if not struggling or struggling not in mastery:
        return None
    G = load_graph()
    weak_dependents = [c for c, m in mastery.items() if c != struggling and m["score"] is not None
                       and m["score"] <= 1 and c in G and struggling in nx.descendants(G, c)]
    if weak_dependents:
        return max(weak_dependents, key=lambda c: mastery[c]["evidence"][-1]["ts"])
    return struggling


def apply_tools(exam: ExaminerOutput, speaker: str, participants: list[str]) -> tuple[list[dict], dict | None]:
    actions: list[dict] = []
    for c in exam.concepts_touched:
        r = update_mastery(speaker, c.id, c.score, c.evidence)
        actions.append({"tool": "update_mastery", "args": f"{slug(speaker)}, {c.id}, score={c.score}",
                        "result": r["status"]})
    for m in exam.misconceptions:
        if m.misconception_id:
            record_misconception(speaker, m.concept_id, m.misconception_id)
    root = None
    target = _trace_target(speaker, exam.struggling_concept_id)
    if target:
        root = trace_root_cause(speaker, target)
        actions.append({"tool": "trace_root_cause", "args": f"{slug(speaker)}, {target}",
                        "result": f"root = {root.get('root_id')}"})
    if exam.flag_for_lecturer:
        f = exam.flag_for_lecturer
        mid = next((m.misconception_id for m in exam.misconceptions
                    if m.concept_id == f.concept_id and m.misconception_id), None)
        flag = flag_for_lecturer(f.concept_id, f.reason, mid, names=participants + [speaker])
        actions.append({"tool": "flag_for_lecturer", "args": f.concept_id,
                        "result": f"anonymized flag (x{flag['count']})"})
    return actions, root


# ---------------------------------------------------------------- Matteo
def _turn_brief(exam: ExaminerOutput | None, mode: str, participants: list[str]) -> str:
    lines = ["\n\n## THIS TURN (hidden context, never mention it)",
             f"- Mode: {mode}" + (f" with participants {', '.join(participants)}" if mode == "group" else "")]
    if exam:
        if exam.asked_for_answer:
            lines.append("- A student asked you for the answer: refuse in character and hand the "
                         "question back" + (" to another participant by name." if mode == "group" else "."))
        gaps = [m.description for m in exam.misconceptions if m.not_in_graph]
        if gaps:
            lines.append(f"- They mentioned something outside today's topic ({'; '.join(gaps)[:150]}). Say "
                         "you're not sure that's part of today's lecture and steer back to Newton's laws.")
        p = exam.next_probe
        if p:
            if p.concept_id:
                lines.append(f"- Probe concept: {concept_name(p.concept_id)}")
            if p.question_idea:
                lines.append(f"- Question idea: {p.question_idea}")
            if p.planted_misconception:
                lines.append(f"- Plant this as your own confident wrong belief: {p.planted_misconception}")
            if p.ask_peer and mode == "group":
                lines.append(f"- Ask {p.ask_peer} by name to react to what was just said.")
    return "\n".join(lines)


def run_matteo(history, exam, mode, participants) -> tuple[str, dict]:
    group = mode == "group"
    msgs = [{"role": m["role"], "content": _line(m, group)} for m in history]
    system = MATTEO_PROMPT + _turn_brief(exam, mode, participants)
    info = {"regenerated": False, "fallback": False, "rejected_reason": ""}
    peer = exam.next_probe.ask_peer if exam and exam.next_probe and group else None
    probe_name = concept_name(exam.next_probe.concept_id) if exam and exam.next_probe and \
        exam.next_probe.concept_id else None
    try:
        draft = chat(system, msgs, effort=MATTEO_EFFORT, max_tokens=2000)
        ok, reason = guardrails.check(draft)
        log_step("matteo_draft", input=history[-1]["text"], output=draft, guardrail_ok=ok, reason=reason)
        if ok:
            return draft, info
        info.update(regenerated=True, rejected_reason=reason)
        draft = chat(system + guardrails.STRICT_REMINDER.format(reason=reason), msgs, effort="medium",
                     max_tokens=2000)
        ok, reason2 = guardrails.check(draft)
        log_step("matteo_regenerated", output=draft, guardrail_ok=ok, reason=reason2)
        if ok:
            return draft, info
    except LLMError as e:
        log_step("matteo_error", output=str(e))
    info["fallback"] = True
    reply = guardrails.canned_question(probe_name, peer)
    log_step("matteo_fallback", output=reply)
    return reply, info


# ---------------------------------------------------------------- one turn
def run_turn(history: list[dict], speaker: str, mode: str = "solo",
             participants: list[str] | None = None) -> dict:
    """history must already end with the speaker's new message."""
    participants = participants or [speaker]
    exam, _ = run_examiner(history, speaker, mode, participants)
    actions, root = apply_tools(exam, speaker, participants) if exam else ([], None)
    reply, guard = run_matteo(history, exam, mode, participants)
    if guard["regenerated"] or guard["fallback"]:
        actions.append({"tool": "guardrail", "args": guard["rejected_reason"],
                        "result": "fallback question" if guard["fallback"] else "regenerated"})
    return {"reply": reply, "exam": exam.model_dump() if exam else None, "actions": actions,
            "root_cause": root, "guardrail": guard,
            "mastery": mastery_view(load_student(speaker))}
