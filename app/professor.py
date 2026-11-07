"""Professor tab: 3 numbers, flags to review (approve/reject), class map on demand."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import altair as alt
import networkx as nx
import pandas as pd
import streamlit as st

import quiz as quizmod
import streaks
from graph import COLORS, band, load_graph
from tools import MISCONCEPTIONS, STUDENTS_DIR, load_flags, set_flag_status

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "materials" / "physics1_newton"
SEED = ROOT / "data" / "class_seed.json"
DISCUSSIONS = json.loads((PACK / "group_discussion_prompts.json").read_text(encoding="utf-8"))["prompts"]
BAND_LABEL = {"untested": "Not yet", "weak": "To fix", "shaky": "Almost", "solid": "Explained well"}


def _class_students() -> list[dict]:
    rows = []
    if SEED.exists():
        for s in json.loads(SEED.read_text(encoding="utf-8"))["students"]:
            rows.append({"label": s["student_id"].replace("synthetic_", "S"), "kind": "synthetic", **s})
    for i, p in enumerate(sorted(STUDENTS_DIR.glob("*.json")), 1):
        s = json.loads(p.read_text(encoding="utf-8"))
        rows.append({"label": f"Live {i}", "kind": "live", **s})  # anonymized: no names
    return rows


def _follow_up(misconception_ids: list[str]) -> str | None:
    for d in DISCUSSIONS:
        if set(d["trigger"]) & set(misconception_ids):
            return f"Run group task {d['id']}, “{d['title']}”, in the next lecture."
    return None


def _quiz_section(G, today: dict | None) -> None:
    st.markdown("### Today's quiz")
    if today:
        res = quizmod.results(today["id"])
        done_n, size, goal = streaks.class_today(today["id"])
        st.caption(f"**{today['title']}** · {len(today['questions'])} questions · {today.get('origin', '')} · "
                   f"answered by {done_n} of {size} (live answers: {res['n']}; others synthetic)")
        if res["per_concept"]:
            worst = sorted(res["per_concept"].items(), key=lambda kv: kv[1])
            st.markdown("  \n".join(f"{'🟥' if v < 0.5 else '🟨' if v < 0.8 else '🟩'} "
                                    f"{G.nodes[c]['name'] if c in G else c}: {round(v * 100)}% correct"
                                    for c, v in worst))
        else:
            st.caption("No live answers yet.")

    with st.expander("Create a quiz from lecture material"):
        st.caption("Upload slides (PDF or ZIP of PDFs). The AI drafts questions from that material only; "
                   "you edit and publish. Students never see the answers before they've answered.")
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
                    st.warning("Upload a file or tick the handout option.")
                    text = None
                if text:
                    with st.spinner("Drafting questions from the material (about 20 s)…"):
                        quizmod.generate_draft(text, title, int(n))
                    st.rerun()
            except Exception as e:  # show the reason, keep the app alive
                st.error(f"Couldn't draft a quiz: {e}")

        for d in quizmod.drafts():
            st.markdown(f"**Draft: {d['title']}** ({len(d['questions'])} questions). Edit cells, then publish.")
            letters = "ABCD"
            rows = [{"Question": q["q"], "A": q["options"][0], "B": q["options"][1], "C": q["options"][2],
                     "D": q["options"][3], "Correct": letters[q["correct"]], "Topic": q["concept"],
                     "Source": q["source"]} for q in d["questions"]]
            edited = st.data_editor(
                pd.DataFrame(rows), key=f"ed_{d['id']}", hide_index=True, num_rows="fixed",
                column_config={"Correct": st.column_config.SelectboxColumn(options=list(letters), required=True),
                               "Topic": st.column_config.SelectboxColumn(options=list(G.nodes) + ["other"])})
            if st.button("Publish to students", key=f"pub_{d['id']}", type="primary"):
                qs = []
                for i, (orig, row) in enumerate(zip(d["questions"], edited.to_dict("records"))):
                    qs.append({**orig, "q": row["Question"], "options": [row["A"], row["B"], row["C"], row["D"]],
                               "correct": letters.index(row["Correct"]), "concept": row["Topic"],
                               "source": row["Source"]})
                quizmod.save_draft(d["id"], qs)
                quizmod.publish(d["id"])
                st.success("Published. It is now today's quiz in the Student tab.")
                st.rerun()


def render() -> None:
    G = load_graph()
    students = _class_students()
    flags = load_flags()
    pending = [f for f in flags if f["status"] == "pending"]
    weak = Counter(c for s in students for c, m in s["mastery"].items() if band(m["score"]) == "weak")
    hardest = G.nodes[weak.most_common(1)[0][0]]["name"] if weak else "n/a"

    today = quizmod.current()
    done_n, size, goal = streaks.class_today(today["id"]) if today else (0, 0, 0)
    k1, k2, k3 = st.columns(3)
    k1.metric("Topics to review", len(pending))
    k2.metric("Hardest topic in class", hardest)
    k3.metric("Class streak", f"🔥 {streaks.class_streak()} sessions",
              help=f"Grows when at least 80% of the class answers the session quiz. "
                   f"Today: {done_n} of {size} answered (goal {goal}). Past sessions are synthetic.")

    st.markdown("### To review")
    st.caption("Topics students got wrong. Anonymous: no names, no quotes. You decide.")
    if not pending:
        st.info("Nothing to review. Teach Matteo something wrong in the Student tab, then come back.")
    for f in sorted(pending, key=lambda f: -f["count"]):
        with st.container(border=True):
            st.markdown(f"**{f['concept_name']}** · seen {f['count']}×  \n{f['reason']}")
            tip = _follow_up(f["misconception_ids"])
            if tip:
                st.caption(f"💡 {tip}")
            a, r, _ = st.columns([1, 1, 9], gap="small")
            if a.button("Approve", key=f"ok_{f['concept_id']}", type="primary"):
                set_flag_status(f["concept_id"], "approved")
                st.rerun()
            if r.button("Reject", key=f"no_{f['concept_id']}", help="The AI got this wrong"):
                set_flag_status(f["concept_id"], "rejected")
                st.rerun()

    done = [f for f in flags if f["status"] != "pending"]
    if done:
        with st.expander(f"Reviewed ({len(done)})"):
            for f in done:
                st.markdown(f"{'✅' if f['status'] == 'approved' else '❌'} {f['concept_name']}")

    _quiz_section(G, today)

    with st.expander("Class map: where the class breaks"):
        order = list(reversed(list(nx.topological_sort(G))))
        rows = [{"Student": s["label"], "Topic": G.nodes[c]["name"],
                 "Level": BAND_LABEL[band(s["mastery"][c]["score"]) if c in s["mastery"] else "untested"]}
                for s in students for c in order]
        scale = alt.Scale(domain=list(BAND_LABEL.values()), range=[COLORS[k] for k in BAND_LABEL])
        chart = (alt.Chart(pd.DataFrame(rows)).mark_rect(cornerRadius=3, stroke="white", strokeWidth=1.5)
                 .encode(x=alt.X("Student:N", sort=None, axis=alt.Axis(labelAngle=-60, title=None)),
                         y=alt.Y("Topic:N", sort=[G.nodes[c]["name"] for c in order], title=None),
                         color=alt.Color("Level:N", scale=scale, legend=alt.Legend(orient="top", title=None)),
                         tooltip=["Student", "Topic", "Level"])
                 .properties(height=400))
        st.altair_chart(chart, width="stretch")
        st.caption("S01–S30 are synthetic demo students; “Live” are real sessions, anonymized.")
        top = Counter(m if isinstance(m, str) else m["id"] for s in students for m in s.get("misconceptions_seen", []))
        if top:
            mid, n = top.most_common(1)[0]
            st.caption(f"Most common misconception: {MISCONCEPTIONS.get(mid, mid)} ({n}×)")
