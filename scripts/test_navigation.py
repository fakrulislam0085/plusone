"""Exhaustive navigation test (40 steps, ~3 real API calls):  python scripts/test_navigation.py
Resets the demo data before and after."""
import json
import sys
import traceback

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from streamlit.testing.v1 import AppTest  # noqa: E402

import demo_data  # noqa: E402

demo_data.seed()
problems = []


def btn(at, start, i=0):
    m = [b for b in at.button if b.label.strip().startswith(start)]
    if not m:
        raise AssertionError(f"no button starting {start!r}; have {[b.label for b in at.button]}")
    return m[i]


def unit_btn(at):
    return [b for b in at.button if b.key and b.key.startswith("unit_newton")][0]


def step(at, name, expect_stage=None, expect_page=None):
    ss = at.session_state
    bad = []
    if at.exception:
        bad.append("EXCEPTION: " + at.exception[0].message[:200])
    if expect_stage and ss["stage"] != expect_stage:
        bad.append(f"stage={ss['stage']} expected {expect_stage}")
    if expect_page and ss["page"] != expect_page:
        bad.append(f"page={ss['page']} expected {expect_page}")
    print(f"{'FAIL' if bad else 'ok  '} | {name:52} page={ss['page']:6} stage={ss['stage']:8} {'; '.join(bad)}")
    if bad:
        problems.append((name, bad))


def run(name, fn):
    try:
        fn()
    except Exception as e:  # report and continue with the next scenario
        problems.append((name, [repr(e)[:200]]))
        print(f"FAIL | {name}: {e!r}"[:260])
        traceback.print_exc(limit=1)


def fresh():
    demo_data.seed()
    at = AppTest.from_file(str(ROOT / "app" / "main.py"), default_timeout=180)
    at.run()
    return at


def s1():  # solo, back/forward, leave and return mid-session
    at = fresh(); step(at, "open home", expect_page="home")
    btn(at, "Open").click().run(); step(at, "home -> course", expect_page="course")
    unit_btn(at).click().run(); step(at, "course -> unit", "start", "unit")
    print("     start buttons:", [b.label.strip() for b in at.button if b.key and "start_" in b.key])
    btn(at, "Study on my own").click().run(); step(at, "card: on my own -> quiz", "quiz")
    btn(at, "←  Back").click().run(); step(at, "quiz back -> start", "start")
    btn(at, "Study on my own").click().run(); step(at, "start again -> quiz", "quiz")
    btn(at, "Skip quiz").click().run(); step(at, "skip quiz -> teach", "teach")
    fc = [b for b in at.button if b.label.strip().startswith("Final check")]
    print("     final check locked before teaching:", fc and fc[0].disabled)
    btn(at, "Physics I").click().run(); step(at, "left menu Physics I mid-session", expect_page="course")
    unit_btn(at).click().run(); step(at, "reopen unit -> resumes teach", "teach", "unit")
    btn(at, "Home").click().run(); step(at, "left menu Home mid-session", expect_page="home")
    btn(at, "Open").click().run(); unit_btn(at).click().run(); step(at, "back into unit", "teach", "unit")
    at.chat_input[0].set_value("Newton's first law: with zero net force, velocity stays constant.").run()
    step(at, "teach 1 turn (live)", "teach")
    fc = [b for b in at.button if b.label.strip().startswith("Final check")]
    print("     final check unlocked after teaching:", fc and not fc[0].disabled)
    btn(at, "Final check").click().run(); step(at, "-> final check", "check")
    btn(at, "←  Keep teaching").click().run(); step(at, "check back -> teach", "teach")
    btn(at, "Final check").click().run(); btn(at, "Skip for now").click().run(); step(at, "skip check -> summary", "summary")
    btn(at, "←  Keep teaching").click().run(); step(at, "summary back -> teach", "teach")
    btn(at, "Final check").click().run(); btn(at, "Skip for now").click().run()
    btn(at, "Back to Physics I").click().run(); step(at, "summary -> course", expect_page="course")
    unit_btn(at).click().run(); step(at, "reopen after finish -> fresh start", "start", "unit")


