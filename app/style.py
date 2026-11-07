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

/* slim header */
.topbar { display:flex; align-items:center; justify-content:space-between; padding: 10px 4px 14px; }
.brand { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; color: var(--ink); }
.brand span { background: linear-gradient(90deg, #00a651, #7cc94a); -webkit-background-clip: text;
              background-clip: text; -webkit-text-fill-color: transparent; }
.tagline { color: var(--muted); font-size: 0.95rem; }
/* step bar */
.steps { display:flex; gap:10px; margin: 6px 0 18px; flex-wrap: wrap; }
.step { display:flex; align-items:center; gap:8px; padding:8px 16px; border-radius:99px; background:#e8e8ed;
        color: var(--muted); font-weight:600; font-size:.92rem; }
.step b { display:inline-flex; width:22px; height:22px; border-radius:50%; align-items:center; justify-content:center;
          background:#fff; color: var(--muted); font-size:.8rem; }
.step.on { background: var(--ink); color:#fff; }
.step.on b { background: var(--lime); color: var(--ink); }
.step.done { background:#e3f4e9; color:#007a3d; }
.step.done b { background:#00a651; color:#fff; }
/* legend */
.legend { color: var(--muted); font-size: .9rem; }
.dot { display:inline-block; width:12px; height:12px; border-radius:3px; margin: 0 4px 0 10px; vertical-align:-1px; }
.dot.g { background:#1f9d55; } .dot.y { background:#d9a21b; } .dot.r { background:#d64545; } .dot.n { background:#9aa1a9; }
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


STEP_NAMES = ["Start", "Quiz", "Teach Matteo", "Summary"]


def header() -> None:
    st.markdown("<div class='topbar'><div class='brand'>➕ Plus<span>One</span></div>"
                "<div class='tagline'>Learn Physics by teaching it · Physics I · Newton's laws</div></div>",
                unsafe_allow_html=True)


def steps(current: int) -> None:
    parts = []
    for i, name in enumerate(STEP_NAMES, 1):
        cls = "on" if i == current else ("done" if i < current else "")
        parts.append(f"<div class='step {cls}'><b>{'✓' if i < current else i}</b>{name}</div>")
    st.markdown("<div class='steps'>" + "".join(parts) + "</div>", unsafe_allow_html=True)
