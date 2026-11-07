"""Professor tab: where the class breaks + anonymized flags with human approve/reject."""
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
QUIZ = {q["id"]: q for q in json.loads((PACK / "quiz_student.json").read_text(encoding="utf-8"))["items"]}
BAND_LABEL = {"untested": "Untested", "weak": "Weak (0–1)", "shaky": "Shaky (2)", "solid": "Solid (3)"}


def _class_students() -> list[dict]:
    rows = []
    if SEED.exists():
        for s in json.loads(SEED.read_text(encoding="utf-8"))["students"]:
            rows.append({"label": s["student_id"].replace("synthetic_", "S"), "kind": "synthetic", **s})
    for i, p in enumerate(sorted(STUDENTS_DIR.glob("*.json")), 1):
        s = json.loads(p.read_text(encoding="utf-8"))
        rows.append({"label": f"Live {i}", "kind": "live", **s})  # anonymized: no names
    return rows


def _follow_ups(misconception_ids: list[str], concept_id: str) -> tuple[list[dict], list[dict]]:
    discussions = [d for d in DISCUSSIONS if set(d["trigger"]) & set(misconception_ids)]
    G = load_graph()
    quiz = [QUIZ[q] for q in G.nodes[concept_id].get("quiz", []) if q in QUIZ] if concept_id in G else []
    return discussions, quiz


def render() -> None:
    G = load_graph()
    order = list(reversed(list(nx.topological_sort(G))))  # prerequisites first
    students = _class_students()
    n_syn = sum(s["kind"] == "synthetic" for s in students)
    n_live = len(students) - n_syn

    st.markdown('<div class="eyebrow">Professor view · Physics I · Newton\'s laws</div>', unsafe_allow_html=True)
    st.markdown("### Where the class breaks")
    st.caption(f"{n_syn} synthetic demo students + {n_live} live session(s). Counts of explanations, "
               "not grades. Weak spots stay hypotheses until confirmed twice.")

    rows, weak_counts = [], Counter()
    for s in students:
        for cid in order:
            m = s["mastery"].get(cid)
            b = band(m["score"]) if m else "untested"
            rows.append({"Student": s["label"], "Concept": G.nodes[cid]["name"], "Level": BAND_LABEL[b],
                         "kind": s["kind"]})
            if b == "weak":
                weak_counts[cid] += 1
    df = pd.DataFrame(rows)
    scale = alt.Scale(domain=list(BAND_LABEL.values()), range=[COLORS[k] for k in BAND_LABEL])
    heat = (alt.Chart(df).mark_rect(cornerRadius=3, stroke="white", strokeWidth=1.5)
            .encode(x=alt.X("Student:N", sort=None, axis=alt.Axis(labelAngle=-60, title=None)),
                    y=alt.Y("Concept:N", sort=[G.nodes[c]["name"] for c in order], title=None),
                    color=alt.Color("Level:N", scale=scale, legend=alt.Legend(orient="top", title=None)),
                    tooltip=["Student", "Concept", "Level"])
            .properties(height=420))
    st.altair_chart(heat, width="stretch")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("#### Most fragile concepts")
        for cid, n in weak_counts.most_common(4):
            tested = sum(1 for s in students if cid in s["mastery"])
            st.markdown(f"**{G.nodes[cid]['name']}**: weak in {n} of {tested} tested explanations  \n"
                        f"<span class='muted'>Source: {G.nodes[cid]['source']}</span>", unsafe_allow_html=True)
    with c2:
        st.markdown("#### Most common misconceptions")
        mc = Counter(m for s in students for m in
                     [x if isinstance(x, str) else x["id"] for x in s.get("misconceptions_seen", [])])
        for mid, n in mc.most_common(4):
            st.markdown(f"**{n}×** `{mid}`  \n<span class='muted'>{MISCONCEPTIONS.get(mid, '')}</span>",
                        unsafe_allow_html=True)

    st.divider()
    st.markdown("### Flags from live sessions")
    st.caption("Anonymized: no names, no quotes. The AI proposes, the professor decides.")
    flags = sorted(load_flags(), key=lambda f: (f["status"] != "pending", -f["count"]))
    if not flags:
        st.info("No live flags yet. Teach Matteo something wrong and come back.")
    for f in flags:
        discussions, quiz = _follow_ups(f["misconception_ids"], f["concept_id"])
        with st.container(border=True):
            badge = {"pending": "🟡 Pending review", "approved": "✅ Approved",
                     "rejected": "❌ Rejected (AI was wrong)"}[f["status"]]
            st.markdown(f"**{f['concept_name']}** · {badge} · seen {f['count']}×")
            st.markdown(f"**Claim:** {f['reason']}")
            for mid in f["misconception_ids"]:
                st.caption(f"`{mid}`: {MISCONCEPTIONS.get(mid, '')}")
            st.markdown("**Uncertainty:** inferred from short chat explanations; treat as a hypothesis, "
                        "not a grade." + (f" Confirm with check question {', '.join(q['id'] for q in quiz)}."
                                          if quiz else ""))
            if discussions:
                d = discussions[0]
                st.markdown(f"**Suggested follow-up:** run group task **{d['id']} · {d['title']}** in the next "
                            f"lecture.  \n<span class='muted'>{d['question']}</span>", unsafe_allow_html=True)
            if f["status"] == "pending":
                note = st.text_input("Note (optional)", key=f"note_{f['concept_id']}",
                                     placeholder="e.g. covered again on Monday")
                a, r, _ = st.columns([1, 1, 3])
                if a.button("Approve", key=f"ok_{f['concept_id']}", type="primary"):
                    set_flag_status(f["concept_id"], "approved", note)
                    st.rerun()
                if r.button("Reject", key=f"no_{f['concept_id']}"):
                    set_flag_status(f["concept_id"], "rejected", note)
                    st.rerun()
            elif f.get("professor_note"):
                st.caption(f"Professor note: {f['professor_note']}")
