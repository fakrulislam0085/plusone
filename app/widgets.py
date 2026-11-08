"""Floating presentation widgets: the streak "Constellation" hero (top-right) and a DEMO-ONLY global chat
(bottom-right).

Presentation only: the streak numbers come from streaks.py unchanged (read-only here). Both widgets are
plain HTML/CSS/vanilla JS injected once into the main page via st.html(unsafe_allow_javascript=True) and
attached to document.body, so they survive Streamlit reruns; every rerun only pushes fresh data.
No new dependencies, no network calls, nothing persisted server-side.
"""
from __future__ import annotations

import json

import streamlit as st

import quiz as quizmod
import streaks

MILESTONES = [3, 7, 14, 30]


def _int_param(name: str) -> int | None:
    raw = st.query_params.get(name)
    try:
        return max(0, min(365, int(raw))) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _hero_data(user: dict, team_ids: list[str] | None, team_name: str | None) -> dict:
    sid = user["id"]
    hist = streaks._load()                       # read-only: same file streaks.py computes from
    sessions = hist["sessions"]
    done = set(hist["answered"].get(sid, []))
    today = quizmod.current()
    today_id = today["id"] if today else None
    ring = [{"id": s["id"], "title": s.get("title", ""), "done": s["id"] in done, "today": s["id"] == today_id}
            for s in sessions[-7:]]
    n = streaks.streak(sid)
    best = cur = 0
    for s in sessions:
        cur = cur + 1 if s["id"] in done else 0
        best = max(best, cur)
    team = streaks.team_streak(team_ids) if team_ids else None
    done_today = (today_id in done) if today_id else True
    demo = False

    # ---- DEMO ONLY (stage): ?streak=12&team=5 overrides what is DISPLAYED. Never writes any data. ----
    d_streak, d_team = _int_param("streak"), _int_param("team")
    if d_streak is not None:
        demo, n, done_today = True, d_streak, True
        lit = min(n, 7)
        ring = [{"id": f"S{i + 1}", "title": "", "done": i >= 7 - lit, "today": i == 6} for i in range(7)]
        best = max(best, n)
    if d_team is not None and team_ids:
        demo, team = True, d_team
    # -------------------------------------------------------------------------------------------------

    state = "done" if done_today else ("risk" if n > 0 else "broken")
    return {"show": True, "student": sid, "streak": n, "best": best, "ring": ring, "state": state,
            "todayId": today_id, "team": team, "teamName": team_name, "demo": demo,
            "milestones": [m for m in MILESTONES if n >= m]}


def render(user: dict, is_prof: bool, team_ids: list[str] | None = None, team_name: str | None = None) -> None:
    data = {"show": False} if is_prof else _hero_data(user, team_ids, team_name)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    st.html(TEMPLATE.replace("__DATA__", payload), unsafe_allow_javascript=True)


