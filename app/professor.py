"""Professor tab: 3 numbers, flags to review (approve/reject), class map on demand."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import altair as alt
import networkx as nx
import pandas as pd
import streamlit as st

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


def render() -> None:
    G = load_graph()
    students = _class_students()
    flags = load_flags()
    pending = [f for f in flags if f["status"] == "pending"]
    weak = Counter(c for s in students for c, m in s["mastery"].items() if band(m["score"]) == "weak")
    hardest = G.nodes[weak.most_common(1)[0][0]]["name"] if weak else "n/a"

    k1, k2, k3 = st.columns(3)
    k1.metric("Topics to review", len(pending))
    k2.metric("Hardest topic in class", hardest)
    k3.metric("Students", len(students), help="Includes 30 synthetic demo students.")

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
