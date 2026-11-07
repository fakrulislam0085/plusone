"""Reset the demo to its realistic starting state (10 SYNTHETIC students):  python scripts/seed_demo.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import demo_data  # noqa: E402

demo_data.seed()
print("seeded: 10 synthetic students, sessions S1-S9, today's quiz + 6 answers, flags, course settings")