TEMPLATE = r"""
<span id="mt-anchor" hidden></span>
<script>
/* Matteo floating widgets. Streak hero = presentation of real data (or a clearly labelled demo override).
   Global chat = DEMO ONLY: hard-coded, no backend, no network, no persistence. */
(function () {
  "use strict";
  var VERSION = "w4";
  var DATA = __DATA__;
  var d = document, W = window.__matteoWidgets || (window.__matteoWidgets = {});
  var reduce = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  var NS = "http://www.w3.org/2000/svg";

  function el(tag, cls, text) { var e = d.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function sv(tag, attrs) { var e = d.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } return null; }

  var CSS = `
  :root { --mt-ink:var(--ink,#1d1d1f); --mt-muted:var(--muted,#6e6e73); --mt-line:var(--line,#e3e3e8);
          --mt-card:var(--card,#ffffff); --mt-green:var(--green,#00a651); --mt-lime:var(--lime,#9be15d);
          --mt-deep:#007a3d; --mt-tint:#e3f4e9; --mt-bg:#f5f5f7; }
  div[data-testid="stElementContainer"]:has(#mt-anchor), div.element-container:has(#mt-anchor) { display:none !important; }
  .mt-hero, .mt-toast, .mt-chat { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI Variable", "Segoe UI", Inter, sans-serif; }
  .mt-hero { position:fixed; top:18px; right:24px; z-index:1000050; display:flex; flex-direction:column; align-items:flex-end; gap:10px; }
  .mt-hero[hidden] { display:none; }
  .mt-badge { position:relative; width:96px; height:96px; border-radius:50%; border:1px solid var(--mt-line); background:var(--mt-card);
              box-shadow:0 1px 2px rgba(0,0,0,.05), 0 10px 30px rgba(0,0,0,.10); cursor:pointer; padding:0; color:var(--mt-ink); }
  .mt-badge:focus-visible { outline:3px solid var(--mt-green); outline-offset:4px; }
  .mt-ring { position:absolute; left:-20px; top:-20px; width:136px; height:136px; overflow:visible; pointer-events:none; }
  .mt-num { position:absolute; left:0; right:0; top:18px; text-align:center; font-size:44px; line-height:44px; font-weight:800;
            letter-spacing:-.03em; font-variant-numeric:tabular-nums; color:var(--mt-ink); }
  .mt-num.small { font-size:32px; }
  .mt-lbl { position:absolute; left:0; right:0; top:62px; text-align:center; font-size:10px; font-weight:700; letter-spacing:.08em;
            text-transform:uppercase; color:var(--mt-muted); }
  .mt-hero[data-state="risk"] .mt-badge { animation: mtPulse 1.6s ease-in-out 2; }
  @keyframes mtPulse { 0% { box-shadow:0 0 0 0 rgba(0,166,81,.45), 0 10px 30px rgba(0,0,0,.10);} 100% { box-shadow:0 0 0 16px rgba(0,166,81,0), 0 10px 30px rgba(0,0,0,.10);} }
  .mt-node { fill:var(--mt-card); stroke:#c7c7cc; stroke-width:1.5; }
  .mt-node.on { fill:var(--mt-green); stroke:var(--mt-green); }
  .mt-node.today { stroke-width:2; }
  .mt-node.today.open { stroke:var(--mt-green); stroke-dasharray:2 2; }
  .mt-node.glow { animation: mtGlow 1.4s ease-out 1; }
  @keyframes mtGlow { 0% { filter:drop-shadow(0 0 0 rgba(155,225,93,0)); } 40% { filter:drop-shadow(0 0 6px rgba(155,225,93,1)); } 100% { filter:drop-shadow(0 0 0 rgba(155,225,93,0)); } }
  .mt-link { stroke:var(--mt-green); stroke-width:1.5; opacity:.7; }
  .mt-orbit { fill:none; stroke:var(--mt-green); stroke-width:1.2; stroke-dasharray:2 4; opacity:.35; }
  .mt-orbit:nth-child(2) { stroke:var(--mt-lime); opacity:.6; } .mt-orbit:nth-child(4) { stroke:var(--mt-lime); opacity:.5; }
  .mt-team { display:flex; align-items:center; gap:6px; padding:5px 10px 5px 8px; border-radius:99px; background:var(--mt-card);
             border:1px solid var(--mt-line); box-shadow:0 4px 14px rgba(0,0,0,.06); font-size:13px; font-weight:700; color:var(--mt-ink);
             font-variant-numeric:tabular-nums; white-space:nowrap; }
  .mt-team[hidden], .mt-hint[hidden], .mt-pop[hidden] { display:none; }
  .mt-hint { max-width:116px; text-align:right; font-size:12px; line-height:1.3; color:var(--mt-deep); background:var(--mt-tint);
             padding:6px 9px; border-radius:12px; transition:opacity .6s; }
  .mt-hint.fade { opacity:0; }
  .mt-pop { position:absolute; top:0; right:112px; width:270px; background:var(--mt-card); border:1px solid var(--mt-line); border-radius:18px;
            box-shadow:0 12px 40px rgba(0,0,0,.14); padding:14px 16px; color:var(--mt-ink); font-size:13px; text-align:left; }
  .mt-pop h4 { margin:0 0 4px; font-size:15px; letter-spacing:-.01em; }
  .mt-pop .mt-demo { display:inline-block; margin-left:6px; font-size:10px; font-weight:800; letter-spacing:.06em; text-transform:uppercase;
            background:var(--mt-lime); color:var(--mt-ink); border-radius:99px; padding:2px 7px; vertical-align:2px; }
  .mt-pop p { margin:4px 0; color:var(--mt-muted); line-height:1.4; }
  .mt-pop .mt-state { color:var(--mt-deep); font-weight:600; }
  .mt-days { display:flex; gap:6px; margin:10px 0 6px; }
  .mt-day { flex:1; text-align:center; font-size:10px; color:var(--mt-muted); }
  .mt-day i { display:block; width:14px; height:14px; margin:0 auto 3px; border-radius:50%; border:1.5px solid #c7c7cc; background:var(--mt-card); }
  .mt-day.on i { background:var(--mt-green); border-color:var(--mt-green); }
  .mt-day.today b { color:var(--mt-ink); }
  .mt-toast { position:fixed; top:226px; right:24px; z-index:1000060; max-width:260px; background:var(--mt-ink); color:#fff; font-size:14px;
              line-height:1.35; padding:10px 14px; border-radius:14px; box-shadow:0 12px 30px rgba(0,0,0,.2); opacity:0;
              transform:translateY(-6px); transition:opacity .3s, transform .3s; pointer-events:none; }
  .mt-toast.show { opacity:1; transform:none; }
  .mt-toast b { color:var(--mt-lime); }

  /* ---------- DEMO ONLY global chat ---------- */
  .mt-chat { position:fixed; right:24px; bottom:16px; z-index:1000040; display:flex; flex-direction:column; align-items:center; gap:4px; }
  .mt-fab { position:relative; width:56px; height:56px; border-radius:50%; border:none; background:var(--mt-green); color:#fff; cursor:pointer;
            box-shadow:0 10px 26px rgba(0,166,81,.35); display:flex; align-items:center; justify-content:center; }
  .mt-fab:focus-visible { outline:3px solid var(--mt-ink); outline-offset:3px; }
  .mt-unread { position:absolute; top:-4px; right:-4px; min-width:20px; height:20px; padding:0 6px; border-radius:99px; background:var(--mt-ink);
               color:#fff; font-size:11px; font-weight:800; line-height:20px; text-align:center; font-variant-numeric:tabular-nums; }
  .mt-unread[hidden] { display:none; }
  .mt-online { font-size:11px; font-weight:600; color:var(--mt-muted); background:rgba(245,245,247,.9); border-radius:99px; padding:1px 7px; }
  .mt-online::before { content:""; display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--mt-green); margin-right:4px; vertical-align:1px; }
  .mt-panel { position:fixed; right:24px; bottom:24px; width:360px; height:480px; z-index:1000045; background:var(--mt-card);
              border:1px solid var(--mt-line); border-radius:22px; box-shadow:0 20px 60px rgba(0,0,0,.18); display:flex; flex-direction:column; overflow:hidden; }
  .mt-panel[hidden] { display:none; }
  .mt-ph { display:flex; align-items:center; gap:8px; padding:12px 14px 8px; }
  .mt-ph h3 { margin:0; font-size:16px; font-weight:700; letter-spacing:-.01em; color:var(--mt-ink); padding:0; }
  .mt-tag { font-size:10px; font-weight:700; letter-spacing:.04em; color:var(--mt-muted); background:#eef0f3; border-radius:99px; padding:2px 8px; }
  .mt-x { margin-left:auto; width:30px; height:30px; border-radius:50%; border:none; background:#eef0f3; color:var(--mt-ink); cursor:pointer; font-size:16px; line-height:30px; }
  .mt-x:focus-visible, .mt-chip:focus-visible, .mt-send:focus-visible { outline:2px solid var(--mt-green); outline-offset:2px; }
  .mt-chips { display:flex; gap:6px; padding:0 14px 8px; flex-wrap:wrap; }
  .mt-chip { position:relative; font-size:12px; font-weight:600; border-radius:99px; padding:4px 10px; border:1px solid var(--mt-line); background:var(--mt-card);
             color:var(--mt-muted); cursor:pointer; }
  .mt-chip[aria-pressed="true"] { background:var(--mt-ink); color:#fff; border-color:var(--mt-ink); }
  .mt-chip.new::after { content:""; position:absolute; top:-2px; right:-2px; width:8px; height:8px; border-radius:50%; background:var(--mt-green); }
  .mt-pin { margin:0 14px 6px; padding:8px 10px; border-radius:12px; background:var(--mt-tint); font-size:13px; color:var(--mt-ink); line-height:1.35; }
  .mt-pin b { display:block; font-size:10px; letter-spacing:.06em; text-transform:uppercase; color:var(--mt-deep); margin-bottom:2px; }
  .mt-list { flex:1; overflow-y:auto; padding:4px 14px 6px; display:flex; flex-direction:column; gap:10px; background:var(--mt-card); }
  .mt-msg { display:flex; gap:8px; align-items:flex-start; }
  .mt-av { flex:none; width:28px; height:28px; border-radius:50%; font-size:11px; font-weight:800; display:flex; align-items:center; justify-content:center; color:#fff; }
  .mt-body { min-width:0; }
  .mt-meta { font-size:12px; color:var(--mt-muted); } .mt-meta b { color:var(--mt-ink); margin-right:6px; }
  .mt-text { font-size:13.5px; color:var(--mt-ink); line-height:1.38; overflow-wrap:anywhere; }
  .mt-msg.me .mt-text { background:var(--mt-tint); border-radius:10px; padding:4px 8px; }
  .mt-typing { font-size:12px; color:var(--mt-muted); padding:0 14px 4px; font-style:italic; min-height:16px; }
  .mt-form { display:flex; gap:8px; padding:10px 12px 12px; border-top:1px solid var(--mt-line); }
  .mt-form input { flex:1; min-width:0; border:1px solid var(--mt-line); border-radius:99px; padding:9px 14px; font-size:14px; background:var(--mt-bg); color:var(--mt-ink); font-family:inherit; }
  .mt-form input:focus { outline:2px solid var(--mt-green); outline-offset:0; }
  .mt-send { width:38px; height:38px; border-radius:50%; border:none; background:var(--mt-green); color:#fff; cursor:pointer; display:flex; align-items:center; justify-content:center; }

  @media (max-width: 640px) {
    .topbar { flex-wrap:wrap; padding-right:184px !important; }
    .mt-hero { top:10px; right:10px; flex-direction:row-reverse; align-items:flex-start; gap:6px; }
    .mt-badge { transform:scale(.75); transform-origin:top right; margin-left:-24px; margin-bottom:-24px; }
    .mt-team { margin-top:22px; font-size:12px; }
    .mt-hint { display:none !important; }
    .mt-pop { position:fixed; top:96px; right:10px; left:10px; width:auto; }
    .mt-toast { top:96px; left:12px; right:12px; max-width:none; }
    .mt-panel { inset:0; width:auto; height:auto; border-radius:0; right:0; bottom:0; }
  }
  @media (prefers-reduced-motion: reduce) {
    .mt-hero[data-state="risk"] .mt-badge, .mt-node.glow { animation:none !important; }
    .mt-toast, .mt-hint { transition:none !important; }
  }`;

  var css = d.getElementById("mt-widgets-css");
  if (!css) { css = el("style"); css.id = "mt-widgets-css"; d.head.appendChild(css); }
  css.textContent = CSS;

  if (W.version !== VERSION) {            // (re)build once per page load / code version
    ["mt-hero", "mt-toast", "mt-chat"].forEach(function (id) { var n = d.getElementById(id); if (n) n.remove(); });
    if (W.timer) clearTimeout(W.timer);
    W.version = VERSION; W.prev = null; W.hero = buildHero(); W.chat = buildChat();
  }
  updateHero(DATA);

  // ================================================================ streak hero
  function buildHero() {
    var root = el("div", "mt-hero"); root.id = "mt-hero"; root.hidden = true;
    var badge = el("button", "mt-badge"); badge.type = "button";
    badge.setAttribute("aria-haspopup", "dialog"); badge.setAttribute("aria-expanded", "false"); badge.setAttribute("aria-controls", "mt-pop");
    var ring = sv("svg", { viewBox: "0 0 136 136", "class": "mt-ring", "aria-hidden": "true", focusable: "false" });
    var gO = sv("g", {}), gL = sv("g", {}), gN = sv("g", {});
    ring.appendChild(gO); ring.appendChild(gL); ring.appendChild(gN);
    var num = el("span", "mt-num", "0"), lbl = el("span", "mt-lbl", "sessions");
    badge.appendChild(ring); badge.appendChild(num); badge.appendChild(lbl);
    var team = el("div", "mt-team"); team.hidden = true;
    var tsv = sv("svg", { width: "26", height: "12", viewBox: "0 0 26 12", "aria-hidden": "true" });
    tsv.appendChild(sv("line", { x1: "5", y1: "6", x2: "21", y2: "6", stroke: "#00a651", "stroke-width": "1.6" }));
    tsv.appendChild(sv("circle", { cx: "5", cy: "6", r: "4", fill: "#00a651" }));
    tsv.appendChild(sv("circle", { cx: "21", cy: "6", r: "4", fill: "#9be15d" }));
    var tt = el("span"); team.appendChild(tsv); team.appendChild(tt);
    var hint = el("div", "mt-hint"); hint.hidden = true; hint.setAttribute("role", "status");
    var pop = el("div", "mt-pop"); pop.id = "mt-pop"; pop.hidden = true; pop.setAttribute("role", "dialog"); pop.setAttribute("aria-label", "Streak details");
    root.appendChild(badge); root.appendChild(team); root.appendChild(hint); root.appendChild(pop);
    var toast = el("div", "mt-toast"); toast.id = "mt-toast"; toast.setAttribute("role", "status"); toast.setAttribute("aria-live", "polite");
    d.body.appendChild(root); d.body.appendChild(toast);

    var hover = false;
    function openPop(byHover) { hover = byHover; pop.hidden = false; badge.setAttribute("aria-expanded", "true"); toast.classList.remove("show"); }
    function closePop() { pop.hidden = true; badge.setAttribute("aria-expanded", "false"); hover = false; }
    badge.addEventListener("click", function () { if (pop.hidden || hover) { openPop(false); } else { closePop(); } });
    root.addEventListener("mouseenter", function () { if (pop.hidden) openPop(true); });
    root.addEventListener("mouseleave", function () { if (hover) closePop(); });
    d.addEventListener("keydown", function (e) { if (e.key === "Escape" && !pop.hidden) { closePop(); badge.focus(); } });
    d.addEventListener("click", function (e) { if (!pop.hidden && !root.contains(e.target)) closePop(); });
    return { root: root, badge: badge, num: num, gO: gO, gL: gL, gN: gN, team: team, tt: tt, hint: hint, pop: pop, toast: toast };
  }

  function updateHero(D) {
    var H = W.hero;
    if (!D.show) { H.root.hidden = true; return; }
    H.root.hidden = false; H.root.setAttribute("data-state", D.state);
    var n = D.streak, word = n === 1 ? "session" : "sessions";
    H.badge.setAttribute("aria-label", n + " " + word + " in a row" + (D.demo ? " (demo values)" : "") + ". Show details");
    // ring: last 7 sessions, oldest -> newest clockwise from the top
    [H.gO, H.gL, H.gN].forEach(function (g) { while (g.firstChild) g.removeChild(g.firstChild); });
    D.milestones.forEach(function (m, i) { H.gO.appendChild(sv("circle", { "class": "mt-orbit", cx: "68", cy: "68", r: String(54 + i * 4) })); });
    var pts = D.ring.map(function (s, i, a) {
      var ang = (-90 + i * 360 / Math.max(a.length, 7)) * Math.PI / 180;
      return { x: 68 + 42 * Math.cos(ang), y: 68 + 42 * Math.sin(ang), s: s };
    });
    for (var i = 1; i < pts.length; i++) {
      if (pts[i].s.done && pts[i - 1].s.done)
        H.gL.appendChild(sv("line", { "class": "mt-link", x1: pts[i - 1].x, y1: pts[i - 1].y, x2: pts[i].x, y2: pts[i].y }));
    }
    var glowKey = "matteo.glow." + D.student + "." + D.todayId + (D.demo ? ".demo" : "");
    pts.forEach(function (p) {
      var c = "mt-node" + (p.s.done ? " on" : "") + (p.s.today ? " today" + (p.s.done ? "" : " open") : "");
      if (p.s.today && p.s.done && !reduce && !store(glowKey)) { c += " glow"; store(glowKey, "1"); }
      H.gN.appendChild(sv("circle", { "class": c, cx: p.x, cy: p.y, r: p.s.today ? "5" : "4.2" }));
    });
    // number: count up once on load / when it changes
    H.num.classList.toggle("small", n >= 100);
    var from = (W.prev == null) ? 0 : W.prev;
    if (W.prev !== n) {
      if (reduce || from === n) { H.num.textContent = String(n); }
      else {
        var t0 = performance.now(), dur = 900;
        (function step(t) {
          var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
          H.num.textContent = String(Math.round(from + (n - from) * e));
          if (k < 1) requestAnimationFrame(step);
        })(t0);
      }
      W.prev = n;
    }
    // team chip (real data only when available)
    if (D.team != null) {
      H.team.hidden = false;
      H.tt.textContent = (D.teamName || "Team") + " · " + D.team;
      H.team.setAttribute("aria-label", (D.teamName || "Team") + ": " + D.team + " sessions in a row with every member" + (D.demo ? " (demo values)" : ""));
    } else { H.team.hidden = true; }
    // state hint (short-lived on screen; always in the popover)
    var stateLine = D.state === "done" ? "Done for today's session. Nice and calm."
      : D.state === "risk" ? "Do today's session to keep it."
      : "Fresh start: do today's session to light the first node.";
    if (D.state !== "done") {
      H.hint.textContent = stateLine; H.hint.hidden = false; H.hint.classList.remove("fade");
      clearTimeout(W.hintT); W.hintT = setTimeout(function () { H.hint.classList.add("fade"); setTimeout(function () { H.hint.hidden = true; }, 700); }, 6000);
    } else { H.hint.hidden = true; }
    // popover
    var P = H.pop; while (P.firstChild) P.removeChild(P.firstChild);
    var h = el("h4", null, n + " " + word + " in a row");
    if (D.demo) h.appendChild(el("span", "mt-demo", "demo values"));
    P.appendChild(h);
    P.appendChild(el("p", "mt-state", stateLine));
    var days = el("div", "mt-days");
    D.ring.forEach(function (s) {
      var c = el("div", "mt-day" + (s.done ? " on" : "") + (s.today ? " today" : ""));
      c.appendChild(el("i")); c.appendChild(el("b", null, s.today ? "today" : s.id));
      c.title = (s.title ? s.title + " · " : "") + (s.done ? "taken part" : "missed");
      days.appendChild(c);
    });
    P.appendChild(el("p", null, "Last " + D.ring.length + " sessions"));
    P.appendChild(days);
    if (D.best) P.appendChild(el("p", null, "Best run: " + D.best + " sessions"));
    P.appendChild(el("p", null, "Counts lecture sessions where you took the session quiz."));
    // milestone toast, once per milestone (per browser)
    var top = D.milestones.length ? D.milestones[D.milestones.length - 1] : null;
    var COPY = { 3: "Matteo knows your name now.", 7: "Matteo is starting to get it.", 14: "Matteo asks sharper questions now.", 30: "Matteo is ready for the exam." };
    var mk = "matteo.ms." + D.student + "." + top + (D.demo ? ".demo" : "");
    if (top && !store(mk)) {
      store(mk, "1");
      var T = H.toast; while (T.firstChild) T.removeChild(T.firstChild);
      T.appendChild(el("b", null, top + " sessions: ")); T.appendChild(d.createTextNode(COPY[top]));
      T.classList.add("show"); clearTimeout(W.toastT);
      W.toastT = setTimeout(function () { T.classList.remove("show"); }, 4500);
    }
  }

  // ================================================================ DEMO ONLY: global chat
  // DEMO ONLY: hard-coded, no backend. Seeded messages are fictional; nothing is sent or stored.
  function buildChat() {
    var COLORS = ["#00a651", "#007a3d", "#1d1d1f", "#6e6e73", "#3d9a52"];
    var now = Date.now();
    function m(name, text, minsAgo) { return { name: name, text: text, ts: now - minsAgo * 60000 }; }
    var CH = {
      "#general": [
        m("Giulia", "Morning! Physics I quiz is open until 18:00, don't forget.", 41),
        m("Marco", "Is the lecture recording up yet? I missed the part about friction.", 38),
        m("Aisha", "Not yet, but the handout covers it: section on static vs kinetic.", 35),
        m("Tomás", "Exam in three weeks and I still mix up mass and weight. Help.", 29),
        m("Priya", "Mass is how much stuff, weight is the force of gravity on it. Explaining it to Matteo fixed it for me.", 27),
        m("Luca", "Anyone free to teach Matteo with us at 16:00? Library, second floor.", 20),
        m("Sofia", "I'm in! Bringing snacks for the third law debate.", 18),
        m("Kenji", "Team C just hit 5 sessions in a row. Your move, Team A.", 9),
        m("Elif", "Challenge accepted. Matteo still thinks the truck pushes harder though.", 6),
        m("Noah", "Classic Matteo. Did you ask him about the forces on BOTH cars?", 3)
      ],
      "#physics-1": [
        m("Chiara", "Why does a box at rest have no friction if nobody pushes it?", 33),
        m("Omar", "Because static friction only answers a push. No push, nothing to cancel.", 31),
        m("Priya", "Free-body diagram tip: one object per drawing. Saved my homework.", 22),
        m("Marco", "Constant velocity means net force zero. Took me a week to believe it.", 15),
        m("Aisha", "Matteo asked me where the force \"is stored\" in a ball. Good question honestly.", 7),
        m("Giulia", "It isn't stored anywhere: a force is an interaction between two objects.", 5)
      ],
      "#study-buddies": [
        m("Luca", "Looking for one more person for a Thursday study group.", 44),
        m("Tomás", "Me! Mechanics is my weak spot.", 40),
        m("Sofia", "We teach Matteo for 20 minutes, then quiz each other. Works great.", 26),
        m("Kenji", "Any group doing the incline problems this weekend?", 12),
        m("Elif", "Ours. Sunday 11:00, online. Ping me.", 8)
      ]
    };
    var LIVE = [
      ["#general", "Marco", "Recording is up now, check the course page."],
      ["#physics-1", "Tomás", "So the scale in an elevator shows the normal force, not my weight?"],
      ["#physics-1", "Priya", "Yes! That's exactly why it changes when the elevator accelerates."],
      ["#general", "Aisha", "Quiz done. Now teaching Matteo what I got wrong."],
      ["#study-buddies", "Noah", "Can I join the Sunday group?"],
      ["#general", "Giulia", "Matteo just asked my group if heavier things fall faster. Chaos."],
      ["#physics-1", "Omar", "They don't: bigger force, but bigger mass too. Same acceleration."],
      ["#general", "Sofia", "Team A at 4 sessions. We're coming for you, Team C."],
      ["#study-buddies", "Elif", "Sure Noah, link in the course chat later."],
      ["#physics-1", "Chiara", "Got it. Friction just matches the push until it can't anymore."],
      ["#general", "Kenji", "Anyone else nervous for the midterm? Asking for a friend (me)."],
      ["#general", "Luca", "Same. Teaching Matteo every day is the only thing that helps."],
      ["#physics-1", "Marco", "Third law pairs act on DIFFERENT objects. Writing that on my hand."],
      ["#study-buddies", "Tomás", "Thursday group: we're four now, one seat left."],
      ["#general", "Priya", "Pro tip: when Matteo says \"I don't get it\", draw it for him."],
      ["#physics-1", "Aisha", "Net force zero doesn't mean no forces. It means they cancel."],
      ["#general", "Noah", "Matteo finally got the truck question right. Proud parent moment."],
      ["#study-buddies", "Sofia", "Library is packed, moving to room 3B."],
      ["#general", "Elif", "Okay, back to studying. See you at the lecture!"]
    ];
    var MAX = 40;
    var total = Object.keys(CH).reduce(function (a, k) { return a + CH[k].length; }, 0);
    var active = "#general", unread = 3, open = false;

    var wrap = el("div", "mt-chat"); wrap.id = "mt-chat";
    var fab = el("button", "mt-fab"); fab.type = "button";
    fab.setAttribute("aria-label", "Open global chat (simulated preview)"); fab.setAttribute("aria-expanded", "false"); fab.setAttribute("aria-controls", "mt-panel");
    var ico = sv("svg", { width: "26", height: "26", viewBox: "0 0 24 24", fill: "none", stroke: "#fff", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" });
    ico.appendChild(sv("path", { d: "M7.9 20A9 9 0 1 0 4 16.1L2 22Z" }));
    var badge = el("span", "mt-unread", String(unread)); badge.setAttribute("aria-hidden", "true");
    fab.appendChild(ico); fab.appendChild(badge);
    var online = el("div", "mt-online", "128 online");
    var panel = el("section", "mt-panel"); panel.id = "mt-panel"; panel.hidden = true;
    panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "Global chat, simulated preview");
    var ph = el("div", "mt-ph"); ph.appendChild(el("h3", null, "Global chat")); ph.appendChild(el("span", "mt-tag", "Preview · simulated"));
    var x = el("button", "mt-x", "×"); x.type = "button"; x.setAttribute("aria-label", "Close chat"); ph.appendChild(x);
    var chips = el("div", "mt-chips"); chips.setAttribute("role", "group"); chips.setAttribute("aria-label", "Channels");
    var chipEls = {};
    Object.keys(CH).forEach(function (c) {
      var b = el("button", "mt-chip", c); b.type = "button"; b.setAttribute("aria-pressed", c === active ? "true" : "false");
      b.addEventListener("click", function () { active = c; b.classList.remove("new"); renderList(); syncChips(); input.placeholder = "Message " + c; });
      chipEls[c] = b; chips.appendChild(b);
    });
    var pin = el("div", "mt-pin"); pin.appendChild(el("b", null, "Pinned · Matteo"));
    pin.appendChild(d.createTextNode("Can someone explain why heavier things don't fall faster?"));
    var list = el("div", "mt-list"); list.setAttribute("role", "log"); list.setAttribute("aria-live", "polite"); list.setAttribute("aria-label", "Messages");
    var typing = el("div", "mt-typing"); typing.setAttribute("aria-hidden", "true");
    var form = el("form", "mt-form");
    var input = el("input"); input.type = "text"; input.maxLength = 300; input.placeholder = "Message " + active; input.setAttribute("aria-label", "Message");
    var send = el("button", "mt-send"); send.type = "submit"; send.setAttribute("aria-label", "Send message");
    var sico = sv("svg", { width: "18", height: "18", viewBox: "0 0 24 24", fill: "none", stroke: "#fff", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" });
    sico.appendChild(sv("path", { d: "m22 2-7 20-4-9-9-4Z" })); sico.appendChild(sv("path", { d: "M22 2 11 13" }));
    send.appendChild(sico); form.appendChild(input); form.appendChild(send);
    [ph, chips, pin, list, typing, form].forEach(function (n) { panel.appendChild(n); });
    wrap.appendChild(fab); wrap.appendChild(online);
    d.body.appendChild(wrap); d.body.appendChild(panel);

    function initials(n) { return n === "You" ? "Y" : n.split(/\s+/).map(function (p) { return p.charAt(0); }).join("").slice(0, 2).toUpperCase(); }
    function color(n) { var h = 0; for (var i = 0; i < n.length; i++) h = (h * 31 + n.charCodeAt(i)) >>> 0; return COLORS[h % COLORS.length]; }
    function ago(ts) { var s = Math.max(0, (Date.now() - ts) / 1000); return s < 60 ? "now" : s < 3600 ? Math.floor(s / 60) + "m" : Math.floor(s / 3600) + "h"; }
    function msgEl(msg) {          // all user/seed text goes through textContent: always escaped
      var r = el("div", "mt-msg" + (msg.me ? " me" : ""));
      var av = el("div", "mt-av", initials(msg.name)); av.style.background = msg.me ? "#9be15d" : color(msg.name);
      if (msg.me) av.style.color = "#1d1d1f";
      av.setAttribute("aria-hidden", "true");
      var body = el("div", "mt-body"), meta = el("div", "mt-meta");
      meta.appendChild(el("b", null, msg.name)); var t = el("span", "mt-ago", ago(msg.ts)); t.dataset.ts = String(msg.ts); meta.appendChild(t);
      body.appendChild(meta); body.appendChild(el("div", "mt-text", msg.text));
      r.appendChild(av); r.appendChild(body); return r;
    }
    function renderList() { while (list.firstChild) list.removeChild(list.firstChild); CH[active].forEach(function (mm) { list.appendChild(msgEl(mm)); }); list.scrollTop = list.scrollHeight; }
    function syncChips() { Object.keys(chipEls).forEach(function (c) { chipEls[c].setAttribute("aria-pressed", c === active ? "true" : "false"); }); }
    function syncBadge() { badge.textContent = String(unread); badge.hidden = unread <= 0; fab.setAttribute("aria-label", "Open global chat (simulated preview)" + (unread > 0 ? ", " + unread + " unread" : "")); }
    function openPanel() { open = true; panel.hidden = false; fab.setAttribute("aria-expanded", "true"); unread = 0; syncBadge(); renderList(); input.focus(); }
    function closePanel() { open = false; panel.hidden = true; fab.setAttribute("aria-expanded", "false"); fab.focus(); }
    fab.addEventListener("click", function () { open ? closePanel() : openPanel(); });
    x.addEventListener("click", closePanel);
    panel.addEventListener("keydown", function (e) { if (e.key === "Escape") { e.stopPropagation(); closePanel(); } });
    form.addEventListener("submit", function (e) {
      e.preventDefault(); var v = input.value.trim(); if (!v) return;
      var mm = { name: "You", text: v, ts: Date.now(), me: true }; CH[active].push(mm); list.appendChild(msgEl(mm)); list.scrollTop = list.scrollHeight; input.value = "";
    });
    setInterval(function () { list.querySelectorAll(".mt-ago").forEach(function (s) { s.textContent = ago(Number(s.dataset.ts)); }); }, 30000);

    var qi = 0;
    function schedule() {
      if (qi >= LIVE.length || total >= MAX) return;
      W.timer = setTimeout(function () {
        var next = LIVE[qi++], ch = next[0], name = next[1];
        var showTyping = open && ch === active;
        if (showTyping) typing.textContent = name + " is typing…";
        setTimeout(function () {
          typing.textContent = "";
          var mm = { name: name, text: next[2], ts: Date.now() }; CH[ch].push(mm); total++;
          if (open && ch === active) { list.appendChild(msgEl(mm)); list.scrollTop = list.scrollHeight; }
          else if (open) { chipEls[ch].classList.add("new"); }
          else { unread++; syncBadge(); }
          schedule();
        }, showTyping ? 1600 : 0);
      }, 8000 + Math.random() * 7000);
    }
    syncBadge(); schedule();
    return { panel: panel };
  }
})();
</script>
"""
