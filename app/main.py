"""PlusOne: Streamlit UI.  Run:  .venv\\Scripts\\streamlit run app/main.py"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from llm import LLMError, chat
from log import log_step

ROOT = Path(__file__).resolve().parent.parent
MATTEO_PROMPT = (ROOT / "prompts" / "matteo.md").read_text(encoding="utf-8")

GREETING = ("Ciao! I'm Matteo, first year. Today the prof did Newton's laws and honestly "
            "I'm lost 😅 Can you explain it to me? Where should we start?")
SAFE_FALLBACK = "Sorry, I got confused 😅 Can you say that again in simpler words?"

st.set_page_config(page_title="PlusOne · Teach Matteo", page_icon="➕", layout="wide")

if "messages" not in st.session_state:
    # Each message: {"role": "user"|"assistant", "speaker": str, "text": str}
    st.session_state.messages = [{"role": "assistant", "speaker": "Matteo", "text": GREETING}]


def to_llm_messages(history: list[dict]) -> list[dict]:
    return [{"role": m["role"], "content": m["text"]} for m in history]


def matteo_reply(history: list[dict]) -> str:
    try:
        reply = chat(MATTEO_PROMPT, to_llm_messages(history), effort="medium", max_tokens=2000)
        log_step("matteo", input=history[-1]["text"], output=reply)
        return reply or SAFE_FALLBACK
    except LLMError as e:
        log_step("matteo_error", input=history[-1]["text"], output=str(e))
        return SAFE_FALLBACK


st.title("➕ PlusOne")
st.caption("Learn Physics I by teaching Matteo, a confused AI freshman · Newton's laws")

tab_teach, tab_prof = st.tabs(["🧑‍🎓 Teach Matteo", "👩‍🏫 Professor"])

with tab_teach:
    left, right = st.columns([3, 2], gap="large")

    with left:
        chat_box = st.container(height=520)
        with chat_box:
            for m in st.session_state.messages:
                avatar = "🤔" if m["role"] == "assistant" else "🧑‍🎓"
                with st.chat_message(m["role"], avatar=avatar):
                    st.markdown(m["text"])

        prompt = st.chat_input("Explain something to Matteo…")
        if prompt:
            st.session_state.messages.append({"role": "user", "speaker": "You", "text": prompt})
            with chat_box:
                with st.chat_message("user", avatar="🧑‍🎓"):
                    st.markdown(prompt)
                with st.chat_message("assistant", avatar="🤔"):
                    with st.spinner("Matteo is thinking…"):
                        reply = matteo_reply(st.session_state.messages)
                    st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "speaker": "Matteo", "text": reply})

        if st.button("🔄 New session"):
            st.session_state.clear()
            st.rerun()

    with right:
        st.subheader("Knowledge graph")
        st.info("Live concept graph arrives in Milestone 2.")

with tab_prof:
    st.info("Professor view arrives in Milestone 5.")
