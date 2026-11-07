"""Professor console: Class insights · Quiz · Course controls.

Class insights replaces the old heatmap: one row per topic, worst first, a single bar
(to fix / almost / solid / not yet, out of the roster), the most common misconception,
and the AI's flag with Approve / Reject on the same row. Counts, never names.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

import audit
import course
from icons import dot, ic
import quiz as quizmod
import streaks
from graph import band, load_graph
from tools import MISCONCEPTIONS, STUDENTS_DIR, load_flags, set_flag_status

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "materials" / "physics1_newton"
DISCUSSIONS = json.loads((PACK / "group_discussion_prompts.json").read_text(encoding="utf-8"))["prompts"]
BAR = [("weak", "#d64545", "to fix"), ("shaky", "#d9a21b", "almost"), ("solid", "#1f9d55", "solid"),
       ("untested", "#c9ccd1", "not yet")]


def _students() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(STUDENTS_DIR.glob("*.json"))]


def _follow_up(misconception_ids: list[str]) -> str | None:
    for d in DISCUSSIONS:
        if set(d["trigger"]) & set(misconception_ids):
            return f"Group task {d['id']} · {d['title']}"
    return None


def _bar_html(counts: dict, total: int) -> str:
    parts = []
    for key, color, label in BAR:
        n = counts.get(key, 0)
        if n:
            parts.append(f"<div title='{n} {label}' style='flex:{n};background:{color};color:#fff;font-size:.8rem;"
                         f"font-weight:600;text-align:center;line-height:26px'>{n}</div>")
    return (f"<div style='display:flex;height:26px;border-radius:8px;overflow:hidden;background:#eee'>"
            f"{''.join(parts)}</div>")


# ---------------------------------------------------------------- 1 class insights
def insights() -> None:
    G = load_graph()
    students = _students()
    total = len(students)
    today = quizmod.current()
    done_n, size, goal = streaks.class_today(today["id"]) if today else (0, 0, 0)
    flags = {f["concept_id"]: f for f in load_flags()}
    pending = [f for f in flags.values() if f["status"] == "pending"]

    k1, k2, k3 = st.columns(3)
    k1.metric("Today's quiz answered", f"{done_n} of {size}", help=f"Class goal: {goal}.")
    k2.metric("Topics to review", len(pending))
    k3.metric("Class streak", f"{streaks.class_streak()} sessions", help="Grows when 80% answer the session quiz.")

    st.markdown("### Where the class breaks")
    st.markdown("<p class='legend'><span class='dot r'></span>to fix <span class='dot y'></span>almost "
                f"<span class='dot g'></span>solid <span class='dot n'></span>not yet · out of {total} students · "
                "no names</p>", unsafe_allow_html=True)
    rows = []
    for c in G.nodes:
        counts = Counter(band(s["mastery"][c]["score"]) if c in s["mastery"] else "untested" for s in students)
        rows.append((c, counts))
    rows.sort(key=lambda r: (-r[1].get("weak", 0), -r[1].get("shaky", 0)))
    trouble = [r for r in rows if r[1].get("weak", 0)]
    rest = [r for r in rows if not r[1].get("weak", 0)]

    def row(c, counts):
        f = flags.get(c)
        with st.container(border=True):
            a, b, d = st.columns([3, 4, 2], vertical_alignment="center")
            with a:
                st.markdown(f"**{G.nodes[c]['name']}**")
                if f:
                    st.caption(f"AI hypothesis: {f['reason']} · in {f['count']} student(s)")
            with b:
                st.markdown(_bar_html(counts, total), unsafe_allow_html=True)
                if f:
                    tip = _follow_up(f["misconception_ids"])
                    if tip:
                        st.markdown(f"<span class='muted'>{ic('lightbulb', 15)}Suggested: {tip}</span>", unsafe_allow_html=True)
            with d:
                if f and f["status"] == "pending":
                    x, y = st.columns(2)
                    x.button("Approve", key=f"ok_{c}", type="primary", on_click=set_flag_status, args=(c, "approved"))
                    y.button("Reject", key=f"no_{c}", on_click=set_flag_status, args=(c, "rejected"),
                             help="The AI got this wrong")
                elif f:
                    st.markdown(ic("circle-check", 16, "#1f9d55") + "Approved" if f["status"] == "approved"
                                else ic("circle-x", 16, "#d64545") + "Rejected", unsafe_allow_html=True)

    if not trouble:
        st.info("No weak topics yet.")
    for c, counts in trouble:
        row(c, counts)
    with st.expander(f"Other topics ({len(rest)})"):
        for c, counts in rest:
            row(c, counts)


# ---------------------------------------------------------------- 2 quiz
def quiz_page() -> None:
    G = load_graph()
    today = quizmod.current()
    if today:
        res = quizmod.results(today["id"])
        done_n, size, goal = streaks.class_today(today["id"])
        st.markdown(f"### {today['title']}")
        st.caption(f"{len(today['questions'])} questions · {today.get('origin', '')} · answered by {done_n} of "
                   f"{size} · graded by code, never by AI")
        for c, v in sorted(res["per_concept"].items(), key=lambda kv: kv[1]):
            st.markdown(f"{dot('weak' if v < 0.5 else 'shaky' if v < 0.8 else 'solid')}**{G.nodes[c]['name'] if c in G else c}**: "
                        f"{round(v * 100)}% correct")
        with st.expander("See the questions"):
            for i, q in enumerate(today["questions"], 1):
                st.markdown(f"**{i}.** {q['q']}  \nCorrect: **{q['options'][q['correct']]}** · {q['source']}")

    st.markdown("### Create a quiz from lecture material")
    st.caption("Upload slides (PDF or a ZIP of PDFs). The AI drafts questions from that material only; you edit "
               "and publish. Publishing makes it today's quiz for students.")
    up = st.file_uploader("Lecture material", type=["pdf", "zip"])
    use_pack = st.checkbox("Or use the course handout (demo pack)", value=up is None)
    c1, c2 = st.columns([3, 1])
    title = c1.text_input("Quiz title", value="Newton's laws · AI draft")
    n = c2.number_input("Questions", 3, 10, 5)
    if st.button("Generate draft", type="primary"):
        try:
            if up is not None:
                text = quizmod.extract_text(up.name, up.getvalue())
            elif use_pack:
                text = quizmod.extract_text(quizmod.HANDOUT.name, quizmod.HANDOUT.read_bytes())
            else:
                text = None
                st.warning("Upload a file or tick the handout option.")
            if text:
                with st.spinner("Drafting questions from the material (about 15 s)…"):
                    quizmod.generate_draft(text, title, int(n))
                st.rerun()
        except Exception as e:  # keep the app alive, show why
            st.error(f"Couldn't draft a quiz: {e}")
    letters = "ABCD"
    for d in quizmod.drafts():
        with st.container(border=True):
            st.markdown(f"**Draft: {d['title']}** · {len(d['questions'])} questions · edit any cell, then publish")
            rows = [{"Question": q["q"], "A": q["options"][0], "B": q["options"][1], "C": q["options"][2],
                     "D": q["options"][3], "Correct": letters[q["correct"]], "Topic": q["concept"],
                     "Source": q["source"]} for q in d["questions"]]
            edited = st.data_editor(
                pd.DataFrame(rows), key=f"ed_{d['id']}", hide_index=True, num_rows="fixed",
                column_config={"Correct": st.column_config.SelectboxColumn(options=list(letters), required=True),
                               "Topic": st.column_config.SelectboxColumn(options=list(G.nodes) + ["other"])})
            if st.button("Publish to students", key=f"pub_{d['id']}", type="primary"):
                qs = [{**o, "q": r["Question"], "options": [r["A"], r["B"], r["C"], r["D"]],
                       "correct": letters.index(r["Correct"]), "concept": r["Topic"], "source": r["Source"]}
                      for o, r in zip(d["questions"], edited.to_dict("records"))]
                quizmod.save_draft(d["id"], qs)
                quizmod.publish(d["id"])
                st.rerun()


# ---------------------------------------------------------------- 3 course controls
def controls() -> None:
    st.markdown("### Units students can open")
    labels = {"done": "Completed", "open": "Open now", "locked": "Locked"}
    for u in course.units():
        a, b = st.columns([3, 2], vertical_alignment="center")
        a.markdown(f"**{u['title']}** · {u['week']}" + ("" if u["has_content"] else "  \n<span class='muted'>no "
                   "material uploaded in this demo</span>"), unsafe_allow_html=True)
        new = b.segmented_control("Status", list(labels), format_func=labels.get, default=u["status"],
                                  key=f"unit_{u['id']}_{st.session_state.get('sid', 0)}", label_visibility="collapsed")
        if new and new != u["status"]:
            course.set_unit_status(u["id"], new)
            st.rerun()

    st.markdown("### What Matteo may plant today")
    st.caption("Matteo only plants misconceptions you allow, chosen from the course catalogue. Untick one to "
               "stop him using it (e.g. after you covered it in class).")
    allowed = st.multiselect("Allowed misconceptions", list(MISCONCEPTIONS), default=course.allowed_misconceptions(),
                             format_func=lambda m: f"{m}: {MISCONCEPTIONS[m]}", label_visibility="collapsed")
    if st.button("Save Matteo settings", type="primary"):
        course.set_allowed_misconceptions(allowed)
        st.success(f"Saved: Matteo may plant {len(allowed)} of {len(MISCONCEPTIONS)} misconceptions.")

    st.markdown("### Announcement to students")
    text = st.text_area("Shown on every student's home page", value=course.announcement(), max_chars=300)
    if st.button("Post announcement"):
        course.set_announcement(text)
        st.success("Posted.")


# ---------------------------------------------------------------- 0 AI teaching audit (professor only)
def _tell_students(concept_name: str) -> None:
    course.set_announcement(f"Next lecture opens with a short recap of {concept_name}. "
                            "Before class, try teaching it to Matteo: where do you get stuck?")


def audit_page() -> None:
    if st.session_state.get("user") != "prof":   # access guard in code, not only in the menu
        st.error("The teaching audit is available to the course professor only.")
        return
    G = load_graph()
    doc = audit.load()
    current_hash = audit.evidence()["hash"]

    st.markdown(
        f"<div class='audit-hero'><div class='eyebrow'>{ic('sparkles', 15, '#9be15d')}AI teaching audit · professor only</div>"
        "<div class='ah-title'>What should I recap in the next lecture?</div>"
        "<div class='ah-sub'>Matteo reads the anonymous class evidence (levels per topic, quiz results, flags you "
        "approved) and drafts a recap plan. Suggestions only: you decide.</div></div>", unsafe_allow_html=True)

    a, b, _ = st.columns([2, 2, 5])
    label = "Generate audit" if not doc else "Regenerate"
    if a.button(label, type="primary", key="gen_audit", width="stretch"):
        with st.spinner("Reading the class evidence and drafting a recap plan (about 15 s)…"):
            audit.generate()
        st.rerun()
    if not doc:
        st.info("No audit yet. Click **Generate audit** to analyse today's class data.")
        return
    b.download_button("Download recap plan", audit.markdown(doc), file_name="recap_plan_newtons_laws.md",
                      mime="text/markdown", key="dl_audit", width="stretch")
    if doc["evidence_hash"] != current_hash:
        st.warning("New class activity since this audit. Regenerate to include it.")

    au = doc["audit"]
    with st.container(border=True):
        st.markdown(f"#### {au['headline']}")   # AI text: plain markdown, never raw HTML
    st.caption(f"Generated {doc['generated_at']} · {doc['generated_by']} · anonymous data from {doc['class_size']} "
               "students (synthetic demo class + live sessions)")

    html_map, h = audit.mindmap_html(doc)
    st.iframe(html_map, height=h)

    st.markdown(f"### {ic('clipboard-check', 22)}Recap plan for the next lecture", unsafe_allow_html=True)
    for i, p in enumerate(au["priorities"], 1):
        c, r = p["concept_id"], p["recap"]
        name = G.nodes[c]["name"]
        planned = c in doc["planned"]
        with st.container(border=True):
            left, right = st.columns([5, 2], gap="large")
            with left:
                sev = "high" if p["severity"] == "high" else "medium"
                st.markdown(f"<span class='sevchip {sev}'>{'High' if sev == 'high' else 'Medium'} priority</span>"
                            f"<span class='minchip'>{r['minutes']} min</span>", unsafe_allow_html=True)
                st.markdown(f"#### {i}. {name}")
                st.markdown(f"**Evidence:** {p['evidence']}")
                if p["misconception_id"]:
                    st.markdown(f"**Misconception to address:** {MISCONCEPTIONS[p['misconception_id']]}")
                if p["teach_first"]:
                    st.markdown(f"**May be rooted in:** {G.nodes[p['teach_first']]['name']}. Recap that first.")
                st.markdown(f"**Open with:** {r['hook']}")
                st.markdown("\n".join(f"{j}. {s}" for j, s in enumerate(r["steps"], 1)))
                st.markdown(f"**Check question:** {r['check_question']}")
                if r["group_task_id"]:
                    t = audit.TASKS[r["group_task_id"]]
                    st.markdown(f"**Group task {t['id']} · {t['title']}:** {t['question']}")
                st.caption(f"Source to revisit: {G.nodes[c]['source']}")
            with right:
                st.button("Planned for next lecture" if planned else "Add to next lecture", key=f"plan_{c}",
                          type="secondary" if planned else "primary", width="stretch",
                          on_click=audit.toggle_planned, args=(c,))
                st.button("Tell students", key=f"tell_{c}", width="stretch", on_click=_tell_students, args=(name,),
                          help="Posts an announcement on every student's home page.")
                if planned:
                    st.markdown(f"<span class='muted'>{ic('circle-check', 15, '#1f9d55')}On your next-lecture plan</span>",
                                unsafe_allow_html=True)
    if au["going_well"]:
        st.markdown(f"{ic('circle-check', 18, '#1f9d55')}**Going well:** "
                    + ", ".join(G.nodes[c]["name"] for c in au["going_well"]), unsafe_allow_html=True)
    if au["caveat"]:
        st.caption(au["caveat"])


def render() -> None:
    sections = ["AI teaching audit", "Class insights", "Quiz", "Course controls"]
    section = st.segmented_control("Section", sections, default="AI teaching audit",
                                   key="prof_section", label_visibility="collapsed") or "AI teaching audit"
    {"AI teaching audit": audit_page, "Class insights": insights, "Quiz": quiz_page, "Course controls": controls}[section]()
