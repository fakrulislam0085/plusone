"""PlusOne: Streamlit UI.  Run:  .venv\\Scripts\\streamlit run app/main.py

Views (top switch):  Student | Professor
Student flow:  1 Start -> 2 Quiz -> 3 Teach Matteo -> 4 Summary
Every step has the same nav row under the step bar: [← Back]  ...  [Next action →]
All navigation goes through on_click callbacks (one click = one move, no lost state).
"""
from __future__ import annotations

import json

import streamlit as st

import professor
import quiz as quizmod
import streaks
import style
from graph import band, concept_name, load_graph, render_html
from orchestrator import run_turn
from tools import FLAGS_PATH, STUDENTS_DIR, load_student, mastery_view, trace_root_cause

DEMO_GROUP = ["Alex", "Bea", "Chris", "Dani"]  # synthetic names from the material pack
AVATARS = {"Alex": "🧑‍🦱", "Bea": "👩‍🦰", "Chris": "🧑‍🦲", "Dani": "👩‍🦳"}
STAGES = {"start": 1, "quiz": 2, "teach": 3, "summary": 4}

st.set_page_config(page_title="PlusOne · Teach Matteo", page_icon="➕", layout="wide",
                   initial_sidebar_state="collapsed")
style.apply()
quizmod.ensure_default()

ss = st.session_state
ss.setdefault("stage", "start")
ss.setdefault("sid", 0)            # session counter: new session -> fresh widget keys
ss.setdefault("view", "Student")


def k(name: str) -> str:
    """Widget key scoped to the current session, so nothing leaks into a new session."""
    return f"{name}_{ss.sid}"


# ---------------------------------------------------------------- state helpers
def greeting(mode: str, focus: str | None) -> str:
    if focus:
        return (f"Ciao{' everyone' if mode == 'group' else ''}! I'm Matteo 👋 I got **{concept_name(focus)}** "
                "wrong on today's quiz too 😅 Can you explain it to me?")
    if mode == "group":
        return ("Ciao everyone! I'm Matteo 👋 Thanks for letting me join your study group. "
                "The prof did Newton's laws today and I'm lost 😅 Who wants to start?")
    return ("Ciao! I'm Matteo, first year. Today the prof did Newton's laws and honestly "
            "I'm lost 😅 Can you explain it to me? Where should we start?")


def weakest() -> str | None:
    G = load_graph()
    weak = [c for r in ss.get("quiz_results", {}).values() for c in r["weak_concepts"] if c in G]
    return weak[0] if weak else None


def go(stage: str) -> None:
    ss.stage = stage


def start_session() -> None:
    mode = "group" if ss.get(k("mode")) == "Study group" else "solo"
    if mode == "solo":
        participants = [(ss.get(k("name")) or "You").strip() or "You"]
    else:
        raw = ss.get(k("group")) or ", ".join(DEMO_GROUP)
        participants = [n.strip() for n in raw.split(",") if n.strip()] or DEMO_GROUP
    ss.mode, ss.participants, ss.quiz_results = mode, participants, {}
    ss.messages, ss.focus = None, None
    ss.stage = "quiz" if quizmod.current() else "teach"
    if ss.stage == "teach":
        open_chat(None)


def open_chat(focus: str | None) -> None:
    """Go to the teaching step. Keeps the existing chat if you come back to it."""
    if ss.get("messages") is None or (focus is not None and ss.get("focus") != focus and len(ss.messages) <= 1):
        ss.messages = [{"role": "assistant", "speaker": "Matteo", "text": greeting(ss.mode, focus)}]
        ss.root, ss.last, ss.focus = {}, None, focus
    ss.stage = "teach"


def new_session() -> None:
    ss.sid += 1
    for key in ("mode", "participants", "quiz_results", "messages", "focus", "root", "last"):
        ss.pop(key, None)
    ss.stage = "start"


def reset_demo_data() -> None:
    for p in STUDENTS_DIR.glob("*.json"):
        p.unlink()
    if FLAGS_PATH.exists():
        FLAGS_PATH.unlink()
    quizmod.reset()
    streaks.reset()
    new_session()


