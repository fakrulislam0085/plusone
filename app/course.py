"""Course structure + the professor's controls (data/course.json, regenerated on reset).

- units: which lecture units exist and whether students can open them (professor locks/unlocks)
- allowed_misconceptions: which catalogue misconceptions Matteo may plant (professor decides)
- announcement: one message from the professor shown on every student's portal
"""
from __future__ import annotations

import json
from pathlib import Path

from tools import MISCONCEPTIONS

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "course.json"

COURSE = {"code": "01PHYDEMO", "name": "Physics I", "cfu": 10, "teacher": "Prof. Bianchi (demo)"}
OTHER_COURSES = [("Mathematical Analysis I", "10 CFU"), ("Linear Algebra and Geometry", "10 CFU"),
                 ("Chemistry", "8 CFU"), ("Computer Sciences", "8 CFU")]
UNITS = [  # only 'newton' has material in this demo
    {"id": "vectors", "title": "Units and vectors", "week": "Weeks 1–2", "has_content": False},
    {"id": "kinematics", "title": "Kinematics", "week": "Weeks 3–5", "has_content": False},
    {"id": "newton", "title": "Newton's laws", "week": "Weeks 6–7", "has_content": True},
    {"id": "energy", "title": "Work and energy", "week": "Weeks 8–9", "has_content": False},
    {"id": "momentum", "title": "Momentum and collisions", "week": "Weeks 10–11", "has_content": False},
    {"id": "rotation", "title": "Rotation", "week": "Weeks 12–13", "has_content": False},
]
DEFAULT = {"unit_status": {"vectors": "done", "kinematics": "done", "newton": "open", "energy": "locked",
                           "momentum": "locked", "rotation": "locked"},
           "allowed_misconceptions": list(MISCONCEPTIONS),
           "announcement": "Quiz for Newton's laws is open until 18:00. Teach Matteo what you miss!"}


def load() -> dict:
    if PATH.exists():
        return json.loads(PATH.read_text(encoding="utf-8"))
    save(json.loads(json.dumps(DEFAULT)))
    return json.loads(json.dumps(DEFAULT))


def save(cfg: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(cfg, indent=1, ensure_ascii=False), encoding="utf-8")


def units() -> list[dict]:
    status = load()["unit_status"]
    return [{**u, "status": status.get(u["id"], "locked")} for u in UNITS]


def set_unit_status(unit_id: str, status: str) -> None:
    cfg = load()
    cfg["unit_status"][unit_id] = status
    save(cfg)


def allowed_misconceptions() -> list[str]:
    return load()["allowed_misconceptions"]


def set_allowed_misconceptions(ids: list[str]) -> None:
    cfg = load()
    cfg["allowed_misconceptions"] = [i for i in ids if i in MISCONCEPTIONS]
    save(cfg)


def announcement() -> str:
    return load().get("announcement", "")


def set_announcement(text: str) -> None:
    cfg = load()
    cfg["announcement"] = text.strip()[:300]
    save(cfg)


def reset() -> None:
    if PATH.exists():
        PATH.unlink()
