"""AI teaching audit for the PROFESSOR: where the class breaks -> what to recap next lecture, and how.

Pipeline:  anonymous aggregate evidence (code)  ->  teaching coach (LLM, strict JSON, prompts/coach.md)
           ->  validated in code (ids, numbers' sources, group tasks)  ->  mind map + recap plan.
No student names or raw text ever reach the coach. If the LLM fails, a rule-based draft is shown instead.
"""
from __future__ import annotations

import hashlib
import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import networkx as nx

import quiz as quizmod
from graph import band, load_graph
from llm import LLMError, chat
from log import log_step
from tools import MISCONCEPTIONS, STUDENTS_DIR, load_flags

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "audit.json"
PROMPT = (ROOT / "prompts" / "coach.md").read_text(encoding="utf-8")
TASKS = {t["id"]: t for t in json.loads((ROOT / "materials" / "physics1_newton" / "group_discussion_prompts.json")
                                         .read_text(encoding="utf-8"))["prompts"]}


# ---------------------------------------------------------------- 1 evidence (deterministic, anonymous)
def evidence() -> dict:
    G = load_graph()
    students = [json.loads(p.read_text(encoding="utf-8")) for p in STUDENTS_DIR.glob("*.json")]
    n = len(students)
    today = quizmod.current()
    quiz_pct = quizmod.results(today["id"])["per_concept"] if today else {}
    flags = {f["concept_id"]: f for f in load_flags()}
    misc = Counter(m if isinstance(m, str) else m["id"] for s in students for m in s.get("misconceptions_seen", []))
    topics = {}
    for c in G.nodes:
        lv = Counter(band(s["mastery"][c]["score"]) if c in s["mastery"] else "untested" for s in students)
        f = flags.get(c)
        weak_prereqs = [p for p in nx.descendants(G, c)
                        if sum(1 for s in students if p in s["mastery"] and s["mastery"][p]["score"] <= 1) >= 2]
        topics[c] = {"to_fix": lv["weak"], "almost": lv["shaky"], "solid": lv["solid"], "not_yet": lv["untested"],
                     "quiz_pct_correct": round(quiz_pct[c] * 100) if c in quiz_pct else None,
                     "flag": {"students": f["count"], "status": f["status"], "reason": f["reason"],
                              "misconception_ids": f["misconception_ids"]} if f else None,
                     "weak_prerequisites": weak_prereqs, "source": G.nodes[c]["source"]}
    ev = {"class_size": n, "topics": topics, "misconceptions_seen": dict(misc.most_common(6)),
          "quiz": {"title": today["title"], "answered": len(quizmod.results(today["id"])["scores"])} if today else None}
    ev["hash"] = hashlib.sha256(json.dumps(ev, sort_keys=True).encode()).hexdigest()[:12]
    return ev


def _priority(t: dict) -> float:
    if t["flag"] and t["flag"]["status"] == "rejected":
        return -1
    q = (100 - t["quiz_pct_correct"]) / 100 if t["quiz_pct_correct"] is not None else 0
    return t["to_fix"] * 2 + t["almost"] + q * 3 + (t["flag"]["students"] if t["flag"] else 0)


# ---------------------------------------------------------------- 2 coach (LLM) + validation + fallback
def _plain(text: str) -> str:
    """Turn field names / topic ids the model may echo into readable words."""
    G = load_graph()
    for k, v in {"to_fix": "to fix", "not_yet": "not yet", "quiz_pct_correct": "quiz % correct"}.items():
        text = text.replace(k, v)
    for c in sorted(G.nodes, key=len, reverse=True):
        text = text.replace(c, G.nodes[c]["name"])
    return text


def _validate(raw: dict, ev: dict) -> dict:
    G = load_graph()
    pri = []
    for p in raw.get("priorities", [])[:3]:
        c = p.get("concept_id")
        if c not in G:
            continue
        r = p.get("recap") or {}
        pri.append({"concept_id": c, "severity": "high" if p.get("severity") == "high" else "medium",
                    "evidence": _plain(str(p.get("evidence", "")))[:240],
                    "misconception_id": p.get("misconception_id") if p.get("misconception_id") in MISCONCEPTIONS else None,
                    "teach_first": p.get("teach_first") if p.get("teach_first") in G and p.get("teach_first") != c else None,
                    "recap": {"minutes": max(3, min(20, int(r.get("minutes", 8) or 8))),
                              "hook": _plain(str(r.get("hook", "")))[:220],
                              "steps": [_plain(str(s))[:160] for s in (r.get("steps") or [])][:3],
                              "check_question": _plain(str(r.get("check_question", "")))[:220],
                              "group_task_id": r.get("group_task_id") if r.get("group_task_id") in TASKS else None}})
    if not pri:
        raise ValueError("coach returned no valid priorities")
    return {"headline": _plain(str(raw.get("headline", "")))[:220], "priorities": pri,
            "going_well": [c for c in raw.get("going_well", []) if c in G][:3],
            "caveat": _plain(str(raw.get("caveat", "")))[:240]}


