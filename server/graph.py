from collections import defaultdict
from server.schemas import Edge
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

def build_adjacency_list(edges: list[Edge]) -> dict[str, list[str]]:
    adj = defaultdict(list)

    vertices = {
        vertex 
        for edge in edges
        for vertex in (edge.from_, edge.to)
    }

    for vertex in vertices:
        adj[vertex] = [edge.to for edge in edges if edge.from_ == vertex]

    return adj

def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    visited = set()
    visiting = set()
    result = []

    def dfs(node):
        if node in visiting:
            raise ValueError("Cycle detected")

        if node in visited:
            return

        visiting.add(node)

        for neighbor in graph.get(node, []):
            dfs(neighbor)

        visiting.remove(node)
        visited.add(node)

        result.append(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    result.reverse()
    return result
