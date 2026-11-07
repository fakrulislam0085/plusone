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

/* portal */
.profile { background:#fff; border:1px solid var(--line); border-radius:20px; padding:22px 26px; margin-bottom:16px;
           box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 6px 24px rgba(0,0,0,.05); }
.profile .bar { width:44px; height:4px; border-radius:4px; background: linear-gradient(90deg,#00a651,#9be15d); margin-bottom:10px; }
.profile h3 { margin:0 0 2px; font-size:1.5rem; }
.profile .facts { display:flex; gap:28px; flex-wrap:wrap; margin-top:12px; }
.profile .facts div { font-size:.85rem; color: var(--muted); }
.profile .facts b { display:block; color: var(--ink); font-size:.95rem; font-weight:600; }
.course-off { border:1px solid var(--line); border-radius:14px; padding:10px 14px; margin-top:8px; opacity:.55; background:#fafafa; }
.crumbs { color: var(--muted); font-size:.9rem; margin: 0 0 6px; }
.crumbs b { color: var(--ink); }
.unit-title { font-size:1.35rem; font-weight:650; letter-spacing:-0.02em; line-height:1.25; color:var(--ink);
              min-height:2.5em; margin:10px 0 2px; }
.profile .pname { font-size:1.5rem; font-weight:650; letter-spacing:-0.02em; color:var(--ink); margin-bottom:2px; }
/* study-mode cards */
.mode-card { min-height: 205px; padding: 6px 4px 4px; }
.mode-ic { width:56px; height:56px; border-radius:16px; display:flex; align-items:center; justify-content:center; margin-bottom:14px; }
.mode-ic svg { margin-right:0 !important; vertical-align:0 !important; }
.mode-ic.solo { background:#e3f4e9; } .mode-ic.group { background:#eef0f3; }
.mode-title { font-size:1.35rem; font-weight:700; letter-spacing:-0.02em; color:var(--ink); margin-bottom:6px; }
.mode-desc { color:var(--muted); font-size:.95rem; line-height:1.45; min-height:4.4em; }
.mode-meta { margin-top:12px; font-size:.95rem; color:var(--ink); }
/* AI teaching audit */
.audit-hero { border-radius:24px; padding:22px 26px; margin:6px 0 14px; color:#f5f5f7;
              background: radial-gradient(circle at 92% 0%, #3d9a52 0%, #1b4a2a 32%, #111214 70%); }
.audit-hero .eyebrow { color:#9be15d; }
.ah-title { font-size:1.7rem; font-weight:700; letter-spacing:-0.02em; margin:4px 0 6px; color:#fff; }
.ah-sub { color:#c7c7cc; font-size:.95rem; max-width:820px; }
.sevchip { display:inline-block; font-size:.75rem; font-weight:700; padding:3px 10px; border-radius:99px; margin-right:6px; }
.sevchip.high { background:#fdecec; color:#b42318; } .sevchip.medium { background:#fdf5e1; color:#8a5a00; }
.minchip { display:inline-block; font-size:.75rem; font-weight:600; padding:3px 10px; border-radius:99px;
           background:#eef0f3; color:#4a4a50; }
.chip { display:inline-block; font-size:.78rem; font-weight:600; padding:3px 10px; border-radius:99px; }
.chip.open { background:#e3f4e9; color:#007a3d; } .chip.done { background:#eef0f3; color:#4a4a50; }
.chip.locked { background:#f3f0ea; color:#8a6d3b; }
</style>
"""

HERO = """
<div class="hero">
  <div class="eyebrow">Matteo · Student Tech Clash 2026 · AI on Campus</div>
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


def _logo() -> str:
    from icons import ic
    return ic("smile", 26, "#00a651", 2.2)


def _check() -> str:
    from icons import PATHS
    return ("<svg width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='3' "
            f"stroke-linecap='round' stroke-linejoin='round'>{PATHS['check']}</svg>")


STEP_NAMES = ["Start", "Quiz", "Teach Matteo", "Final check", "Summary"]


def header() -> None:
    st.markdown("<div class='topbar'><div class='brand'>" + _logo() + "<span>Matteo</span></div>"
                "<div class='tagline'>Campus portal · demo</div></div>",
                unsafe_allow_html=True)


def steps(current: int) -> None:
    parts = []
    for i, name in enumerate(STEP_NAMES, 1):
        cls = "on" if i == current else ("done" if i < current else "")
        parts.append(f"<div class='step {cls}'><b>{_check() if i < current else i}</b>{name}</div>")
    st.markdown("<div class='steps'>" + "".join(parts) + "</div>", unsafe_allow_html=True)


def profile(name: str, subtitle: str, facts: list[tuple[str, str]]) -> None:
    items = "".join(f"<div>{k}<b>{v}</b></div>" for k, v in facts)
    st.markdown(f"<div class='profile'><div class='bar'></div><div class='pname'>{name}</div><div class='muted'>{subtitle}</div>"
                f"<div class='facts'>{items}</div></div>", unsafe_allow_html=True)


def crumbs(parts: list[str]) -> None:
    st.markdown("<div class='crumbs'>" + " › ".join(parts[:-1] + [f"<b>{parts[-1]}</b>"]) + "</div>",
                unsafe_allow_html=True)