def s2():  # switch user mid-session
    at = fresh()
    btn(at, "Open").click().run(); unit_btn(at).click().run(); btn(at, "Study on my own").click().run()
    at.selectbox[0].set_value("alex").run(); step(at, "switch to Alex mid-quiz -> home fresh", "start", "home")
    btn(at, "Open").click().run(); unit_btn(at).click().run(); btn(at, "Study on my own").click().run()
    print("     Alex sees previous result:", at.session_state["quiz_results"].get("Alex", {}).get("score"))
    step(at, "Alex quiz (already answered)", "quiz")
    at.selectbox[0].set_value("prof").run(); step(at, "switch to professor", "start", "home")
    btn(at, "Open").click().run(); step(at, "professor -> console", expect_page="course")
    at.selectbox[0].set_value("giulia").run(); step(at, "back to Giulia", "start", "home")


def s3():  # group: quiz taker, skip, speakers, check gating
    at = fresh()
    at.selectbox[0].set_value("alex").run(); btn(at, "Open").click().run(); unit_btn(at).click().run()
    btn(at, "Study with Team A").click().run(); step(at, "card: study group -> quiz", "quiz")
    print("     participants:", at.session_state["participants"], "| already answered:", list(at.session_state["quiz_results"]))
    print("     taker options:", [r.options for r in at.radio if r.label.startswith("Who is taking")])
    btn(at, "Teach Matteo").click().run(); step(at, "group -> teach (some answered)", "teach")
    print("     speaker options:", [r.options for r in at.radio if r.label.startswith("Who's speaking")])
    btn(at, "←  Back to quiz").click().run(); step(at, "group back to quiz", "quiz")
    btn(at, "←  Back").click().run(); step(at, "group back to start", "start")
    btn(at, "Study on my own").click().run(); step(at, "switch to solo after group", "quiz")
    print("     participants now:", at.session_state["participants"])


def s4():  # professor locks unit while a student is inside; reset restores
    at = fresh()
    btn(at, "Open").click().run(); unit_btn(at).click().run(); btn(at, "Study on my own").click().run()
    import course
    course.set_unit_status("newton", "locked")
    at.run(); step(at, "unit locked while student inside", "quiz", "unit")
    print("     warning shown:", [w.value[:60] for w in at.warning])
    btn(at, "Physics I").click().run()
    print("     card now:", [(b.label, b.disabled) for b in at.button if b.key and b.key.startswith("unit_newton")])
    at.selectbox[0].set_value("prof").run(); btn(at, "Open").click().run()
    at.segmented_control[0].set_value("Course controls").run(); step(at, "prof course controls")
    btn(at, "Reset demo").click().run(); step(at, "reset demo from console", "start", "home")
    btn(at, "Open").click().run(); at.segmented_control[0].set_value("Course controls").run()
    print("     after reset, newton status:", next(u["status"] for u in course.units() if u["id"] == "newton"))
    step(at, "controls after reset (no re-lock)")


def s5():  # professor sections, flags, audit actions, student sees announcement
    at = fresh()
    at.selectbox[0].set_value("prof").run(); btn(at, "Open").click().run()
    for sec in ["Class insights", "Quiz", "Course controls", "AI teaching audit"]:
        at.segmented_control[0].set_value(sec).run(); step(at, f"prof section {sec}")
    at.segmented_control[0].set_value("Class insights").run()
    n = len([b for b in at.button if b.label == "Approve"])
    btn(at, "Approve").click().run(); step(at, "approve a flag")
    print("     approve buttons before/after:", n, len([b for b in at.button if b.label == "Approve"]))
    at.segmented_control[0].set_value("AI teaching audit").run()
    btn(at, "Generate audit").click().run(); step(at, "generate audit (live AI)")
    btn(at, "Tell students").click().run(); btn(at, "Add to next lecture").click().run(); step(at, "audit actions")
    at.selectbox[0].set_value("giulia").run(); step(at, "student home after announcement", expect_page="home")
    print("     student sees:", [m.value[:70] for m in at.markdown if "recap" in m.value.lower()][:1])


for name, fn in [("solo flow", s1), ("switch user", s2), ("group flow", s3), ("lock unit + reset", s4), ("professor", s5)]:
    print(f"\n=== {name}")
    run(name, fn)
print("\nPROBLEMS:", json.dumps(problems, indent=1) if problems else "none")
demo_data.seed()