def _fallback(ev: dict) -> dict:
    """Rule-based draft (no LLM): used when the coach is unavailable."""
    G = load_graph()
    ranked = sorted(ev["topics"].items(), key=lambda kv: -_priority(kv[1]))
    pri = []
    for c, t in ranked[:3]:
        if _priority(t) <= 0:
            break
        ids = (t["flag"] or {}).get("misconception_ids") or []
        mid = ids[0] if ids else None
        task = next((k for k, v in TASKS.items() if mid and mid in v["trigger"]), None)
        pri.append({"concept_id": c, "severity": "high" if t["to_fix"] >= 3 else "medium",
                    "evidence": f"{t['to_fix']} of {ev['class_size']} students to fix, {t['almost']} almost"
                                + (f"; quiz {t['quiz_pct_correct']}% correct" if t["quiz_pct_correct"] is not None else "") + ".",
                    "misconception_id": mid, "teach_first": t["weak_prerequisites"][0] if t["weak_prerequisites"] else None,
                    "recap": {"minutes": 8, "hook": f"Ask the class to predict before you explain: {G.nodes[c]['name']}.",
                              "steps": ["Students predict alone, then vote.", "Pairs explain their reasoning to each other.",
                                        "Reveal and discuss the common wrong idea."],
                              "check_question": f"One quick question on {G.nodes[c]['name']} before moving on.",
                              "group_task_id": task}})
    return {"headline": "Rule-based draft: recap the topics with the most students to fix first.", "priorities": pri,
            "going_well": [c for c, t in ranked[::-1] if t["solid"] >= ev["class_size"] / 3][:3],
            "caveat": "Generated without the AI coach (offline draft). Counts come straight from the class data."}


def generate() -> dict:
    G = load_graph()
    ev = evidence()
    payload = {"EVIDENCE": {k: v for k, v in ev.items() if k != "hash"},
               "TOPICS": [{"id": c, "name": G.nodes[c]["name"], "description": G.nodes[c]["description"]} for c in G.nodes],
               "MISCONCEPTIONS": MISCONCEPTIONS,
               "GROUP_TASKS": [{k: t[k] for k in ("id", "title", "question", "trigger")} for t in TASKS.values()]}
    try:
        raw = chat(PROMPT, [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], json=True,
                   effort="medium", max_tokens=8000)
        audit, by = _validate(raw, ev), "AI coach (Claude Opus 5.5)"
    except (LLMError, ValueError, TypeError, KeyError) as e:
        log_step("audit_coach_error", output=str(e)[:200])
        audit, by = _fallback(ev), "rule-based draft (AI unavailable)"
    doc = {"generated_at": datetime.now().strftime("%d %b %Y, %H:%M"), "generated_by": by, "evidence_hash": ev["hash"],
           "class_size": ev["class_size"], "audit": audit, "planned": []}
    PATH.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    log_step("tool.teaching_audit", output={"priorities": [p["concept_id"] for p in audit["priorities"]], "by": by})
    return doc


def load() -> dict | None:
    return json.loads(PATH.read_text(encoding="utf-8")) if PATH.exists() else None


def toggle_planned(concept_id: str) -> None:
    doc = load()
    if doc:
        doc["planned"] = [c for c in doc["planned"] if c != concept_id] if concept_id in doc["planned"] \
            else doc["planned"] + [concept_id]
        PATH.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")


def reset() -> None:
    if PATH.exists():
        PATH.unlink()


# ---------------------------------------------------------------- 3 mind map (HTML, all text escaped)
SEV = {"high": ("#d64545", "#fdecec"), "medium": ("#d9a21b", "#fdf5e1")}


