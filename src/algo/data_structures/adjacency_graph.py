from pydantic import BaseModel
from typing import Set, List, Dict


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
    def parents_with_one_child(self) -> Set[int]:
        if not self.adjacency_lists:
            return set()
        return set(
            adjacency_list.parent
            for adjacency_list in self.adjacency_lists
            if adjacency_list.children_n == 1
        )

    @property
    def children_with_one_parent(self) -> Set[int]:
        child_count: Dict[int, int] = {}

        for adjacency_list in self.adjacency_lists:
            for child in adjacency_list.children:
                child_count[child] = child_count.get(child, 0) + 1

        if not child_count:
            return set()

        return set(child for child, count in child_count.items() if count == 1)

    def get_parents_of_child(self, target_child: int) -> Set[int]:
        parents: set[int] = []

        for adjacency_list in self.adjacency_lists:
            for child in adjacency_list.children:
                if child == target_child:
                    parents.add(adjacency_list.parent)

        return parents

    def get_children_for_parent(self, target_parent: int) -> Set[int]:
        adjacency_list = self.get_adjacency_graph(target_parent)
        if adjacency_list:
            return adjacency_list.children
        return Set()

    def get_adjacency_graph(self, parent: int) -> AdjacencyList:
        for adjacency_list in self.adjacency_lists:
            if adjacency_list.parent == parent:
                return adjacency_list
        raise ValueError(f"{parent} not found in adjacency lists")

    def add_child_to_parent(self, parent: int, child: int) -> None:
        try:
            parents_adjacency_list = self.get_adjacency_graph(parent)
            parents_adjacency_list.children.add(child)
        except ValueError:
            self.adjacency_lists.append(AdjacencyList(parent=parent, children={child}))
