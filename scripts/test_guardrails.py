"""Offline guardrail test (no API calls):  .venv\\Scripts\\python scripts/test_guardrails.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from guardrails import check  # noqa: E402

MUST_BLOCK = [
    "The answer is that both forces are equal and opposite.",
    "Newton's third law states that every action has an equal and opposite reaction.",
    "Let me explain: the net force is 6 N, so the acceleration is 3 m/s².",
    "Step 1: add the forces. Step 2: divide by the mass.",
    "Net force = 10 - 4 = 6 N, and a = 6 / 2 = 3 m/s².",
    "You should draw a free-body diagram first and then sum the forces.",
    "Here's how it works: static friction adjusts up to its maximum.",
    "In summary, the puck keeps moving because no net force acts on it.",
    "The correct answer is B.",
    "Hmm " * 85,  # too long
]
MUST_PASS = [
    "I don't know, that's literally why I'm asking you! So does the car push back on the truck at all?",
    "Ohh wait, so the truck pushes harder on the car because it's heavier, right?",
    "Bea, do you agree with what Alex said about the puck?",
    "Okay that clicked! So if the forces cancel, it just keeps going? But why does my phone stop on the desk?",
    "Hmm, but if I push a box with 12 N and it doesn't move, is there even any friction?",
]

fails = 0
for text in MUST_BLOCK:
    ok, reason = check(text)
    status = "BLOCKED" if not ok else "!! LEAKED"
    fails += ok
    print(f"{status:9} | {reason:28} | {text[:70]}")
for text in MUST_PASS:
    ok, reason = check(text)
    status = "passed" if ok else "!! FALSE BLOCK"
    fails += not ok
    print(f"{status:9} | {reason:28} | {text[:70]}")
print("\nGUARDRAIL TESTS:", "ALL OK" if fails == 0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
