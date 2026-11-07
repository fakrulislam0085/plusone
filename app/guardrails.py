"""Guardrail IN CODE on Matteo's draft: a prompt can be talked around, this check cannot.

Matteo must never act as the tutor: no answers, no law statements, no worked solutions.
"""
from __future__ import annotations

import re

MAX_WORDS = 80

BLOCKLIST = [
    (r"\bthe (correct |right |real )?answer is\b", "states the answer"),
    (r"\bthe correct answer\b", "states the answer"),
    (r"\bnewton'?s (first|second|third|1st|2nd|3rd) law (states|says|tells us)\b", "states a law"),
    (r"\bthe definition (of [\w\s']+ )?is\b", "gives a definition"),
    (r"\b(the )?net force (is|equals|=)\s*-?\d", "computes the result"),
    (r"\byou should\b", "instructs the student"),
    (r"\blet me explain\b", "switches to tutor mode"),
    (r"\bhere'?s (how|why|the (answer|solution|explanation))\b", "switches to tutor mode"),
    (r"\bin summary\b", "summarises like a tutor"),
    (r"\bstep \d\b", "gives a step-by-step solution"),
    (r"\bthe solution (is|would be)\b", "gives the solution"),
    # audit fix: Matteo must not state OR confirm a numeric result ("that's why it's 3 m/s²")
    (r"\b(is|it's|it is|equals|=|gives you|comes out (to|as))\s*-?\d+(\.\d+)?\s*(m/s²|m/s\^2|m/s|n|kg)\b",
     "states or confirms a numeric result"),
]

STRICT_REMINDER = (
    "\n\n## GUARDRAIL REMINDER (your previous draft was rejected)\n"
    "Your last draft sounded like a tutor ({reason}). You are Matteo, the confused learner. "
    "Do NOT state laws, definitions, answers or calculations. Reply with ONE short confused "
    "question (max 2 sentences, under 50 words) that makes the students explain."
)


def check(draft: str) -> tuple[bool, str]:
    """Return (ok, reason). reason is '' when ok."""
    text = draft.strip()
    if not text:
        return False, "empty reply"
    if len(text.split()) > MAX_WORDS:
        return False, f"too long ({len(text.split())} words > {MAX_WORDS})"
    low = text.lower()
    for pattern, reason in BLOCKLIST:
        if re.search(pattern, low):
            return False, reason
    # worked calculation: two or more "= number" steps, or unit arithmetic like "10 N - 4 N"
    if len(re.findall(r"=\s*-?\d", low)) >= 2 or re.search(
            r"\d+(\.\d+)?\s*(n|kg|m/s²|m/s\^2)\s*[-+×x*/÷]\s*\d", low):
        return False, "works out a calculation"
    return True, ""


_EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF⭐‍️]")


def strip_emoji(text: str) -> str:
    """The UI uses Lucide icons only; remove any emoji the model still writes."""
    text = re.sub(r"[ \t]{2,}", " ", _EMOJI.sub("", text))
    return re.sub(r"[ \t]+([,.!?;:])", r"\1", text).strip()


def canned_question(concept_name: str | None, peer: str | None = None) -> str:
    if peer:
        return f"Hmm, I'm lost again. {peer}, how would you explain this part to me?"
    topic = concept_name or "this"
    return f"Wait, I'm still confused about {topic}. Can you explain it with a simple example?"
