"""Session quiz (integrated from the team's quiz_feature):
professor uploads lecture PDF/ZIP -> AI drafts a quiz -> professor edits + publishes ->
students answer -> graded deterministically in code (no LLM) -> per-concept gaps.

Integrated changes vs the original FastAPI module: runs inside the Streamlit app (one process,
demo-safe), LLM calls go through app/llm.py (provider-swappable), concepts are tagged with
knowledge-graph IDs, PDF text via pypdf (already a dependency), no names on the professor side.
A ready-to-use quiz is built from the material pack's own answer key (no LLM needed).
"""
from __future__ import annotations

import io
import json
import random
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

import streaks
from graph import load_graph
from llm import LLMError, chat
from log import log_step
from tools import slug

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "quizzes.json"
PACK = ROOT / "materials" / "physics1_newton"
HANDOUT = PACK / "01_Newtons_Laws_Student_Handout.pdf"
PROMPT = (ROOT / "prompts" / "quizmaster.md").read_text(encoding="utf-8")
PACK_QUIZ_ID = "S9"
# pack quiz items -> graph concept (explicit, reviewed by hand)
PACK_ITEMS = {"Q01": "newton_first_law", "Q02": "net_force", "Q04": "newton_third_law",
              "Q06": "static_friction", "Q07": "newton_third_law"}
MAX_FILES, MAX_PDF_BYTES, MAX_CHARS = 20, 30_000_000, 60_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load() -> dict:
    if PATH.exists():
        return json.loads(PATH.read_text(encoding="utf-8"))
    return {"quizzes": {}, "subs": {}}


