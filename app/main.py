"""PlusOne: Streamlit UI.  Run:  .venv\\Scripts\\streamlit run app/main.py"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from graph import render_html
from orchestrator import run_turn
from tools import FLAGS_PATH, STUDENTS_DIR, load_flags, load_student, mastery_view

ROOT = Path(__file__).resolve().parent.parent
DEMO_GROUP = ["Alex", "Bea", "Chris", "Dani"]  # synthetic names from the material pack
AVATARS = {"Alex": "🧑‍🦱", "Bea": "👩‍🦰", "Chris": "🧑‍🦲", "Dani": "👩‍🦳"}
GREETING = ("Ciao! I'm Matteo, first year. Today the prof did Newton's laws and honestly "
            "I'm lost 😅 Can you explain it to me? Where should we start?")
GREETING_GROUP = ("Ciao everyone! I'm Matteo 👋 Thanks for letting me join your study group. "
                  "The prof did Newton's laws today and I'm lost 😅 Who wants to start?")

st.set_page_config(page_title="PlusOne · Teach Matteo", page_icon="➕", layout="wide")


def init_state(mode: str) -> None:
    st.session_state.mode = mode
    st.session_state.messages = [{"role": "assistant", "speaker": "Matteo",
                                  "text": GREETING_GROUP if mode == "group" else GREETING}]
    st.session_state.root = {}      # speaker -> last root-cause result
    st.session_state.last = None    # last turn result (for the agent trace)


def reset_demo_data() -> None:
    for p in STUDENTS_DIR.glob("*.json"):
        p.unlink()
    if FLAGS_PATH.exists():
        FLAGS_PATH.unlink()


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Session")
    mode_label = st.radio("Mode", ["Solo", "Study group"], horizontal=True,
                          help="Study group: several students teach Matteo together (the +1).")
    mode = "group" if mode_label == "Study group" else "solo"
    if "messages" not in st.session_state or st.session_state.get("mode") != mode:
        init_state(mode)
    if mode == "solo":
        solo_name = st.text_input("Your name", value="You").strip() or "You"
        participants = [solo_name]
    else:
        raw = st.text_input("Group members", value=", ".join(DEMO_GROUP))
        participants = [n.strip() for n in raw.split(",") if n.strip()] or DEMO_GROUP
    st.divider()
    if st.button("🔄 New conversation"):
        init_state(mode)
        st.rerun()
    if st.button("🧹 Reset demo data",
                 help="Deletes all student memory files and lecturer flags."):
        reset_demo_data()
        init_state(mode)
        st.rerun()
    st.caption("Course material: PlusOne demo pack aligned with OpenStax University Physics Vol. 1, "
               "Ch. 5 (CC BY 4.0). Not official PoliTO notes. Group names are synthetic.")

# ---------------------------------------------------------------- header
st.title("➕ PlusOne")
st.caption("Learn Physics I by teaching Matteo, a confused AI freshman · Newton's laws")
tab_teach, tab_prof = st.tabs(["🧑‍🎓 Teach Matteo", "👩‍🏫 Professor"])

with tab_teach:
    left, right = st.columns([3, 2], gap="large")

    with left:
        if mode == "group":
            speaker = st.radio("Who's speaking?", participants, horizontal=True, key="speaker_pick")
        else:
            speaker = participants[0]

        chat_box = st.container(height=500)
        with chat_box:
            for m in st.session_state.messages:
                if m["role"] == "assistant":
                    with st.chat_message("assistant", avatar="🤔"):
                        st.markdown(m["text"])
                else:
                    with st.chat_message("user", avatar=AVATARS.get(m["speaker"], "🧑‍🎓")):
                        st.markdown(f"**{m['speaker']}:** {m['text']}" if mode == "group" else m["text"])

        prompt = st.chat_input(f"{speaker}, explain something to Matteo…")
        if prompt:
            st.session_state.messages.append({"role": "user", "speaker": speaker, "text": prompt})
            with chat_box:
                with st.chat_message("user", avatar=AVATARS.get(speaker, "🧑‍🎓")):
                    st.markdown(f"**{speaker}:** {prompt}" if mode == "group" else prompt)
                with st.chat_message("assistant", avatar="🤔"):
                    with st.spinner("Matteo is thinking… (the Examiner is checking the graph)"):
                        result = run_turn(st.session_state.messages, speaker, mode, participants)
            st.session_state.messages.append({"role": "assistant", "speaker": "Matteo",
                                              "text": result["reply"]})
            st.session_state.last = result
            if result["root_cause"] and result["root_cause"].get("found"):
                st.session_state.root[speaker] = result["root_cause"]
            st.rerun()

    with right:
        student = load_student(speaker)
        root = st.session_state.root.get(speaker)
        highlight = [p["id"] for p in root["path"]] if root else []
        st.subheader(f"Knowledge graph · {speaker}")
        st.iframe(render_html(mastery_view(student), highlight=highlight), height=470)
        st.caption("⬜ untested · 🟥 weak · 🟨 shaky · 🟩 solid · dashed = needs confirmation · "
                   "arrows: prerequisite → concept · hover a node for its source")

        with st.container(border=True):
            st.markdown("#### 🧭 Why am I stuck?")
            if root:
                st.markdown(root["explanation"])
                chain = " → ".join(f"{p['name']}" for p in reversed(root["path"]))
                st.markdown(f"**Path:** {chain}")
                for p in root["path"]:
                    score = "untested" if p["score"] is None else f"{p['score']}/3"
                    st.caption(f"• {p['name']}: {score} · Source: {p['source']}")
                if root.get("untested_prereqs"):
                    st.caption("Check next: " + ", ".join(u["name"] for u in root["untested_prereqs"]))
            else:
                st.caption("Nothing to trace yet. Keep teaching Matteo!")

        last = st.session_state.last
        with st.expander("🔍 What the agent did this turn", expanded=False):
            if not last:
                st.caption("No turn yet.")
            else:
                if last["actions"]:
                    for a in last["actions"]:
                        st.markdown(f"- `{a['tool']}({a['args']})` → {a['result']}")
                else:
                    st.markdown("- no tool calls this turn")
                exam = last["exam"]
                if exam:
                    gaps = [m["description"] for m in exam["misconceptions"] if m["not_in_graph"]]
                    if gaps:
                        st.warning("Not in the course graph: " + "; ".join(gaps))
                    st.code(json.dumps(exam, indent=1, ensure_ascii=False), language="json")
                else:
                    st.warning("Examiner unavailable this turn (Matteo answered without a probe).")

with tab_prof:
    st.subheader("Flagged concepts (anonymized)")
    flags = load_flags()
    if not flags:
        st.caption("No flags yet.")
    for f in sorted(flags, key=lambda f: -f["count"]):
        st.markdown(f"**{f['concept_name']}** · seen {f['count']}× · {f['status']}  \n{f['reason']}"
                    + (f"  \n`{', '.join(f['misconception_ids'])}`" if f["misconception_ids"] else ""))
    st.info("Full professor view (class heatmap, approve/reject) arrives in Milestone 5.")
