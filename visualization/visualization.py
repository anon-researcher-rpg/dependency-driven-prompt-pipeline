from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
import networkx as nx

from core.config import ROOT_DIRECTORY


RELATION_COLORS = {
    "Przyjaźń": "green",
    "Sojusz": "blue",
    "Rywalizacja": "orange",
    "Konflikt": "red",
    "Wrogość": "black",
    "Nienawiść": "darkred",
    "Zemsta": "purple",
    "Współpraca": "cyan",
    "Odmienne cele": "gray",
    "neutral": "gray",
}

RELATION_TRANSLATIONS = {
    "Friendship": "Przyjaźń",
    "Alliance": "Sojusz",
    "Rivalry": "Rywalizacja",
    "Conflict": "Konflikt",
    "Hostility": "Wrogość",
    "Hatred": "Nienawiść",
    "Revenge": "Zemsta",
    "Cooperation": "Współpraca",
    "Different goals": "Odmienne cele",
    "Neutral": "neutral",
    "neutral": "neutral",
}


def normalize_relation_type(rel_type: str | None) -> str:
    if not rel_type:
        return "neutral"
    rel_type = rel_type.strip()
    return RELATION_TRANSLATIONS.get(rel_type, rel_type)


def load_relations(relations_file: Path) -> list[dict[str, Any]]:
    if not relations_file.exists():
        print(f"File not found: {relations_file}")
        return []
    try:
        return json.loads(relations_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Failed to read relations file: {relations_file}. Error: {e}")
        return []


def visualize(relations: list[dict[str, Any]], output_file: Path, show: bool = True) -> Optional[Path]:
    if not relations:
        print("Relations not loaded")
        return None

    G = nx.DiGraph()

    for rel in relations:
        npc_from = rel.get("from")
        npc_to = rel.get("to")
        relation_type = normalize_relation_type(rel.get("type"))

        if not npc_from or not npc_to:
            continue

        G.add_node(npc_from)
        G.add_node(npc_to)
        G.add_edge(npc_from, npc_to, type=relation_type)

    if G.number_of_edges() == 0:
        print("No valid edges to draw.")
        return None

    plt.figure(figsize=(18, 12))
    pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42)

    nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=2000)

    for rel_type, color in RELATION_COLORS.items():
        edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("type") == rel_type]
        if edges:
            nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color, width=3, arrowsize=25)

    nx.draw_networkx_labels(
        G,
        pos,
        font_size=12,
        font_family="sans-serif",
        bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.3"),
    )

    for rel_type, color in RELATION_COLORS.items():
        plt.plot([], [], color=color, label=rel_type, linewidth=3)

    plt.legend(title="Relation type", loc="upper left", fontsize=12)
    plt.title("NPC relations graph", fontsize=16)
    plt.axis("off")
    plt.tight_layout()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=300)
    print(f"Graph saved inside {output_file}")

    if show:
        plt.show(block=True)

    plt.close()
    return output_file


def run(out_dir: Optional[str | Path] = None, lang: Optional[str] = None) -> Optional[Path]:
    """
    Pipeline entrypoint. Reads <out_dir>/npcs/relations.json and saves graph PNG.
    lang is unused but kept for API consistency with other stages.
    """
    out_path = Path(out_dir) if out_dir is not None else Path(ROOT_DIRECTORY)
    out_path.mkdir(parents=True, exist_ok=True)

    relations_file = out_path / "npcs" / "relations.json"
    output_file = out_path / "npc_relations_graph.png"

    relations = load_relations(relations_file)
    if not relations:
        print(f"No data found inside {relations_file}")
        return None

    print(f"Loaded {len(relations)} relations. Creating graph...")
    return visualize(relations, output_file, show=True)


def main() -> None:
    run()


if __name__ == "__main__":
    main()