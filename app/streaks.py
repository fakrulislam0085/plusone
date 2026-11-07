"""Streaks (from the StreakTA prototype): personal, team and class streaks per lecture session.

A *session* = one lecture with its quiz. You keep your streak by answering each session's quiz.
- personal streak: consecutive sessions you answered, ending at the latest one you could answer
- team streak:     consecutive sessions where EVERY group member answered
- class streak:    consecutive sessions where >= 80% of the class answered
No public individual leaderboard (design choice: rank groups, never individuals).
Past sessions S1-S8 are SYNTHETIC demo history (data/streaks.json is regenerated on reset).
"""
from __future__ import annotations

import json
from pathlib import Path

from tools import slug

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "streaks.json"
CLASS_SIZE = 30
CLASS_GOAL = 0.8

PAST = ["Units and vectors", "Motion in 1D", "Motion in 2D", "Projectiles", "Circular motion",
        "Relative motion", "What is a force?", "Mass and weight"]
SEED_ANSWERED = {  # synthetic history so the demo shows real-looking streaks
    "you": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"],
    "alex": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"],
    "bea": ["S3", "S4", "S5", "S6", "S7", "S8"],
    "chris": ["S1", "S2", "S4", "S5", "S6", "S7", "S8"],
    "dani": ["S5", "S6", "S7", "S8"],
}
SEED_CLASS = {"S1": 26, "S2": 25, "S3": 27, "S4": 22, "S5": 25, "S6": 26, "S7": 24, "S8": 25}
TODAY_BASELINE = 21  # synthetic classmates who already answered today's quiz


def _load() -> dict:
    if PATH.exists():
        return json.loads(PATH.read_text(encoding="utf-8"))
    data = {"synthetic_note": "S1-S8 and class counts are synthetic demo history.",
            "sessions": [{"id": f"S{i}", "title": t} for i, t in enumerate(PAST, 1)],
            "answered": {k: list(v) for k, v in SEED_ANSWERED.items()},
            "class_answered": dict(SEED_CLASS)}
    _save(data)
    return data


def _save(data: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def ensure_session(session_id: str, title: str) -> None:
    """Register today's quiz as the newest session (idempotent)."""
    data = _load()
    if session_id not in [s["id"] for s in data["sessions"]]:
        data["sessions"].append({"id": session_id, "title": title})
        data["class_answered"].setdefault(session_id, TODAY_BASELINE)
        _save(data)


def record(student: str, session_id: str) -> None:
    data = _load()
    done = data["answered"].setdefault(slug(student), [])
    if session_id not in done:
        done.append(session_id)
        data["class_answered"][session_id] = data["class_answered"].get(session_id, TODAY_BASELINE) + 1
        _save(data)


def _run(ok) -> int:
    """Length of the run of sessions (newest first) satisfying ok(id); today's still-open session
    doesn't break a streak if it isn't done yet."""
    sessions = [s["id"] for s in _load()["sessions"]]
    n, first = 0, True
    for sid in reversed(sessions):
        if ok(sid):
            n += 1
        elif first:      # today's session not done yet: streak still alive
            pass
        else:
            break
        first = False
    return n


def streak(student: str) -> int:
    done = set(_load()["answered"].get(slug(student), []))
    return _run(lambda sid: sid in done)


def answered(student: str, session_id: str) -> bool:
    return session_id in _load()["answered"].get(slug(student), [])


def team_streak(members: list[str]) -> int:
    data = _load()
    sets = [set(data["answered"].get(slug(m), [])) for m in members]
    return _run(lambda sid: all(sid in s for s in sets))


def class_streak() -> int:
    counts = _load()["class_answered"]
    return _run(lambda sid: counts.get(sid, 0) >= CLASS_GOAL * CLASS_SIZE)


def class_today(session_id: str) -> tuple[int, int, int]:
    """(answered, class size, needed for the class goal)"""
    n = _load()["class_answered"].get(session_id, TODAY_BASELINE)
    return n, CLASS_SIZE, int(CLASS_GOAL * CLASS_SIZE + 0.999)


def reset() -> None:
    if PATH.exists():
        PATH.unlink()
