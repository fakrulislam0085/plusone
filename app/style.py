"""Apple-like light look with Reply's green gradient as the accent (no Reply logo/branding)."""
import streamlit as st

CSS = """
<style>
:root { --ink:#1d1d1f; --muted:#6e6e73; --line:#e3e3e8; --card:#ffffff;
        --green:#00a651; --lime:#9be15d; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display:none; }
.block-container { padding-top: 1rem; max-width: 1320px; }
h1, h2, h3, h4 { letter-spacing: -0.02em; color: var(--ink); }
.muted { color: var(--muted); font-size: 0.88rem; }
.eyebrow { font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
           color: var(--green); margin-bottom: 0.2rem; }

/* hero */
.hero { position: relative; overflow: hidden; border-radius: 28px; padding: 20px 28px 18px;
        background: #0b0b0c; color: #fff; margin-bottom: 18px; }
.hero::after { content:""; position:absolute; right:-120px; top:-140px; width:520px; height:520px;
        border-radius:50%; background: radial-gradient(circle at 30% 30%, var(--lime), var(--green) 55%,
        transparent 70%); opacity: .55; filter: blur(10px); z-index: 0; pointer-events: none; }
.hero .eyebrow { color: var(--lime); position: relative; z-index: 1; }
.hero h1 { color:#fff !important; font-size: 2rem; line-height: 1.1; font-weight: 700; margin: 2px 0 6px; padding:0 !important;
           position: relative; z-index: 1; }
.hero h1 span { -webkit-text-fill-color: transparent; background: linear-gradient(90deg, var(--lime), var(--green)); -webkit-background-clip: text;
                background-clip: text; color: transparent; }
.hero p { color: #d2d2d7; font-size: 0.95rem; max-width: 760px; margin: 0; position: relative; z-index: 1; }
.hero .pills { margin-top: 10px; position: relative; z-index: 1; }
.hero .pill { display:inline-block; font-size:.8rem; padding:5px 12px; border-radius:99px; margin-right:6px;
              background: rgba(255,255,255,.1); color:#f5f5f7; border:1px solid rgba(255,255,255,.18); }

/* tabs as a segmented control */
[role="tablist"] { gap: 6px; background: #e8e8ed; padding: 4px; border-radius: 99px; width: fit-content; }
[role="tab"] { border-radius: 99px !important; padding: 6px 18px !important; height: auto !important; }
[role="tab"][aria-selected="true"] { background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,.12); }
[role="tablist"] + div[data-baseweb], [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }
[role="tab"] p { font-weight: 600; }

/* cards & containers */
[data-testid="stVerticalBlockBorderWrapper"] { background: var(--card); border-radius: 20px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 6px 24px rgba(0,0,0,.05); }
iframe { border-radius: 18px; background: #fff; box-shadow: 0 6px 24px rgba(0,0,0,.05); }

/* chat bubbles */
[data-testid="stChatMessage"] { background: #f5f5f7; border-radius: 18px; padding: 10px 14px; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
[data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]) { background: #eaf7ef; }
[data-testid="stChatInput"] { border-radius: 99px; }

/* sidebar */
section[data-testid="stSidebar"] { background: #fbfbfd; border-right: 1px solid var(--line); }
</style>
"""

HERO = """
<div class="hero">
  <div class="eyebrow">PlusOne · Student Tech Clash 2026 · AI on Campus</div>
  <h1>Learn Physics by <span>teaching it.</span></h1>
  <p>Matteo is a confused AI freshman. He never gives answers: you, or your whole study group, explain,
     and he asks. Behind him, an examiner maps every explanation onto the course graph and shows
     why you're stuck, down to the source.</p>
  <div class="pills"><span class="pill">Physics I · Newton's laws</span><span class="pill">Solo or study group</span>
  <span class="pill">Professor in the loop</span></div>
</div>
"""


def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero() -> None:
    st.markdown(HERO, unsafe_allow_html=True)
