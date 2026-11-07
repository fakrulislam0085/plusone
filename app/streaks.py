"""Streaks (from the StreakTA prototype): personal, team and class streaks per lecture session.

A *session* = one lecture with its quiz; you keep your streak by answering each session's quiz.
- personal: consecutive sessions you answered (today's open session doesn't break it)
- team:     consecutive sessions where EVERY team member answered
- class:    consecutive sessions where >= 80% of the roster answered
Everything is computed from data/streaks.json (written by scripts/seed_demo.py; synthetic history).
No public individual leaderboard: we rank groups, never individuals.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools import slug

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "streaks.json"
ROSTER = ROOT / "data" / "roster.json"
CLASS_GOAL = 0.8


def _load() -> dict:
    if PATH.exists():
        return json.loads(PATH.read_text(encoding="utf-8"))
    return {"sessions": [], "answered": {}}


def _save(data: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def roster() -> list[dict]:
    return json.loads(ROSTER.read_text(encoding="utf-8")) if ROSTER.exists() else []


def ensure_session(session_id: str, title: str) -> None:
    data = _load()
    if session_id not in [s["id"] for s in data["sessions"]]:
        data["sessions"].append({"id": session_id, "title": title})
        _save(data)


def record(student: str, session_id: str) -> None:
    data = _load()
    done = data["answered"].setdefault(slug(student), [])
    if session_id not in done:
        done.append(session_id)
        _save(data)


def _run(ok) -> int:
    n, first = 0, True
    for s in reversed(_load()["sessions"]):
        if ok(s["id"]):
            n += 1
        elif not first:
            break
        first = False
    return n


def answered(student: str, session_id: str) -> bool:
    return session_id in _load()["answered"].get(slug(student), [])


def streak(student: str) -> int:
    done = set(_load()["answered"].get(slug(student), []))
    return _run(lambda sid: sid in done)


def team_streak(members: list[str]) -> int:
    data = _load()
    sets = [set(data["answered"].get(slug(m), [])) for m in members]
    return _run(lambda sid: all(sid in s for s in sets)) if sets else 0


def class_today(session_id: str) -> tuple[int, int, int]:
    """(answered, roster size, needed for the class goal)"""
    ids = [r["id"] for r in roster()]
    data = _load()
    n = sum(1 for i in ids if session_id in data["answered"].get(i, []))
    return n, len(ids), int(CLASS_GOAL * len(ids) + 0.999)


def class_streak() -> int:
    ids = [r["id"] for r in roster()]
    if not ids:
        return 0
    data = _load()
    return _run(lambda sid: sum(sid in data["answered"].get(i, []) for i in ids) >= CLASS_GOAL * len(ids))


def reset() -> None:
    if PATH.exists():
        PATH.unlink()