def mindmap_html(doc: dict) -> str:
    G = load_graph()
    a = doc["audit"]
    e = html.escape
    rows = []  # (priority, leaves)
    for p in a["priorities"]:
        leaves = []
        if p["misconception_id"]:
            leaves.append(("Misconception", MISCONCEPTIONS[p["misconception_id"]]))
        if p["teach_first"]:
            leaves.append(("Recap first", G.nodes[p["teach_first"]]["name"]))
        leaves.append(("Open with", p["recap"]["hook"]))
        leaves.append(("Check", p["recap"]["check_question"]))
        rows.append((p, leaves[:4]))
    leaf_h, gap, W = 78, 18, 1180
    blocks = [max(1, len(l)) * leaf_h + gap for _, l in rows]
    good_h = 90 if a["going_well"] else 0
    H = max(sum(blocks) + good_h + 40, 360)
    root = (30, H / 2 - 55, 230, 110)
    nodes, lines, y = [], [], 20
    for (p, leaves), bh in zip(rows, blocks):
        col, bg = SEV[p["severity"]]
        py = y + bh / 2 - 38
        px = 330
        nodes.append(f"<div class='n pri' style='left:{px}px;top:{py}px;border-color:{col};background:{bg}'>"
                     f"<div class='sev' style='color:{col}'>{'HIGH' if p['severity'] == 'high' else 'MEDIUM'} · {p['recap']['minutes']} min</div>"
                     f"<div class='t'>{e(G.nodes[p['concept_id']]['name'])}</div></div>")
        lines.append((root[0] + root[2], root[1] + root[3] / 2, px, py + 38, col, 3))
        for i, (k, v) in enumerate(leaves):
            ly = y + i * leaf_h
            nodes.append(f"<div class='n leaf' style='left:640px;top:{ly}px'><div class='k'>{e(k)}</div>"
                         f"<div class='v'>{e(v)}</div></div>")
            lines.append((px + 250, py + 38, 640, ly + 26, "#c4c8ce", 1.6))
        y += bh
    if a["going_well"]:
        gy = y + 6
        names = " · ".join(e(G.nodes[c]["name"]) for c in a["going_well"])
        nodes.append(f"<div class='n good' style='left:330px;top:{gy}px'><div class='sev' style='color:#1f9d55'>GOING WELL</div>"
                     f"<div class='v'>{names}</div></div>")
        lines.append((root[0] + root[2], root[1] + root[3] / 2, 330, gy + 30, "#1f9d55", 2))
    svg = "".join(f"<path d='M{x1},{y1} C{(x1 + x2) / 2},{y1} {(x1 + x2) / 2},{y2} {x2},{y2}' stroke='{c}' "
                  f"stroke-width='{w}' fill='none' stroke-linecap='round'/>" for x1, y1, x2, y2, c, w in lines)
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,sans-serif;background:#ffffff;color:#1d1d1f}}
.wrap{{position:relative;width:{W}px;height:{H}px}}
svg{{position:absolute;left:0;top:0}}
.n{{position:absolute;box-sizing:border-box;border-radius:16px}}
.root{{left:{root[0]}px;top:{root[1]}px;width:{root[2]}px;height:{root[3]}px;background:#111214;color:#f5f5f7;padding:16px 18px;
       box-shadow:0 8px 24px rgba(0,0,0,.18)}}
.root .k{{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#9be15d;font-weight:700}}
.root .t{{font-size:19px;font-weight:700;margin-top:6px;line-height:1.2}}
.pri{{width:250px;height:76px;border:2px solid;padding:10px 14px;box-shadow:0 4px 14px rgba(0,0,0,.06)}}
.sev{{font-size:10.5px;font-weight:800;letter-spacing:.1em}}
.t{{font-size:15.5px;font-weight:700;margin-top:3px;line-height:1.2}}
.leaf{{width:520px;height:{leaf_h - 10}px;background:#f5f5f7;border:1px solid #e3e3e8;padding:7px 12px;overflow:hidden}}
.k{{font-size:10.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#6e6e73}}
.v{{font-size:13px;line-height:1.3;margin-top:2px}}
.good{{width:560px;min-height:62px;background:#eaf7ef;border:1px solid #bfe5cc;padding:9px 14px}}
</style></head><body><div class='wrap'>
<svg width='{W}' height='{H}'>{svg}</svg>
<div class='n root'><div class='k'>Class audit · {e(doc['generated_at'])}</div><div class='t'>Newton's laws<br>what to recap next</div></div>
{''.join(nodes)}
</div>
<script>
  // scale the whole map to the panel width so nothing is cut off
  const W = {W}, H = {H}, wrap = document.querySelector('.wrap');
  function fit() {{ const s = Math.min(1, (window.innerWidth - 6) / W);
    wrap.style.transform = 'scale(' + s + ')'; wrap.style.transformOrigin = '0 0';
    document.body.style.height = (H * s) + 'px'; }}
  fit(); window.addEventListener('resize', fit);
</script></body></html>""", int(H * 0.8) + 10


def markdown(doc: dict) -> str:
    G = load_graph()
    a = doc["audit"]
    out = [f"# Recap plan · Physics I · Newton's laws", f"_Generated {doc['generated_at']} by {doc['generated_by']} "
           f"from anonymous class data ({doc['class_size']} students). AI suggestions: the professor decides._", "",
           f"**{a['headline']}**", ""]
    for i, p in enumerate(a["priorities"], 1):
        r = p["recap"]
        out += [f"## {i}. {G.nodes[p['concept_id']]['name']} ({p['severity']}, {r['minutes']} min)", f"- Evidence: {p['evidence']}"]
        if p["misconception_id"]:
            out.append(f"- Misconception to address: {MISCONCEPTIONS[p['misconception_id']]}")
        if p["teach_first"]:
            out.append(f"- Possibly rooted in: {G.nodes[p['teach_first']]['name']} (recap that first)")
        out += [f"- Open with: {r['hook']}"] + [f"  {j}. {s}" for j, s in enumerate(r["steps"], 1)]
        out.append(f"- Check question: {r['check_question']}")
        if r["group_task_id"]:
            t = TASKS[r["group_task_id"]]
            out.append(f"- Group task {t['id']} · {t['title']}: {t['question']}")
        out += [f"- Source to revisit: {G.nodes[p['concept_id']]['source']}", ""]
    if a["going_well"]:
        out.append("**Going well:** " + ", ".join(G.nodes[c]["name"] for c in a["going_well"]))
    out.append(f"\n_{a['caveat']}_")
    return "\n".join(out)
