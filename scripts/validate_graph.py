"""Automatic checks on data/graph.json vs the material pack (no API calls).

  .venv\\Scripts\\python scripts/validate_graph.py
"""
import json
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from graph import load_graph  # noqa: E402

PACK = ROOT / "materials" / "physics1_newton"
manifest = json.loads((PACK / "course_manifest.json").read_text(encoding="utf-8"))
quiz = json.loads((PACK / "quiz_student.json").read_text(encoding="utf-8"))["items"]
key = {i["id"]: i for i in json.loads((PACK / "quiz_instructor_key.json").read_text(encoding="utf-8"))["items"]}
ref_ids = {r["id"].replace("OS-", "§") for r in manifest["references"]}

G = load_graph()  # already enforces: every node has a source, edges reference real nodes, no cycles
checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {name}" + (f" | {detail}" if detail else ""))


check("graph loads, every node has a source, DAG", True, f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
used = {m for n in G.nodes for m in G.nodes[n]["misconceptions"]}
check("every misconception ID exists in the pack manifest", used <= set(manifest["misconceptions"]),
      str(used - set(manifest["misconceptions"])) or "")
check("every pack misconception is attached to a concept", set(manifest["misconceptions"]) <= used,
      str(set(manifest["misconceptions"]) - used) or "")
cited = set()
for n in G.nodes:
    for part in G.nodes[n]["source"].replace(",", " ").split():
        if part.startswith("§"):
            cited.add(part.rstrip(";"))
check("every OpenStax section cited is in the pack's reference list", cited <= ref_ids, str(cited - ref_ids) or "")
los = {lo["id"] for lo in manifest["learning_outcomes"]}
check("every learning outcome id on nodes exists", all(set(G.nodes[n]["lo"]) <= los for n in G.nodes))
quiz_ids = {q["id"] for q in quiz}
check("every quiz item linked to a node exists", all(set(G.nodes[n]["quiz"]) <= quiz_ids for n in G.nodes))
# cross-check: each MCQ's distractor misconceptions should belong to a node that links that quiz item
mismatch = []
for q in quiz:
    for mid in set(key.get(q["id"], {}).get("misconception_by_distractor", {}).values()):
        if not any(q["id"] in G.nodes[n]["quiz"] and mid in G.nodes[n]["misconceptions"] for n in G.nodes):
            mismatch.append(f"{q['id']}:{mid}")
check("quiz distractor misconceptions sit on a node linked to that item", not mismatch,
      ", ".join(mismatch) if mismatch else "")
check("prerequisite roots exist (concepts with no prerequisites)",
      any(G.out_degree(n) == 0 for n in G.nodes), ", ".join(n for n in G.nodes if G.out_degree(n) == 0))
check("longest prerequisite chain is short enough to explain", nx.dag_longest_path_length(G) <= 4,
      " -> ".join(nx.dag_longest_path(G)))
print("\nGRAPH VALIDATION:", "ALL PASS" if all(checks) else f"{checks.count(False)} FAIL")
sys.exit(0 if all(checks) else 1)
