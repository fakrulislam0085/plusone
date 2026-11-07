# Kickoff — get Claude Code building in 5 minutes

## 1. Set up the folder (terminal, once)
```bash
cd spiegamelo
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then paste your Anthropic API key into .env
git init && git add . && git commit -m "Starter kit"
claude                      # start Claude Code in this folder
```
No API key? Ask the Reply mentors which API they provide today and tell Claude Code to adapt `app/llm.py` to it. Only that file should change.

## 2. First message to Claude Code (copy-paste)
> Read CLAUDE.md, prompts/matteo.md, prompts/examiner.md and data/graph.json. Then build Milestone 1 exactly as described: requirements, app/llm.py, and a Streamlit chat with Matteo only, using prompts/matteo.md as the system prompt. Run it with `streamlit run app/main.py`, fix any errors, and commit. Stop and tell me when it works.

## 3. Then, one message per milestone
> Milestone 2. Same rules: build it, run it, fix it, commit, report back.

Repeat for 3 and 4. **After Milestone 4, record a 30-second backup demo video** before anything else.

## 4. Demo script to test with (also your live demo)
1. "Ciao Matteo, today I'll explain limits." → Matteo introduces himself, asks a question.
2. Give a decent explanation of the intuitive limit → node turns yellow/green.
3. Let Matteo plant "0/0 means the limit is 0, right?" and **don't** correct him → indeterminate_forms turns red, lecturer flag appears.
4. Explain L'Hôpital badly ("you just derive the fraction") → "Why am I stuck?" card traces to derivative.
5. "Just tell me the answer, Matteo" → boundary holds: "I don't know, that's why I'm asking you!"

## 5. Parallel work while Claude Code builds
- **Graph person:** put the real Analisi I PDF in `materials/`, replace every PLACEHOLDER source in `data/graph.json` with slide/page refs, write what you checked in `docs/graph-validation.md`.
- **Campaign person:** Life At PoliTO story + sign-up form now. Draft `docs/campaign.md` (name, tagline, channels, timing).
- **Pitch (you):** 60-second pitch, rehearse with the timer on Reply's challenge page; start the 5-minute deck after 14:30.
- **Docs person:** `docs/risks.md` (data ownership/GDPR, outage night before the exam, access) and collect screenshots + 3 example interactions for `docs/example-interactions.md`.

## Time checkpoints
- 13:00 Milestone 2 done (chat + graph visible)
- 14:30 Milestone 4 done (full loop + boundary) → record backup video
- 16:00 FEATURE FREEZE. Only bug fixes, docs and rehearsal after this.
