"""Append-only step log: logs/session.jsonl is our testing evidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "session.jsonl"


def log_step(step: str, input=None, output=None, **extra) -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    row = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "step": step,
           "input": input, "output": output, **extra}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