def _save(db: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(db, indent=1, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- the ready-made quiz
def _pack_quiz() -> dict:
    items = {q["id"]: q for q in json.loads((PACK / "quiz_student.json").read_text(encoding="utf-8"))["items"]}
    key = {q["id"]: q for q in json.loads((PACK / "quiz_instructor_key.json").read_text(encoding="utf-8"))["items"]}
    qs = []
    for qid, concept in PACK_ITEMS.items():
        it, k = items[qid], key[qid]
        letters = [o["id"] for o in it["options"]]
        qs.append({"id": qid, "q": it["stem"], "options": [o["text"] for o in it["options"]],
                   "correct": letters.index(k["correct_option"]), "concept": concept,
                   "explanation": k["explanation"],
                   "source": ", ".join(s.replace("OS-", "OpenStax UP1 §") for s in it["sources"])})
    return {"id": PACK_QUIZ_ID, "title": "Session 9 · Newton's laws", "status": "published",
            "origin": "material pack (instructor key)", "questions": qs, "created": _now(), "published": _now()}


def ensure_default() -> None:
    db = _load()
    if PACK_QUIZ_ID not in db["quizzes"]:
        db["quizzes"][PACK_QUIZ_ID] = _pack_quiz()
        _save(db)
    streaks.ensure_session(PACK_QUIZ_ID, "Newton's laws")


def current() -> dict | None:
    """The newest published quiz = today's session."""
    pub = [q for q in _load()["quizzes"].values() if q["status"] == "published"]
    return max(pub, key=lambda q: q["published"]) if pub else None


def drafts() -> list[dict]:
    return [q for q in _load()["quizzes"].values() if q["status"] == "draft"]


def student_view(quiz: dict) -> list[dict]:
    """What students see: no correct answers, no explanations."""
    return [{"id": q["id"], "q": q["q"], "options": q["options"]} for q in quiz["questions"]]


# ---------------------------------------------------------------- grading (deterministic)
def submit(quiz_id: str, student: str, answers: list[int | None]) -> dict:
    db = _load()
    quiz = db["quizzes"][quiz_id]
    concepts, review, score = {}, [], 0
    for q, a in zip(quiz["questions"], answers):
        ok = a == q["correct"]
        score += ok
        c = concepts.setdefault(q["concept"], [0, 0])
        c[0] += ok
        c[1] += 1
        review.append({"q": q["q"], "your": None if a is None else q["options"][a],
                       "correct": q["options"][q["correct"]], "ok": ok, "explanation": q["explanation"],
                       "source": q["source"], "concept": q["concept"]})
    total = len(quiz["questions"])
    weak = [k for k, (g, t) in concepts.items() if g / t < 0.5]
    sub = {"student": slug(student), "score": score, "max": total, "concepts": concepts,
           "weak_concepts": weak, "submitted_at": _now()}
    db["subs"].setdefault(quiz_id, {})[slug(student)] = sub
    _save(db)
    streaks.record(student, quiz_id)
    log_step("tool.grade_quiz", input={"quiz": quiz_id, "student": slug(student)},
             output={"score": f"{score}/{total}", "weak": weak})
    return {**sub, "review": review}


def results(quiz_id: str) -> dict:
    """Professor view: per-concept % correct and score distribution. No names."""
    subs = list(_load()["subs"].get(quiz_id, {}).values())
    per = {}
    for s in subs:
        for c, (g, t) in s["concepts"].items():
            a = per.setdefault(c, [0, 0])
            a[0] += g
            a[1] += t
    return {"n": len(subs), "per_concept": {c: g / t for c, (g, t) in per.items() if t},
            "scores": [f"{s['score']}/{s['max']}" for s in subs]}


# ---------------------------------------------------------------- generation (professor)
def extract_text(filename: str, data: bytes) -> str:
    """PDF or ZIP of PDFs -> page-tagged text (from the team's ingest.py, using pypdf)."""
    pdfs = []
    if filename.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = [i for i in z.infolist()
                     if i.filename.lower().endswith(".pdf") and not i.filename.startswith("__MACOSX")]
            if len(infos) > MAX_FILES:
                raise ValueError(f"ZIP has {len(infos)} PDFs; max is {MAX_FILES}")
            pdfs = [(i.filename, z.read(i)) for i in infos if i.file_size <= MAX_PDF_BYTES]
    else:
        pdfs = [(filename, data)]
    chunks, used = [], 0
    for name, blob in pdfs:
        for n, page in enumerate(PdfReader(io.BytesIO(blob)).pages, 1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            chunk = f"[{name.split('/')[-1]} p.{n}]\n{text}\n"
            if used + len(chunk) > MAX_CHARS:
                return "\n".join(chunks)
            chunks.append(chunk)
            used += len(chunk)
    if not chunks:
        raise ValueError("No extractable text found (scanned PDF? it needs OCR first).")
    return "\n".join(chunks)


def _validate(qs: list[dict]) -> list[dict]:
    G = load_graph()
    out = []
    for i, q in enumerate(qs, 1):
        o = q.get("options", [])
        if (len(o) != 4 or len({s.strip().lower() for s in o}) != 4
                or q.get("correct") not in (0, 1, 2, 3) or not str(q.get("q", "")).strip()):
            raise ValueError("malformed question")
        idx = list(range(4))
        random.shuffle(idx)  # LLMs favour answer positions: reshuffle and remap
        out.append({"id": f"g{i}", "q": q["q"].strip(), "options": [o[j] for j in idx],
                    "correct": idx.index(q["correct"]),
                    "concept": q.get("concept") if q.get("concept") in G else "other",
                    "explanation": q.get("explanation", ""), "source": q.get("source", "")})
    return out


def generate_draft(material: str, title: str, n: int = 5) -> dict:
    G = load_graph()
    user = (f"N = {n}\nCONCEPT_IDS: {', '.join(G.nodes)}\n\nCOURSE MATERIAL:\n{material}")
    last = None
    for attempt in range(2):  # one retry on malformed output
        try:
            raw = chat(PROMPT, [{"role": "user", "content": user}], json=True, effort="low", max_tokens=8000)
            qs = _validate(raw["questions"][:n])
            break
        except (ValueError, KeyError, TypeError, LLMError) as e:
            last = e
            log_step("quiz_generate_invalid", output=str(e)[:200], attempt=attempt)
    else:
        raise ValueError(f"Quiz generation failed: {last}")
    qid = uuid.uuid4().hex[:6]
    db = _load()
    db["quizzes"][qid] = {"id": qid, "title": title, "status": "draft", "origin": "AI draft from material",
                          "questions": qs, "created": _now()}
    _save(db)
    log_step("tool.generate_quiz", input={"title": title, "n": n}, output={"quiz": qid, "questions": len(qs)})
    return db["quizzes"][qid]


def save_draft(quiz_id: str, questions: list[dict]) -> None:
    db = _load()
    db["quizzes"][quiz_id]["questions"] = questions
    _save(db)


def publish(quiz_id: str) -> None:
    db = _load()
    q = db["quizzes"][quiz_id]
    q["status"], q["published"] = "published", _now()
    _save(db)
    streaks.ensure_session(quiz_id, q["title"])
    log_step("professor.publish_quiz", input={"quiz": quiz_id}, output={"questions": len(q["questions"])})


def reset() -> None:
    if PATH.exists():
        PATH.unlink()
