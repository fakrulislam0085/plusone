"""SYNTHETIC demo class: 10 students with believable histories (no real people).

Writes: data/roster.json, data/students/*.json (mastery memory), data/streaks.json (sessions S1-S9),
data/quizzes.json (today's quiz + 6 submissions), data/lecturer_flags.json, data/course.json.
Each profile is a small story so every screen tells the same consistent picture.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import course
import quiz
import streaks
from graph import load_graph
from tools import student_key

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAST = ["Units and vectors", "Motion in 1D", "Motion in 2D", "Projectiles", "Circular motion",
        "Relative motion", "What is a force?", "Mass and weight"]
S = lambda *ns: [f"S{n}" for n in ns]  # noqa: E731

#  id, display name, synthetic student number, team, past sessions answered,
#  mastery {concept: [scores over time]}, misconceptions seen
PROFILES = [
    ("alex", "Alex Moretti", "s300101", "Team A", S(1, 2, 3, 4, 5, 6, 7, 8),
     {"newton_first_law": [0, 1], "net_force": [2], "velocity_vs_acceleration": [1]}, ["MOTION_NEEDS_FORCE"]),
    ("bea", "Bea Conti", "s300102", "Team A", S(3, 4, 5, 6, 7, 8),
     {"newton_first_law": [2, 3], "newton_third_law": [3], "net_force": [3], "free_body_diagram": [2]}, []),
    ("chris", "Chris Ferrari", "s300103", "Team A", S(1, 2, 4, 5, 6, 7, 8),
     {"newton_third_law": [1, 0], "force_interaction": [1], "newton_first_law": [3]}, ["THIRD_LAW_UNEQUAL"]),
    ("dani", "Dani Russo", "s300104", "Team A", S(5, 6, 7, 8),
     {"static_friction": [0, 1], "newton_first_law": [2]}, ["STATIC_FRICTION_ZERO"]),
    ("elena", "Elena Greco", "s300105", "Team B", S(1, 2, 3, 4, 5, 6, 7, 8),
     {"newton_third_law": [1], "free_body_diagram": [0, 1], "weight_normal": [2]}, ["FBD_PAIR"]),
    ("federico", "Federico Gallo", "s300106", "Team B", S(1, 2, 3, 4, 5, 6, 7, 8),
     {"newton_first_law": [3], "newton_second_law": [3], "newton_third_law": [3], "incline": [1]},
     ["INCLINE_COMPONENT"]),
    ("giulia", "Giulia Rossi", "s300107", "Team B", S(2, 3, 4, 5, 6, 7, 8), {}, []),
    ("hamid", "Hamid Karimi", "s300108", "Team C", S(4, 5, 6, 7, 8),
     {"mass_inertia": [0, 1], "newton_second_law": [1], "net_force": [2]}, ["MASS_ACCEL"]),
    ("irene", "Irene Marino", "s300109", "Team C", S(1, 2, 3, 4, 5, 6, 7, 8),
     {"newton_first_law": [3], "newton_second_law": [3], "newton_third_law": [3], "static_friction": [2]}, []),
    ("luca", "Luca Bruno", "s300110", "Team C", S(6, 7, 8),
     {"force_interaction": [0], "newton_third_law": [0, 1]}, ["THIRD_LAW_UNEQUAL"]),
]
ANSWERED_TODAY = ["alex", "bea", "chris", "elena", "federico", "irene"]  # 6 of 10 took today's quiz
REASONS = {
    "newton_third_law": "treats the heavier body as exerting the larger interaction force",
    "newton_first_law": "believes a moving object needs a continuing force to keep moving",
    "static_friction": "assumes no friction acts while the box is at rest",
    "free_body_diagram": "draws action and reaction on the same free-body diagram",
    "mass_inertia": "expects the heavier body to accelerate more under the same net force",
    "force_interaction": "treats force as something an object carries, not an interaction",
    "incline": "swaps sine and cosine for the weight components on a slope",
    "velocity_vs_acceleration": "infers a forward force from a constant velocity",
    "newton_second_law": "uses one applied force instead of the net force",
}
MISC_FOR = {"newton_third_law": "THIRD_LAW_UNEQUAL", "newton_first_law": "MOTION_NEEDS_FORCE",
            "static_friction": "STATIC_FRICTION_ZERO", "free_body_diagram": "FBD_PAIR", "mass_inertia": "MASS_ACCEL",
            "incline": "INCLINE_COMPONENT", "velocity_vs_acceleration": "VELOCITY_FORCE",
            "newton_second_law": "NET_VS_APPLIED"}


def _ts(days_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(timespec="seconds")


def seed() -> None:
    DATA.mkdir(exist_ok=True)
    (DATA / "students").mkdir(exist_ok=True)
    for p in (DATA / "students").glob("*.json"):
        p.unlink()
    for f in ("lecturer_flags.json", "quizzes.json", "streaks.json", "course.json", "class_seed.json",
              "audit.json"):
        if (DATA / f).exists():
            (DATA / f).unlink()

    roster = [{"id": i, "name": n, "first": n.split()[0], "matricola": m, "team": t,
               "program": "Computer Engineering (demo)", "cohort": "2026/27"} for i, n, m, t, *_ in PROFILES]
    (DATA / "roster.json").write_text(json.dumps(roster, indent=1), encoding="utf-8")

    for sid, _name, _m, _t, _past, mastery, miscs in PROFILES:
        entries = {}
        for c, scores in mastery.items():
            ev = [{"score": s, "evidence": "earlier session (synthetic)", "ts": _ts(7 - j)} for j, s in enumerate(scores)]
            last2 = scores[-2:]
            confirmed = len(last2) == 2 and ((last2[0] <= 1) == (last2[1] <= 1))
            entries[c] = {"score": scores[-1], "status": "confirmed" if confirmed else "needs_confirmation",
                          "evidence": ev}
        doc = {"student_id": sid, "mastery": entries, "turns": 0,
               "misconceptions_seen": [{"id": x, "concept_id": None, "status": "confirmed", "ts": _ts(3)} for x in miscs]}
        (DATA / "students" / f"{sid}.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")

    streaks._save({"synthetic_note": "Sessions S1-S8 and all answers are synthetic demo history.",
                   "sessions": [{"id": f"S{i}", "title": t} for i, t in enumerate(PAST, 1)],
                   "answered": {sid: list(past) for sid, _n, _m, _t, past, *_ in PROFILES}})
    course.load()            # writes default course.json
    quiz.ensure_default()    # today's quiz = session S9
    today = quiz.current()
    weak_of = {sid: {c for c, sc in mastery.items() if sc[-1] <= 1} for sid, _n, _m, _t, _p, mastery, _x in PROFILES}
    for sid in ANSWERED_TODAY:
        answers = [(q["correct"] + 1) % 4 if q["concept"] in weak_of[sid] else q["correct"] for q in today["questions"]]
        quiz.submit(today["id"], sid, answers)

    G = load_graph()
    flags = {}
    for sid, _n, _m, _t, _p, mastery, _x in PROFILES:
        for c, sc in mastery.items():
            if sc[-1] <= 1 and c in REASONS:
                f = flags.setdefault(c, {"concept_id": c, "concept_name": G.nodes[c]["name"], "reason": REASONS[c],
                                         "misconception_ids": [MISC_FOR[c]] if c in MISC_FOR else [], "count": 0,
                                         "status": "pending", "first_seen": _ts(5), "last_seen": _ts(0.2)})
                f.setdefault("student_keys", []).append(student_key(sid))
                f["count"] = f["events"] = len(f["student_keys"])
    (DATA / "lecturer_flags.json").write_text(json.dumps(list(flags.values()), indent=2), encoding="utf-8")


def ensure() -> None:
    if not (DATA / "roster.json").exists():
        seed()


def roster() -> list[dict]:
    ensure()
    return json.loads((DATA / "roster.json").read_text(encoding="utf-8"))
