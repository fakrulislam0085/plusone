"""Seed a SYNTHETIC class of 30 students for the professor view -> data/class_seed.json

  .venv\\Scripts\\python scripts/seed_demo.py

Clearly synthetic demo data (fixed random seed). Not real students, not measured results.
Weak spots are set where physics-education research says first-year students usually struggle
(third-law pairs, static friction, motion-needs-force), so the heatmap tells a plausible story.
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from graph import load_graph  # noqa: E402

# probability of (untested, weak 0-1, shaky 2, solid 3) per concept
PROFILE = {
    "force_interaction":        (0.10, 0.15, 0.30, 0.45),
    "net_force":                (0.10, 0.15, 0.30, 0.45),
    "velocity_vs_acceleration": (0.10, 0.25, 0.30, 0.35),
    "mass_inertia":             (0.15, 0.20, 0.30, 0.35),
    "newton_first_law":         (0.05, 0.30, 0.30, 0.35),
    "newton_second_law":        (0.05, 0.20, 0.35, 0.40),
    "system_boundary":          (0.30, 0.30, 0.25, 0.15),
    "newton_third_law":         (0.05, 0.50, 0.25, 0.20),
    "free_body_diagram":        (0.15, 0.35, 0.30, 0.20),
    "weight_normal":            (0.15, 0.10, 0.30, 0.45),
    "static_friction":          (0.20, 0.45, 0.25, 0.10),
    "kinetic_friction":         (0.30, 0.20, 0.30, 0.20),
    "incline":                  (0.35, 0.25, 0.25, 0.15),
}
MISCONCEPTION_FOR_WEAK = {
    "newton_first_law": "MOTION_NEEDS_FORCE", "newton_third_law": "THIRD_LAW_UNEQUAL",
    "static_friction": "STATIC_FRICTION_MAX", "free_body_diagram": "FBD_PAIR",
    "mass_inertia": "MASS_ACCEL", "net_force": "NET_VS_APPLIED",
    "velocity_vs_acceleration": "VELOCITY_FORCE", "incline": "INCLINE_COMPONENT",
    "system_boundary": "SYSTEM_BOUNDARY",
}


def main() -> None:
    G = load_graph()
    assert set(PROFILE) == set(G.nodes), "PROFILE must cover every graph concept"
    rng = random.Random(7)
    students = []
    for i in range(1, 31):
        mastery, miscs = {}, []
        for cid, probs in PROFILE.items():
            bucket = rng.choices(["untested", "weak", "shaky", "solid"], probs)[0]
            if bucket == "untested":
                continue
            score = {"weak": rng.choice([0, 1]), "shaky": 2, "solid": 3}[bucket]
            mastery[cid] = {"score": score, "status": rng.choice(["confirmed", "needs_confirmation"])}
            if bucket == "weak" and cid in MISCONCEPTION_FOR_WEAK and rng.random() < 0.7:
                miscs.append(MISCONCEPTION_FOR_WEAK[cid])
        students.append({"student_id": f"synthetic_{i:02d}", "mastery": mastery, "misconceptions_seen": miscs})
    out = {"synthetic": True, "note": "Synthetic demo class (random seed 7). Not real students.",
           "students": students}
    (ROOT / "data" / "class_seed.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote data/class_seed.json with {len(students)} synthetic students")


if __name__ == "__main__":
    main()
