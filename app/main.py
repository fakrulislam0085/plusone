"""PlusOne: Streamlit UI.  Run:  .venv\\Scripts\\streamlit run app/main.py

Student flow:  1 Start (who is learning)  ->  2 Teach Matteo  ->  3 Summary
Professor tab: flags to review (approve/reject) + class map.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

import professor
import style
from graph import band, concept_name, load_graph, render_html
from orchestrator import run_turn
from tools import FLAGS_PATH, STUDENTS_DIR, load_student, mastery_view, trace_root_cause

ROOT = Path(__file__).resolve().parent.parent
DEMO_GROUP = ["Alex", "Bea", "Chris", "Dani"]  # synthetic names from the material pack
AVATARS = {"Alex": "🧑‍🦱", "Bea": "👩‍🦰", "Chris": "🧑‍🦲", "Dani": "👩‍🦳"}
GREETING = ("Ciao! I'm Matteo, first year. Today the prof did Newton's laws and honestly "
            "I'm lost 😅 Can you explain it to me? Where should we start?")
GREETING_GROUP = ("Ciao everyone! I'm Matteo 👋 Thanks for letting me join your study group. "
                  "The prof did Newton's laws today and I'm lost 😅 Who wants to start?")

st.set_page_config(page_title="PlusOne · Teach Matteo", page_icon="➕", layout="wide",
                   initial_sidebar_state="collapsed")
style.apply()

ss = st.session_state
ss.setdefault("stage", "start")


def start_session(mode: str, participants: list[str]) -> None:
    ss.stage, ss.mode, ss.participants = "teach", mode, participants
    ss.messages = [{"role": "assistant", "speaker": "Matteo",
                    "text": GREETING_GROUP if mode == "group" else GREETING}]
    ss.root, ss.last = {}, None


def reset_demo_data() -> None:
    for p in STUDENTS_DIR.glob("*.json"):
        p.unlink()
    if FLAGS_PATH.exists():
        FLAGS_PATH.unlink()


# ---------------------------------------------------------------- sidebar (presenter tools only)
with st.sidebar:
    st.markdown("#### Presenter tools")
    if st.button("🧹 Reset demo data", help="Deletes all student memory files and professor flags."):
        reset_demo_data()
        ss.clear()
        st.rerun()
    st.caption("Course material: demo pack aligned with OpenStax University Physics Vol. 1, Ch. 5 "
               "(CC BY 4.0). Not official PoliTO notes. Group names are synthetic.")

style.header()
tab_student, tab_prof = st.tabs(["Student", "Professor"])

# ================================================================= STUDENT
with tab_student:
    style.steps({"start": 1, "teach": 2, "summary": 3}[ss.stage])

    # ---------------- step 1: start
    if ss.stage == "start":
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            with st.container(border=True):
                st.markdown("### Who is learning today?")
                st.caption("Topic: **Physics I · Newton's laws**. You explain, Matteo asks.")
                mode_label = st.radio("Mode", ["Just me", "Study group"], horizontal=True,
                                      label_visibility="collapsed")
                if mode_label == "Just me":
                    name = st.text_input("Your first name", value="You").strip() or "You"
                    participants, mode = [name], "solo"
                else:
                    raw = st.text_input("Group members (comma separated)", value=", ".join(DEMO_GROUP))
                    participants = [n.strip() for n in raw.split(",") if n.strip()] or DEMO_GROUP
                    mode = "group"
                if st.button("Start teaching Matteo  →", type="primary", width="stretch"):
                    start_session(mode, participants)
                    st.rerun()
            st.markdown(
                "<p class='muted' style='text-align:center'>Matteo never gives answers. "
                "Your professor only sees anonymous topics, never your name.</p>", unsafe_allow_html=True)

    # ---------------- step 2: teach
    elif ss.stage == "teach":
        mode, participants = ss.mode, ss.participants
        left, right = st.columns([3, 2], gap="large")
        with left:
            if mode == "group":
                speaker = st.radio("Who's speaking?", participants, horizontal=True, key="speaker_pick")
            else:
                speaker = participants[0]
            chat_box = st.container(height=470)
            with chat_box:
                for m in ss.messages:
                    if m["role"] == "assistant":
                        with st.chat_message("assistant", avatar="🤔"):
                            st.markdown(m["text"])
                    else:
                        with st.chat_message("user", avatar=AVATARS.get(m["speaker"], "🧑‍🎓")):
                            st.markdown(f"**{m['speaker']}:** {m['text']}" if mode == "group" else m["text"])
            prompt = st.chat_input(f"{speaker}, explain something to Matteo…")
            if prompt:
                ss.messages.append({"role": "user", "speaker": speaker, "text": prompt})
                with chat_box:
                    with st.chat_message("user", avatar=AVATARS.get(speaker, "🧑‍🎓")):
                        st.markdown(f"**{speaker}:** {prompt}" if mode == "group" else prompt)
                    with st.chat_message("assistant", avatar="🤔"):
                        with st.spinner("Matteo is thinking…"):
                            result = run_turn(ss.messages, speaker, mode, participants)
                ss.messages.append({"role": "assistant", "speaker": "Matteo", "text": result["reply"]})
                ss.last = result
                if result["root_cause"] and result["root_cause"].get("found"):
                    ss.root[speaker] = result["root_cause"]
                st.rerun()
            if st.button("Finish session  →", type="primary"):
                ss.stage = "summary"
                st.rerun()

        with right:
            student = load_student(speaker)
            root = ss.root.get(speaker)
            st.markdown(f"#### {speaker}'s topic map")
            st.iframe(render_html(mastery_view(student),
                                  highlight=[p["id"] for p in root["path"]] if root else []), height=400)
            st.markdown("<p class='legend'><span class='dot g'></span>explained well "
                        "<span class='dot y'></span>almost <span class='dot r'></span>to fix "
                        "<span class='dot n'></span>not yet</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("#### 🧭 Why am I stuck?")
                if root:
                    st.markdown(root["explanation"])
                    st.caption("Source: " + " · ".join(p["source"] for p in root["path"]))
                else:
                    st.caption("Nothing yet. If you get something wrong, Matteo's helper shows you why.")
            if ss.last:
                with st.expander("Behind the scenes (what the AI did)"):
                    for a in ss.last["actions"] or [{"tool": "none", "args": "", "result": "no actions"}]:
                        st.markdown(f"- `{a['tool']}` {a['args']} → {a['result']}")
                    if ss.last["exam"]:
                        st.code(json.dumps(ss.last["exam"], indent=1, ensure_ascii=False), language="json")

    # ---------------- step 3: summary
    else:
        G = load_graph()
        st.markdown("### Session summary")
        cols = st.columns(min(len(ss.participants), 4) or 1, gap="large")
        for col, person in zip(cols * 4, ss.participants):
            mastery = load_student(person)["mastery"]
            good = [c for c, m in mastery.items() if m["score"] is not None and m["score"] >= 2 and c in G]
            fix = [c for c, m in mastery.items() if m["score"] is not None and m["score"] <= 1 and c in G]
            with col:
                with st.container(border=True):
                    st.markdown(f"#### {person}")
                    if not mastery:
                        st.caption("Didn't explain anything this time.")
                    if good:
                        st.markdown("**✅ Explained well**  \n" + "  \n".join(
                            f"{'🟩' if band(mastery[c]['score']) == 'solid' else '🟨'} {concept_name(c)}" for c in good))
                    if fix:
                        st.markdown("**🔁 To review**")
                        for c in fix:
                            rc = trace_root_cause(person, c)
                            st.markdown(f"🟥 **{concept_name(c)}**  \n{rc['explanation']}")
                            st.caption(f"Read: {G.nodes[rc.get('root_id', c)]['source']}")
                        st.caption("📨 Sent to your professor as an anonymous topic (no name).")
        a, b, _ = st.columns([1, 1, 3])
        if a.button("← Keep teaching"):
            ss.stage = "teach"
            st.rerun()
        if b.button("New session", type="primary"):
            ss.stage = "start"
            st.rerun()

# ================================================================= PROFESSOR
with tab_prof:
    professor.render()
