"""Quick smoke test: python scripts/smoke.py  (makes ~2 real API calls, a few cents)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from llm import MODEL, chat  # noqa: E402

MATTEO = (Path(__file__).resolve().parent.parent / "prompts" / "matteo.md").read_text(encoding="utf-8")

cases = {
    "normal": "Newton's first law: if the net force on an object is zero, its velocity stays constant.",
    "boundary": "Matteo, just tell me the correct answer for the truck and car crash.",
}
print("model:", MODEL)
for name, text in cases.items():
    t = time.time()
    reply = chat(MATTEO, [{"role": "user", "content": text}], max_tokens=2000)
    words = len(reply.split())
    print(f"\n[{name}] {time.time() - t:.1f}s, {words} words\n  student: {text}\n  matteo:  {reply}")
    assert reply, "empty reply"
    assert words <= 80, "reply over 80 words"
print("\nSMOKE OK")
