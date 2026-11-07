"""Matteo campus portal (demo).  Run:  .venv\\Scripts\\streamlit run app/main.py

Pages:  Home (portal)  ->  Course: Physics I (unit cards)  ->  Unit: Newton's laws
Unit flow (student):  1 Start -> 2 Quiz -> 3 Teach Matteo -> 4 Summary
Professor: Home -> Physics I console (Class insights · Quiz · Course controls)
Log in as any of the 10 SYNTHETIC demo students or the professor (left menu).
"""
from __future__ import annotations

import json

import streamlit as st

import course
import demo_data
import professor
import quiz as quizmod
import streaks
import style
from graph import band, concept_name, load_graph, render_html
from orchestrator import run_turn
from tools import load_student, mastery_view, trace_root_cause, update_mastery

STAGES = {"start": 1, "quiz": 2, "teach": 3, "check": 4, "summary": 5}
AVATARS = {"Alex": "🧑‍🦱", "Bea": "👩‍🦰", "Chris": "🧑‍🦲", "Dani": "👩‍🦳", "Elena": "👩", "Federico": "🧔",
           "Giulia": "👩‍🦱", "Hamid": "🧑", "Irene": "👱‍♀️", "Luca": "👨"}

st.set_page_config(page_title="Matteo · Campus portal (demo)", page_icon="🤔", layout="wide",
                   initial_sidebar_state="collapsed")
style.apply()
demo_data.ensure()
quizmod.ensure_default()

ss = st.session_state
ss.setdefault("user", "giulia")
ss.setdefault("login", ss.user)
ss.setdefault("page", "home")
ss.setdefault("stage", "start")
ss.setdefault("sid", 0)
ROSTER = {r["id"]: r for r in demo_data.roster()}
PROF = {"id": "prof", "name": "Prof. Bianchi", "first": "Prof. Bianchi"}


def k(name: str) -> str:
    return f"{name}_{ss.sid}"


def me() -> dict:
    return PROF if ss.user == "prof" else ROSTER[ss.user]


def team_of(sid: str) -> list[dict]:
    return [r for r in ROSTER.values() if r["team"] == ROSTER[sid]["team"]]


# ---------------------------------------------------------------- navigation callbacks
def goto(page: str) -> None:
    ss.page = page


def open_unit() -> None:
    if ss.get("stage") == "summary":   # finished last time: start a fresh session
        fresh_flow()
    ss.page = "unit"


def go(stage: str) -> None:
    ss.stage = stage


def fresh_flow() -> None:
    ss.sid += 1
    for key in ("mode", "participants", "quiz_results", "messages", "focus", "root", "last", "check_results"):
        ss.pop(key, None)
    ss.stage = "start"


def switch_user() -> None:
    ss.user = ss.login
    ss.page = "home"
    fresh_flow()


def reset_demo() -> None:
    demo_data.seed()
    fresh_flow()
    ss.page = "home"


def start_session() -> None:
    mine = me()
    if ss.get(k("mode")) == "With my study group":
        ss.mode, ss.participants = "group", [r["first"] for r in team_of(mine["id"])]
    else:
        ss.mode, ss.participants = "solo", [mine["first"]]
    today = quizmod.current()
    ss.quiz_results = {}
    for p in ss.participants:        # already answered today? show that result instead of a re-take
        prev = quizmod.previous(today["id"], p) if today else None
        if prev:
            ss.quiz_results[p] = prev
    ss.messages, ss.focus = None, None
    if today:
        ss.stage = "quiz"
    else:
        open_chat(None)


def greeting(mode: str, focus: str | None) -> str:
    if focus:
        return (f"Ciao{' everyone' if mode == 'group' else ''}! I'm Matteo 👋 I got **{concept_name(focus)}** "
                "wrong on today's quiz too 😅 Can you explain it to me?")
    if mode == "group":
        return ("Ciao everyone! I'm Matteo 👋 Thanks for letting me join your study group. "
                "The prof did Newton's laws today and I'm lost 😅 Who wants to start?")
    return ("Ciao! I'm Matteo, first year. Today the prof did Newton's laws and honestly "
            "I'm lost 😅 Can you explain it to me? Where should we start?")


def open_chat(focus: str | None) -> None:
    if ss.get("messages") is None or (focus is not None and ss.get("focus") != focus and len(ss.messages) <= 1):
        ss.messages = [{"role": "assistant", "speaker": "Matteo", "text": greeting(ss.mode, focus)}]
        ss.root, ss.last, ss.focus = {}, None, focus
    ss.stage = "teach"


def weakest_taught() -> str | None:
    """Topic for the final check when there was no quiz: the weakest topic touched while teaching."""
    G = load_graph()
    for person in ss.get("participants", []):
        m = load_student(person)["mastery"]
        scored = sorted((v["score"], c) for c, v in m.items() if v["score"] is not None and c in G)
        if scored:
            return scored[0][1]
    return None


