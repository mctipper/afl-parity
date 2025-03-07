from pydantic import BaseModel
from typing import Set, List, Optional


class AdjacencyList(BaseModel):
    parent: int
    children: Set[int] = set()

    @property
    def children_n(self) -> int:
        return len(self.children)


class AdjacencyGraph(BaseModel):
    adjacency_lists: List[AdjacencyList] = []

    @property
    def parents(self) -> Set[int]:
        """all unique parents"""
        return {adjacency_list.parent for adjacency_list in self.adjacency_lists}

    @property
    def children(self) -> Set[int]:
        """all unique children"""
        return {
            child
            for adjacency_list in self.adjacency_lists
            for child in adjacency_list.children
        }

    @property
    def parents_with_least_children(self) -> List[int]:
        if not self.adjacency_lists:
            return []
        min_children_n = min(
            adjacency_list.children_n for adjacency_list in self.adjacency_lists
        )
        return [
            adjacency_list.parent
            for adjacency_list in self.adjacency_lists
            if adjacency_list.children_n == min_children_n
        ]

    @property
    def parents_with_most_children(self) -> List[int]:
        if not self.adjacency_lists:
            return []
        max_children_n = max(
            adjacency_list.children_n for adjacency_list in self.adjacency_lists
        )
        return [
            adjacency_list.parent
            for adjacency_list in self.adjacency_lists
            if adjacency_list.children_n == max_children_n
        ]

    def _get_adjacency_graph(self, parent: int) -> Optional[AdjacencyList]:
        for adjacency_list in self.adjacency_lists:
            if adjacency_list.parent == parent:
                return adjacency_list
        return None

    def add_child_to_parent(self, parent: int, child: int) -> None:
        parents_adjacency_list = self._get_adjacency_graph(parent)
        if not parents_adjacency_list:
            self.adjacency_lists.append(AdjacencyList(parent=parent, children={child}))
        else:
            parents_adjacency_list.children.add(child)
