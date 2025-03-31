from pydantic import BaseModel
from typing import Set, List, Optional, Dict


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
    def parents_with_one_child(self) -> Optional[List[int]]:
        if not self.adjacency_lists:
            return []
        return [
            adjacency_list.parent
            for adjacency_list in self.adjacency_lists
            if adjacency_list.children_n == 1
        ]

    @property
    def children_with_one_parent(self) -> Optional[List[int]]:
        """
        Finds the children with the least number of parents.
        """
        # Create a dictionary to count how many parents each child has
        child_count: Dict[int, int] = {}

        # Iterate over all adjacency lists
        for adjacency_list in self.adjacency_lists:
            for child in adjacency_list.children:
                # increment the count for each child
                child_count[child] = child_count.get(child, 0) + 1

        if not child_count:
            return []

        # Find all children with the minimum parent count
        return [child for child, count in child_count.items() if count == 1]

    def get_parents_of_child(self, target_child: int) -> List[int]:
        parents: List[int] = []

        for adjacency_list in self.adjacency_lists:
            for child in adjacency_list.children:
                if child == target_child:
                    parents.append(adjacency_list.parent)

        return parents

    def get_children_for_parent(self, target_parent: int) -> set[int]:
        adjacency_list = self.get_adjacency_graph(target_parent)
        if adjacency_list:
            return adjacency_list.children
        return Set()

    def get_adjacency_graph(self, parent: int) -> Optional[AdjacencyList]:
        for adjacency_list in self.adjacency_lists:
            if adjacency_list.parent == parent:
                return adjacency_list
        return None

    def add_child_to_parent(self, parent: int, child: int) -> None:
        parents_adjacency_list = self.get_adjacency_graph(parent)
        if not parents_adjacency_list:
            self.adjacency_lists.append(AdjacencyList(parent=parent, children={child}))
        else:
            parents_adjacency_list.children.add(child)