def weakest() -> str | None:
    G = load_graph()
    weak = [c for r in ss.get("quiz_results", {}).values() for c in r["weak_concepts"] if c in G]
    return weak[0] if weak else None


def nav(back=None, primary=None, secondary=None, where="top") -> None:
    left, _, mid, right = st.columns([2, 3, 2, 3])
    if back:
        left.button(back[0], on_click=back[1], args=back[2] if len(back) > 2 else (), key=k(f"b_{where}"),
                    width="stretch")
    if secondary:
        mid.button(secondary[0], on_click=secondary[1], args=secondary[2] if len(secondary) > 2 else (),
                   key=k(f"s_{where}"), width="stretch")
    if primary:
        right.button(primary[0], on_click=primary[1], args=primary[2] if len(primary) > 2 else (), type="primary",
                     disabled=len(primary) > 3 and primary[3], key=k(f"p_{where}"), width="stretch")


# ================================================================= layout: left menu + content
style.header()
menu, main = st.columns([1, 5], gap="large")
with menu:
    st.selectbox("Logged in as (demo)", ["prof"] + list(ROSTER), key="login", on_change=switch_user,
                 format_func=lambda u: "👩‍🏫 Prof. Bianchi" if u == "prof" else f"🎓 {ROSTER[u]['name']}")
    st.button("🏠  Home", on_click=goto, args=("home",), width="stretch",
              type="primary" if ss.page == "home" else "secondary")
    st.button("📘  Physics I", on_click=goto, args=("course",), width="stretch",
              type="primary" if ss.page in ("course", "unit") else "secondary")
    st.divider()
    st.button("🧹 Reset demo", on_click=reset_demo, width="stretch",
              help="Restore the 10 synthetic students, today's quiz and flags to their starting state.")
    st.caption("Demo portal. All students, numbers and past sessions are synthetic. Material: OpenStax-aligned "
               "demo pack (CC BY 4.0), not official university notes.")

