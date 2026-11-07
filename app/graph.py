"""Course knowledge graph: load + validate data/graph.json, render it with pyvis.

Edge direction in the file: {"from": A, "to": B, "type": "requires"} means A requires B.
In networkx we keep that direction (A -> B), so B is a prerequisite of A and
`nx.descendants(G, A)` = all (transitive) prerequisites of A.
"""
from __future__ import annotations

import json
import textwrap
from functools import lru_cache
from pathlib import Path

import networkx as nx
from pyvis.network import Network

ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = ROOT / "data" / "graph.json"

COLORS = {"untested": "#9aa1a9", "weak": "#d64545", "shaky": "#d9a21b", "solid": "#1f9d55"}
PALE = {"weak": "#f4b4b4", "shaky": "#f3dc9b", "solid": "#a9dcbd"}  # same band, not confirmed yet


def band(score: int | None) -> str:
    if score is None:
        return "untested"
    if score <= 1:
        return "weak"
    if score == 2:
        return "shaky"
    return "solid"


@lru_cache(maxsize=1)
def load_graph() -> nx.DiGraph:
    data = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    G = nx.DiGraph()
    for n in data["nodes"]:
        if not n.get("source"):
            raise ValueError(f"graph node {n['id']} has no source")
        G.add_node(n["id"], **n)
    for e in data["edges"]:
        for end in (e["from"], e["to"]):
            if end not in G:
                raise ValueError(f"edge references unknown node {end}")
        G.add_edge(e["from"], e["to"], type=e.get("type", "requires"))
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("graph has a cycle in 'requires' edges")
    return G


def concept_name(cid: str) -> str:
    G = load_graph()
    return G.nodes[cid]["name"] if cid in G else cid


def graph_for_prompt() -> str:
    """Compact JSON the Examiner reads (no internal fields it doesn't need)."""
    G = load_graph()
    nodes = [{k: G.nodes[n][k] for k in ("id", "name", "description", "source", "misconceptions")}
             for n in G.nodes]
    edges = [{"concept": a, "requires": b} for a, b in G.edges]
    return json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False)


def render_html(mastery: dict | None = None, highlight: list[str] | None = None,
                height: int = 460) -> str:
    """mastery: {concept_id: {"score": int, "status": str}}; highlight: root-cause path."""
    G = load_graph()
    mastery = mastery or {}
    highlight = highlight or []
    net = Network(height=f"{height}px", width="100%", directed=True,
                  cdn_resources="in_line", bgcolor="#ffffff", font_color="#1b1d1f")
    for cid, attrs in G.nodes(data=True):
        m = mastery.get(cid, {})
        b = band(m.get("score"))
        tentative = m.get("status") == "needs_confirmation"
        title = f"{attrs['name']}\n{attrs['description']}\nSource: {attrs['source']}"
        if m:
            title += f"\nScore: {m.get('score')}/3 ({m.get('status', '')})"
        pale = tentative and b != "untested"
        net.add_node(
            cid, label=textwrap.fill(attrs["name"], 16), title=title, color=PALE[b] if pale else COLORS[b], shape="box",
            margin=8,
            borderWidth=4 if cid in highlight else 1,
            shapeProperties={"borderDashes": [6, 4] if tentative else False},
            font={"color": "#1b1d1f" if (b == "untested" or pale) else "#ffffff", "size": 15},
        )
    for a, b in G.edges:
        on_path = a in highlight and b in highlight
        # draw prerequisite -> concept ("leads to"), easier to read than "requires"
        net.add_edge(b, a, color="#1b1d1f" if on_path else "#b8bec6", width=3 if on_path else 1)
    net.set_options(json.dumps({
        "layout": {"hierarchical": {"enabled": True, "direction": "UD", "sortMethod": "directed",
                                     "levelSeparation": 80, "nodeSpacing": 135, "treeSpacing": 135}},
        "physics": {"enabled": False},
        "interaction": {"hover": True, "zoomView": True, "dragView": True},
        "edges": {"arrows": {"to": {"enabled": True, "scaleFactor": 0.6}},
                  "smooth": {"type": "cubicBezier", "forceDirection": "vertical"}},
    }))
    return net.generate_html(notebook=False)
