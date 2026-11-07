# Risks and how Matteo handles them

| Risk | Who it hurts | Mitigation (built) | Still open |
|---|---|---|---|
| **The AI gives the answer** (thinks for the student) | Learning | Matteo's role + code guardrail + regenerate/fallback; tested 5/5 live boundary turns and 13/13 offline tutor drafts blocked (incl. the numeric-result leak an audit found) | Regex guardrails catch tested patterns only: indirect paraphrases can still slip through, so we don't claim a guarantee |
| **Wrong diagnosis** (a short answer is read as a misconception) | Students' trust | Weak spots stay *hypotheses* until confirmed twice; nothing traced without evidence; the professor approves/rejects every flag | Needs a real trial to measure the error rate |
| **The AI dominates the group** (students talk to it, not to each other) | Peer learning | Matteo asks named peers to react; he can't be the answer source | Turn-taking and silence policies are not built yet |
| **Student data and privacy** (who owns it?) | Students | Flags carry no names and no quotes; memory is local JSON; only concept-level patterns reach the professor | Real deployment needs GDPR review, consent, retention limits and university-hosted data |
| **Tool down the night before the exam** | Students | Safe canned fallback if the API fails (tested); `llm.py` swaps to another provider in one file | No offline mode |
| **Unequal access** (no laptop, weak connection) | Students left out | Text-only, light web page, works in a phone browser; Italian and English | Not tested on slow networks |
| **Cost** | University | About $0.03–0.05 per student message with Opus; Sonnet halves it | Needs a per-course budget |
| **Over-reliance on AI judgement** by professors | Assessment fairness | Counts, not grades; explicit uncertainty on every flag; formative only, never for marks | Policy decision for the university |
| **Material is not official** | Credibility | Labelled everywhere (OpenStax-aligned demo pack, CC BY 4.0) | Swap in real course slides with permission |
| **Synthetic data mistaken for results** | Credibility | The class heatmap and group names are labelled synthetic; we claim no learning gains | |
