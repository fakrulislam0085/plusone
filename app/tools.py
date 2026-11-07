"""The agent's actions: plain Python, deterministic, logged.

- update_mastery     -> data/students/<student_id>.json
- trace_root_cause   -> walks 'requires' edges in the graph (the graph decides, not the LLM)
- flag_for_lecturer  -> data/lecturer_flags.json (anonymized: no student id, no raw text)
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

from graph import band, concept_name, load_graph
from log import log_step

ROOT = Path(__file__).resolve().parent.parent
STUDENTS_DIR = ROOT / "data" / "students"
FLAGS_PATH = ROOT / "data" / "lecturer_flags.json"
MANIFEST = json.loads((ROOT / "materials" / "physics1_newton" / "course_manifest.json")
                      .read_text(encoding="utf-8"))
MISCONCEPTIONS: dict[str, str] = MANIFEST["misconceptions"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "student"


# ---------------------------------------------------------------- memory
def _student_path(student_id: str) -> Path:
    return STUDENTS_DIR / f"{slug(student_id)}.json"


def load_student(student_id: str) -> dict:
    p = _student_path(student_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"student_id": slug(student_id), "mastery": {}, "misconceptions_seen": [], "turns": 0}


def save_student(student: dict) -> None:
    STUDENTS_DIR.mkdir(parents=True, exist_ok=True)
    _student_path(student["student_id"]).write_text(
        json.dumps(student, indent=2, ensure_ascii=False), encoding="utf-8")


def mastery_view(student: dict) -> dict:
    """{concept_id: {"score", "status"}} for the graph renderer."""
    return {c: {"score": m["score"], "status": m["status"]} for c, m in student["mastery"].items()}


def update_mastery(student_id: str, concept_id: str, score: int, evidence: str) -> dict:
    """Record one piece of evidence. A concept is 'confirmed' only after two consistent
    observations (both weak, or both ok); otherwise it stays a hypothesis."""
    student = load_student(student_id)
    entry = student["mastery"].setdefault(concept_id, {"score": None, "status": "needs_confirmation",
                                                        "evidence": []})
    entry["evidence"].append({"score": score, "evidence": evidence[:160], "ts": _now()})
    entry["evidence"] = entry["evidence"][-6:]
    entry["score"] = score
    recent = [e["score"] for e in entry["evidence"][-2:]]
    consistent = len(recent) == 2 and ((recent[0] <= 1) == (recent[1] <= 1))
    entry["status"] = "confirmed" if consistent else "needs_confirmation"
    save_student(student)
    result = {"concept_id": concept_id, "score": score, "status": entry["status"]}
    log_step("tool.update_mastery", input={"student_id": slug(student_id), "concept_id": concept_id,
                                           "score": score}, output=result)
    return result


def record_misconception(student_id: str, concept_id: str | None, misconception_id: str | None) -> None:
    if not misconception_id:
        return
    student = load_student(student_id)
    seen = student.setdefault("misconceptions_seen", [])
    if misconception_id not in [s["id"] for s in seen]:
        seen.append({"id": misconception_id, "concept_id": concept_id, "status": "needs_confirmation",
                     "ts": _now()})
    else:
        for s in seen:
            if s["id"] == misconception_id:
                s["status"] = "confirmed"
    save_student(student)


# ---------------------------------------------------------------- root cause
def trace_root_cause(student_id: str, concept_id: str) -> dict:
    """Walk prerequisites of `concept_id`; the weakest tested prerequisite is the root cause.
    Ties -> closest prerequisite. Untested prerequisites are reported as 'check next'."""
    G = load_graph()
    if concept_id not in G:
        out = {"concept_id": concept_id, "found": False,
               "explanation": "This concept is not in the course graph, so I can't trace it."}
        log_step("tool.trace_root_cause", input={"concept_id": concept_id}, output=out)
        return out
    mastery = load_student(student_id)["mastery"]
    prereqs = nx.descendants(G, concept_id)
    dist = nx.single_source_shortest_path_length(G, concept_id)

    tested_weak = [p for p in prereqs if p in mastery and mastery[p]["score"] is not None
                   and mastery[p]["score"] <= 2]
    untested = sorted((p for p in prereqs if p not in mastery), key=lambda p: dist[p])

    if tested_weak:
        root = min(tested_weak, key=lambda p: (mastery[p]["score"], dist[p]))
    else:
        root = concept_id
    path_ids = nx.shortest_path(G, concept_id, root)

    def node_info(cid):
        m = mastery.get(cid, {})
        return {"id": cid, "name": G.nodes[cid]["name"], "source": G.nodes[cid]["source"],
                "score": m.get("score"), "status": m.get("status"), "band": band(m.get("score"))}

    path = [node_info(c) for c in path_ids]
    cname = G.nodes[concept_id]["name"]
    if root != concept_id:
        r = path[-1]
        quality = "weak" if r["score"] <= 1 else "shaky"
        via = " → ".join(p["name"] for p in path[1:-1])
        explanation = (f"You struggle with **{cname}** because it requires **{r['name']}**"
                       + (f" (via {via})" if via else "")
                       + f", and your explanation of {r['name']} was {quality}.")
    else:
        explanation = f"Your explanation of **{cname}** itself is the weak spot."
        if untested:
            explanation += (" Its prerequisites haven't been tested yet: check "
                            f"**{G.nodes[untested[0]]['name']}** next.")
        else:
            explanation += " Its prerequisites look fine, so focus on this concept directly."
    if mastery.get(root, {}).get("status") == "needs_confirmation":
        explanation += " _(Hypothesis: needs one more piece of evidence.)_"

    out = {"concept_id": concept_id, "found": True, "root_id": root, "path": path,
           "untested_prereqs": [node_info(u) for u in untested[:3]], "explanation": explanation}
    log_step("tool.trace_root_cause", input={"student_id": slug(student_id), "concept_id": concept_id},
             output={"root": root, "path": path_ids})
    return out


# ---------------------------------------------------------------- lecturer flags
def load_flags() -> list[dict]:
    if FLAGS_PATH.exists():
        return json.loads(FLAGS_PATH.read_text(encoding="utf-8"))
    return []


def _sanitize(reason: str, names: list[str]) -> str:
    """Anonymize: drop participant names and quotes, keep it short and generic."""
    text = re.sub(r"[\"“”'‘’].*?[\"“”'‘’]", "", reason)
    for n in names:
        if n:
            text = re.sub(rf"\b{re.escape(n)}\b", "a student", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()[:140]


def flag_for_lecturer(concept_id: str, reason: str, misconception_id: str | None = None,
                      names: list[str] | None = None) -> dict:
    G = load_graph()
    flags = load_flags()
    reason = _sanitize(reason, names or [])
    for f in flags:
        if f["concept_id"] == concept_id and f["status"] == "pending":
            f["count"] += 1
            f["last_seen"] = _now()
            if misconception_id and misconception_id not in f["misconception_ids"]:
                f["misconception_ids"].append(misconception_id)
            flag = f
            break
    else:
        flag = {"concept_id": concept_id, "concept_name": G.nodes[concept_id]["name"] if concept_id in G
                else concept_id, "reason": reason, "misconception_ids": [misconception_id] if misconception_id
                else [], "count": 1, "status": "pending", "first_seen": _now(), "last_seen": _now()}
        flags.append(flag)
    FLAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FLAGS_PATH.write_text(json.dumps(flags, indent=2, ensure_ascii=False), encoding="utf-8")
    log_step("tool.flag_for_lecturer", input={"concept_id": concept_id}, output={"reason": reason,
                                                                                 "count": flag["count"]})
    return flag


def misconception_text(mid: str | None) -> str | None:
    return MISCONCEPTIONS.get(mid) if mid else None


__all__ = ["update_mastery", "trace_root_cause", "flag_for_lecturer", "load_student", "mastery_view",
           "record_misconception", "load_flags", "MISCONCEPTIONS", "concept_name", "slug"]