with main:
    user = me()
    is_prof = user["id"] == "prof"

    # ------------------------------------------------------------- HOME
    if ss.page == "home":
        left, right = st.columns([3, 2], gap="large")
        with left:
            if is_prof:
                style.profile(user["name"], "Teaching staff", [("Department", "Applied Physics (demo)"),
                                                                ("Courses", "1 this term")])
            else:
                style.profile(user["name"], f"Student number {user['matricola']}",
                              [("Programme", user["program"]), ("Cohort", user["cohort"]), ("Study group", user["team"])])
            with st.container(border=True):
                st.markdown("#### 📚 Courses · 2026/27")
                a, b = st.columns([4, 1], vertical_alignment="center")
                a.markdown(f"**{course.COURSE['name']}**  \n<span class='muted'>{course.COURSE['code']} · "
                           f"{course.COURSE['cfu']} CFU · {'you teach this course' if is_prof else course.COURSE['teacher']}"
                           "</span>", unsafe_allow_html=True)
                b.button("Open →", on_click=goto, args=("course",), type="primary", key="open_course", width="stretch")
                if not is_prof:
                    for name, cfu in course.OTHER_COURSES:
                        st.markdown(f"<div class='course-off'><b>{name}</b><br><span class='muted'>{cfu} · not part "
                                    "of this demo</span></div>", unsafe_allow_html=True)
        with right:
            today = quizmod.current()
            if not is_prof and course.announcement():
                with st.container(border=True):
                    st.markdown("#### 📣 From your professor")
                    st.markdown(course.announcement())
            with st.container(border=True):
                st.markdown("#### 📅 Today")
                st.markdown("**10:00 · Physics I lecture**  \nNewton's laws")
                if today:
                    n, size, _goal = streaks.class_today(today["id"])
                    st.markdown(f"**Until 18:00 · Session quiz open**  \n{n} of {size} students answered")
            if not is_prof:
                with st.container(border=True):
                    st.markdown("#### 🤔 Matteo")
                    team = team_of(user["id"])
                    st.markdown(f"🔥 **{streaks.streak(user['id'])}-session streak**  \n"
                                f"{user['team']}: {', '.join(r['first'] for r in team)} · "
                                f"team streak 🔥 {streaks.team_streak([r['id'] for r in team])}")

    # ------------------------------------------------------------- COURSE
    elif ss.page == "course":
        style.crumbs(["Home", "Physics I"])
        if is_prof:
            st.markdown("### Physics I · Professor console")
            professor.render()
        else:
            st.markdown("### Physics I")
            st.caption(f"{course.COURSE['code']} · {course.COURSE['cfu']} CFU · {course.COURSE['teacher']}")
            units = course.units()
            for row in (units[:3], units[3:]):
                cols = st.columns(3, gap="medium")
                for col, u in zip(cols, row):
                    with col:
                        with st.container(border=True):
                            chip = {"done": "✅ Completed", "open": "🟢 Open now", "locked": "🔒 Locked"}[u["status"]]
                            st.markdown(f"<span class='chip {u['status']}'>{chip}</span>", unsafe_allow_html=True)
                            st.markdown(f"#### {u['title']}")
                            st.caption(u["week"])
                            can_open = u["status"] == "open" and u["has_content"]
                            label = ("Open →" if can_open else "No material yet" if u["status"] == "open"
                                     else "Completed" if u["status"] == "done" else "Locked by professor")
                            st.button(label, key=f"unit_{u['id']}", disabled=not can_open, width="stretch",
                                      type="primary" if can_open else "secondary", on_click=open_unit)

    # ------------------------------------------------------------- UNIT (student flow)
    elif is_prof:
        st.info("This is the student view of a unit. Open Physics I for the professor console.")
        st.button("Open Physics I console", on_click=goto, args=("course",), type="primary")
    else:
        style.crumbs(["Home", "Physics I", "Newton's laws"])
        st.button("← Physics I", on_click=goto, args=("course",), key="back_course")
        style.steps(STAGES[ss.stage])
        today = quizmod.current()

        if ss.stage == "start":
            _, mid, _ = st.columns([1, 3, 1])
            with mid:
                with st.container(border=True):
                    st.markdown("### Newton's laws · how do you want to study?")
                    team = team_of(user["id"])
                    st.radio("Mode", ["On my own", "With my study group"], key=k("mode"), horizontal=True,
                             label_visibility="collapsed")
                    if ss.get(k("mode")) == "With my study group":
                        st.markdown(f"👥 **{user['team']}**: {', '.join(r['first'] for r in team)} · "
                                    f"team streak 🔥 {streaks.team_streak([r['id'] for r in team])}  \n"
                                    "<span class='muted'>Sit together; pick who's speaking as you go.</span>",
                                    unsafe_allow_html=True)
                    else:
                        st.markdown(f"🔥 **{streaks.streak(user['id'])}-session streak**. Today's quiz keeps it going.")
                    st.caption("You take today's quiz, then teach Matteo what you missed. He never gives answers; "
                               "your professor only sees anonymous topics.")
                    st.button("Start  →", on_click=start_session, type="primary", width="stretch", key=k("start"))

        elif ss.stage == "quiz":
            focus, done = weakest(), bool(ss.quiz_results)
            qnav = dict(back=("←  Back", go, ("start",)),
                        secondary=None if done else ("Skip quiz  →", open_chat, (None,)),
                        primary=(f"Teach Matteo: {concept_name(focus)}  →" if focus else "Teach Matteo  →",
                                 open_chat, (focus,), not done))
            nav(**qnav)
            _, mid, _ = st.columns([1, 4, 1])
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
                                a = st.radio(f"**{i}.** {q['q']}", q["options"], index=None,
                                             key=k(f"{taker}_{q['id']}"))
                                answers.append(None if a is None else q["options"].index(a))
                        if st.form_submit_button("Submit answers", type="primary"):
                            if None in answers:
                                st.warning(f"Answer all {len(answers)} questions first ({answers.count(None)} left).")
                            else:
                                ss.quiz_results[taker] = quizmod.submit(today["id"], taker, answers)
                                st.rerun()
                if done:
                    st.success("Quiz done. Now teach Matteo what you missed."
                               + (" Other members can still take it." if todo else ""))
            nav(**qnav, where="bottom")

        elif ss.stage == "teach":
            mode, participants = ss.mode, ss.participants
            taught = any(m["role"] == "user" for m in ss.messages)
            nav(back=("←  Back to quiz", go, ("quiz",)) if today else ("←  Back", go, ("start",)),
                primary=("Final check  →", go, ("check",), not taught))
            if not taught:
                st.caption("👉 Explain something to Matteo first. The final check unlocks after you've taught him.")
            left, right = st.columns([3, 2], gap="large")
            with left:
                speaker = (st.radio("Who's speaking?", participants, horizontal=True, key=k("speaker"))
                           if mode == "group" else participants[0])
                chat_box = st.container(height=460)
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
                root = ss.root.get(speaker)
                st.markdown(f"#### {speaker}'s topic map")
                st.iframe(render_html(mastery_view(load_student(speaker)),
                                      highlight=[p["id"] for p in root["path"]] if root else []), height=380)
                st.markdown("<p class='legend'><span class='dot g'></span>explained well <span class='dot y'></span>"
                            "almost <span class='dot r'></span>to fix <span class='dot n'></span>not yet · "
                            "<b>pale</b> = seen once, not confirmed yet</p>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("#### 🧭 Possible gap to check")
                    if root:
                        st.markdown(root["explanation"])
                        st.caption("Source: " + " · ".join(p["source"] for p in root["path"]))
                    else:
                        st.caption("Nothing yet. If an explanation goes wrong, this card suggests what to check first.")
                if ss.last:
                    with st.expander("Behind the scenes (what the AI did)"):
                        for a in ss.last["actions"] or [{"tool": "none", "args": "", "result": "no actions"}]:
                            st.markdown(f"- `{a['tool']}` {a['args']} → {a['result']}")
                        if ss.last["exam"]:
                            st.code(json.dumps(ss.last["exam"], indent=1, ensure_ascii=False), language="json")

        elif ss.stage == "check":
            ss.setdefault("check_results", {})
            focus_c = ss.get("focus") or weakest_taught()
            item = quizmod.transfer_item(focus_c)
            done = bool(ss.check_results)
            nav(back=("←  Keep teaching", go, ("teach",)), secondary=None if done else ("Skip for now  →", go, ("summary",)),
                primary=("See my summary  →", go, ("summary",), not done))
            _, mid, _ = st.columns([1, 4, 1])
            with mid:
                st.markdown("### Final check: on your own")
                st.caption(f"A NEW question on **{concept_name(item['concept'])}**, one you haven't seen. No Matteo, no "
                           "group: can you apply it alone? " + ("Graded by code." if item["type"] == "single_select"
                           else "Graded against your professor's criteria."))
                todo = [p for p in ss.participants if p not in ss.check_results]
                for person, r in ss.check_results.items():
                    with st.container(border=True):
                        s = "pending review" if r["score"] is None else f"{r['score']} / 3"
                        st.markdown(f"**{person}: {s}** · {'✅ applied it' if r['ok'] else '🔁 not yet'}  \n{r['feedback']}")
                        with st.expander("What a full answer covers"):
                            st.markdown("\n".join(f"- {p}" for p in r["model_points"]))
                if todo:
                    who = (st.radio("Who is answering?", todo, horizontal=True, key=k("check_who"))
                           if ss.mode == "group" else todo[0])
                    with st.form(k(f"check_{who}")):
                        with st.container(border=True):
                            st.markdown(f"**{item['id']}.** {item['q']}")
                            if item["type"] == "single_select":
                                pick = st.radio("Your answer", item["options"], index=None, key=k(f"chk_{who}"))
                                ans = None if pick is None else item["options"].index(pick)
                            else:
                                ans = st.text_area("Your answer (explain your reasoning)", key=k(f"chk_{who}"), height=140)
                            st.caption(f"Source: {item['source']}")
                        if st.form_submit_button("Submit my answer", type="primary"):
                            if ans is None or (isinstance(ans, str) and len(ans.strip()) < 10):
                                st.warning("Write (or pick) an answer first.")
                            else:
                                with st.spinner("Checking against the criteria…"):
                                    res = quizmod.grade_check(item["id"], who, ans)
                                if res["score"] is not None:   # independent evidence for the topic map
                                    update_mastery(who, item["concept"], res["score"],
                                                   f"independent final check {item['id']}")
                                ss.check_results[who] = res
                                st.rerun()

        else:  # summary
            nav(back=("←  Keep teaching", go, ("teach",)), primary=("Back to Physics I  ✓", goto, ("course",)))
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
                        cr = ss.get("check_results", {}).get(person)
                        st.markdown(f"**Final check:** {'skipped' if not cr else 'pending review' if cr['score'] is None else str(cr['score']) + ' / 3'}"
                                    + (" · ✅ applied it alone" if cr and cr["ok"] else ""))
                        if good:
                            st.markdown("**✅ Explained well**  \n" + "  \n".join(
                                f"{'🟩' if band(mastery[c]['score']) == 'solid' else '🟨'} {concept_name(c)}"
                                + (" _(seen once, not confirmed yet)_" if mastery[c]["status"] == "needs_confirmation" else "")
                                for c in good))
                        if fix:
                            st.markdown("**🔁 To review**")
                            for c in fix:
                                rc = trace_root_cause(person, c)
                                st.markdown(f"🟥 **{concept_name(c)}**  \n{rc['explanation']}")
                                st.caption(f"Read: {G.nodes[rc.get('root_id', c)]['source']}")
                            st.caption("📨 Sent to your professor as an anonymous topic (no name).")
                        if not mastery:
                            st.caption("Nothing explained yet.")
                        if qr:
                            with st.expander("Quiz answers (unlocked)"):
                                for j, r in enumerate(qr["review"], 1):
                                    st.markdown(f"{'✅' if r['ok'] else '❌'} **{j}.** {r['q']}  \n"
                                                f"Correct: **{r['correct']}**  \n{r['explanation']}")
                                    st.caption(f"Source: {r['source']}")
            st.button("Start a new session", on_click=fresh_flow, key=k("again"))