def nav(back: tuple | None = None, primary: tuple | None = None, secondary: tuple | None = None,
        where: str = "top") -> None:
    """One consistent row: (label, callback[, args]) for back / secondary / primary."""
    left, _, mid, right = st.columns([2, 4, 2, 3])
    if back:
        left.button(back[0], on_click=back[1], args=back[2] if len(back) > 2 else (), key=k(f"nav_back_{where}"),
                    width="stretch")
    if secondary:
        mid.button(secondary[0], on_click=secondary[1], args=secondary[2] if len(secondary) > 2 else (),
                   key=k(f"nav_secondary_{where}"), width="stretch")
    if primary:
        disabled = len(primary) > 3 and primary[3]
        right.button(primary[0], on_click=primary[1], args=primary[2] if len(primary) > 2 else (),
                     type="primary", disabled=disabled, key=k(f"nav_primary_{where}"), width="stretch")


# ---------------------------------------------------------------- sidebar (presenter tools only)
with st.sidebar:
    st.markdown("#### Presenter tools")
    st.button("🧹 Reset demo data", on_click=reset_demo_data,
              help="Deletes student memory, flags, quiz answers and today's streaks; back to Start.")
    st.caption("Course material: demo pack aligned with OpenStax University Physics Vol. 1, Ch. 5 "
               "(CC BY 4.0). Not official PoliTO notes. Names and past sessions are synthetic.")

# ---------------------------------------------------------------- header + view switch
style.header()
view = st.segmented_control("View", ["Student", "Professor"], key="view", label_visibility="collapsed")
view = view or "Student"   # clicking the selected segment again unselects it: treat as Student

# ================================================================= PROFESSOR
if view == "Professor":
    professor.render()
    st.stop()

# ================================================================= STUDENT
style.steps(STAGES[ss.stage])
today = quizmod.current()

# ---------------- 1 start
if ss.stage == "start":
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with st.container(border=True):
            st.markdown("### Who is learning today?")
            st.caption("Topic: **Physics I · Newton's laws**. Take today's quiz, then teach Matteo what you missed.")
            mode_label = st.radio("Mode", ["Just me", "Study group"], horizontal=True, key=k("mode"),
                                  label_visibility="collapsed")
            if mode_label == "Study group":
                raw = st.text_input("Group members (comma separated)", value=", ".join(DEMO_GROUP), key=k("group"))
                members = [n.strip() for n in raw.split(",") if n.strip()] or DEMO_GROUP
                st.markdown(f"🔥 **Team streak: {streaks.team_streak(members)} sessions**. "
                            "It grows when everyone answers the quiz.")
            else:
                name = st.text_input("Your first name", value="You", key=k("name")).strip() or "You"
                st.markdown(f"🔥 **{streaks.streak(name)}-session streak**. Today's quiz keeps it going.")
            st.button("Start  →", on_click=start_session, type="primary", width="stretch", key=k("start"))
        st.markdown("<p class='muted' style='text-align:center'>Matteo never gives answers. "
                    "Your professor only sees anonymous topics, never your name.</p>", unsafe_allow_html=True)

# ---------------- 2 quiz
elif ss.stage == "quiz":
    focus = weakest()
    done = bool(ss.quiz_results)
    quiz_nav = dict(back=("←  Back", go, ("start",)),
                    secondary=None if done else ("Skip quiz  →", open_chat, (None,)),
                    primary=(f"Teach Matteo: {concept_name(focus)}  →" if focus else "Teach Matteo  →",
                             open_chat, (focus,), not done))
    nav(**quiz_nav)
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        st.markdown(f"### {today['title']}")
        st.caption(f"{len(today['questions'])} questions · about 3 minutes · answers unlock after you teach "
                   "Matteo · graded by code, not by AI")
        for person, r in ss.quiz_results.items():
            with st.container(border=True):
                st.markdown(f"**{person}: {r['score']} / {r['max']}** · 🔥 streak {streaks.streak(person)}")
                st.markdown("To work on: " + ", ".join(f"**{concept_name(c)}**" for c in r["weak_concepts"])
                            if r["weak_concepts"] else "All correct. Now prove it: can you teach it?")
        todo = [p for p in ss.participants if p not in ss.quiz_results]
        if todo:
            taker = (st.radio("Who is taking the quiz?", todo, horizontal=True, key=k("taker"))
                     if ss.mode == "group" else todo[0])
            with st.form(k(f"quiz_{taker}")):
                answers = []
                for i, q in enumerate(quizmod.student_view(today), 1):
                    with st.container(border=True):
                        a = st.radio(f"**{i}.** {q['q']}", q["options"], index=None, key=k(f"{taker}_{q['id']}"))
                        answers.append(None if a is None else q["options"].index(a))
                if st.form_submit_button("Submit answers", type="primary"):
                    if None in answers:
                        st.warning(f"Answer all {len(answers)} questions first "
                                   f"({answers.count(None)} left).")
                    else:
                        ss.quiz_results[taker] = quizmod.submit(today["id"], taker, answers)
                        st.rerun()
        if done:
            st.success("Quiz done. Now teach Matteo what you missed."
                       + (" Other members can still take it." if todo else ""))
    nav(**quiz_nav, where="bottom")

