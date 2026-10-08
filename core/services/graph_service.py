import json
import os
from typing import Dict, List, Set, Optional, Any
from core.schemas.skill_graph import SkillGraph, SkillNode

class GraphService:
    """
    Manages competency graphs, topological dependency resolution,
    prerequisite tracing, and visual DOT graph generation.
    """
    def __init__(self, data_dir: str = "data/skills"):
        self.data_dir = data_dir
        self.graphs: Dict[str, SkillGraph] = {}
        self._load_graphs()

    def _load_graphs(self):
        if not os.path.exists(self.data_dir):
            return
        # Load skill graph files
        file_to_graph: Dict[str, SkillGraph] = {}
        for file_name in os.listdir(self.data_dir):
            if file_name.endswith(".json"):
                path = os.path.join(self.data_dir, file_name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        graph = SkillGraph(**data)
                        self.graphs[graph.goal_id] = graph
                        file_to_graph[file_name] = graph
                except Exception as e:
                    print(f"Error loading skill graph {file_name}: {e}")

        # Map goal aliases from goals.json (e.g. goal_data_scientist -> ml_engineer.json)
        goals_file = os.path.join(os.path.dirname(self.data_dir), "goals", "goals.json")
        if os.path.exists(goals_file):
            try:
                with open(goals_file, "r", encoding="utf-8") as f:
                    goals_data = json.load(f)
                    for g in goals_data:
                        gid = g.get("goal_id")
                        graph_file = g.get("skill_graph_file")
                        if gid and graph_file in file_to_graph:
                            self.graphs[gid] = file_to_graph[graph_file]
            except Exception as e:
                print(f"Error loading goals catalog: {e}")

    def get_graph(self, goal_id: str) -> Optional[SkillGraph]:
        return self.graphs.get(goal_id)

    def get_all_prerequisites(self, goal_id: str, skill_id: str) -> Set[str]:
        """Recursively retrieve all transitive prerequisite skill IDs for a given skill."""
        graph = self.get_graph(goal_id)
        if not graph or skill_id not in graph.nodes:
            return set()
        
        prereqs = set()
        stack = list(graph.nodes[skill_id].prerequisite_skill_ids)
        while stack:
            curr = stack.pop()
            if curr not in prereqs:
                prereqs.add(curr)
                if curr in graph.nodes:
                    stack.extend(graph.nodes[curr].prerequisite_skill_ids)
        return prereqs

    def topological_sort(self, goal_id: str) -> List[str]:
        """
        Return a valid topological ordering of skill IDs respecting prerequisites.
        Uses Kahn's algorithm.
        """
        graph = self.get_graph(goal_id)
        if not graph:
            return []

        in_degree = {sid: 0 for sid in graph.nodes}
        adj: Dict[str, List[str]] = {sid: [] for sid in graph.nodes}

        for sid, node in graph.nodes.items():
            for prereq in node.prerequisite_skill_ids:
                if prereq in graph.nodes:
                    adj[prereq].append(sid)
                    in_degree[sid] += 1

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        sorted_nodes = []

        while queue:
            curr = queue.pop(0)
            sorted_nodes.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_nodes) != len(graph.nodes):
            # Fallback if cycle detected
            return list(graph.nodes.keys())
        return sorted_nodes

    def generate_dot_graph(self, goal_id: str, knowledge_states: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates Graphviz DOT syntax for rendering interactive DAG in Streamlit.
        Colors nodes based on demonstrated proficiency status (adequate, weak, unknown).
        """
        graph = self.get_graph(goal_id)
        if not graph:
            return "digraph G { empty [label=\"No Graph Loaded\"]; }"

        dot_lines = [
            "digraph SkillGraph {",
            "  graph [rankdir=TB, bgcolor=\"transparent\", fontname=\"Helvetica\"];",
            "  node [shape=box, style=\"rounded,filled\", fontname=\"Helvetica\", fontsize=10, margin=\"0.2,0.15\", penwidth=1.5];",
            "  edge [color=\"#94a3b8\", penwidth=1.5, arrowsize=0.8];"
        ]

        # Category colors
        status_colors = {
            "adequate": ("#dcfce7", "#166534", "#22c55e"),      # green bg, dark text, green border
            "needs_improvement": ("#fef9c3", "#854d0e", "#eab308"), # yellow
            "weak": ("#fee2e2", "#991b1b", "#ef4444"),           # red
            "unknown": ("#f1f5f9", "#334155", "#cbd5e1")         # gray
        }

        for sid, node in graph.nodes.items():
            status = "unknown"
            score_text = "Not Assessed"
            if knowledge_states and sid in knowledge_states:
                ks = knowledge_states[sid]
                status = getattr(ks, "status", "unknown")
                score_val = getattr(ks, "demonstrated_score", 0.0)
                score_text = f"Score: {int(score_val * 100)}%"

            bg, text_color, border_color = status_colors.get(status, status_colors["unknown"])
            label = f"{node.name}\\n[{node.category}]\\n{score_text}"
            dot_lines.append(
                f'  "{sid}" [label="{label}", fillcolor="{bg}", fontcolor="{text_color}", color="{border_color}"];'
            )

        for sid, node in graph.nodes.items():
            for prereq in node.prerequisite_skill_ids:
                if prereq in graph.nodes:
                    dot_lines.append(f'  "{prereq}" -> "{sid}";')

        dot_lines.append("}")
        return "\n".join(dot_lines)