# ---------------- 3 teach
elif ss.stage == "teach":
    mode, participants = ss.mode, ss.participants
    nav(back=("←  Back to quiz", go, ("quiz",)) if today else ("←  Back", go, ("start",)),
        primary=("Finish session  →", go, ("summary",)))
    left, right = st.columns([3, 2], gap="large")
    with left:
        speaker = (st.radio("Who's speaking?", participants, horizontal=True, key=k("speaker"))
                   if mode == "group" else participants[0])
        chat_box = st.container(height=470)
        with chat_box:
            for m in ss.messages:
                if m["role"] == "assistant":
                    with st.chat_message("assistant", avatar="🤔"):
                        st.markdown(m["text"])
                else:
                    with st.chat_message("user", avatar=AVATARS.get(m["speaker"], "🧑‍🎓")):
                        st.markdown(f"**{m['speaker']}:** {m['text']}" if mode == "group" else m["text"])
        prompt = st.chat_input(f"{speaker}, explain something to Matteo…", key=k("chat"))
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
    with right:
        student = load_student(speaker)
        root = ss.root.get(speaker)
        st.markdown(f"#### {speaker}'s topic map")
        st.iframe(render_html(mastery_view(student), highlight=[p["id"] for p in root["path"]] if root else []),
                  height=400)
        st.markdown("<p class='legend'><span class='dot g'></span>explained well <span class='dot y'></span>almost "
                    "<span class='dot r'></span>to fix <span class='dot n'></span>not yet</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 🧭 Why am I stuck?")
            if root:
                st.markdown(root["explanation"])
                st.caption("Source: " + " · ".join(p["source"] for p in root["path"]))
            else:
                st.caption("Nothing yet. If you get something wrong, this card shows you why.")
        if ss.last:
            with st.expander("Behind the scenes (what the AI did)"):
                for a in ss.last["actions"] or [{"tool": "none", "args": "", "result": "no actions"}]:
                    st.markdown(f"- `{a['tool']}` {a['args']} → {a['result']}")
                if ss.last["exam"]:
                    st.code(json.dumps(ss.last["exam"], indent=1, ensure_ascii=False), language="json")

# ---------------- 4 summary
else:
    nav(back=("←  Keep teaching", go, ("teach",)), primary=("New session  ✓", new_session))
    G = load_graph()
    st.markdown("### Session summary")
    if ss.mode == "group":
        st.markdown(f"🔥 **Team streak: {streaks.team_streak(ss.participants)} sessions**")
    cols = st.columns(min(len(ss.participants), 4), gap="large")
    for i, person in enumerate(ss.participants):
        mastery = load_student(person)["mastery"]
        good = [c for c, m in mastery.items() if m["score"] is not None and m["score"] >= 2 and c in G]
        fix = [c for c, m in mastery.items() if m["score"] is not None and m["score"] <= 1 and c in G]
        qr = ss.quiz_results.get(person)
        with cols[i % len(cols)]:
            with st.container(border=True):
                st.markdown(f"#### {person} · 🔥 {streaks.streak(person)}")
                if qr:
                    st.markdown(f"**Quiz:** {qr['score']} / {qr['max']}")
                if not mastery:
                    st.caption("Didn't explain anything to Matteo this time.")
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
                if qr:
                    with st.expander("Quiz answers (unlocked)"):
                        for j, r in enumerate(qr["review"], 1):
                            st.markdown(f"{'✅' if r['ok'] else '❌'} **{j}.** {r['q']}  \n"
                                        f"Correct: **{r['correct']}**  \n{r['explanation']}")
                            st.caption(f"Source: {r['source']}")
