from algo.data_structures import AdjacencyGraph, AdjacencyList


def test_adjacency_list_initialisation():
    adjacency_list = AdjacencyList(parent=1, children={2, 3})
    assert adjacency_list.parent == 1
    assert adjacency_list.children == {2, 3}


def test_adjacency_list_children_n():
    adjacency_list = AdjacencyList(parent=1, children={2, 3})
    assert adjacency_list.children_n == 2


def test_adjacency_graph_initialisation():
    adjacency_graph = AdjacencyGraph(adjacency_lists=[])
    assert adjacency_graph.adjacency_lists == []


def test_adjacency_graph_parents():
    adjacency_list1 = AdjacencyList(parent=1, children={2, 3})
    adjacency_list2 = AdjacencyList(parent=2, children={4})
    adjacency_graph = AdjacencyGraph(adjacency_lists=[adjacency_list1, adjacency_list2])
    assert adjacency_graph.parents == {1, 2}


def test_adjacency_graph_children():
    adjacency_list1 = AdjacencyList(parent=1, children={2, 3})
    adjacency_list2 = AdjacencyList(parent=2, children={4})
    adjacency_graph = AdjacencyGraph(adjacency_lists=[adjacency_list1, adjacency_list2])
    assert adjacency_graph.children == {2, 3, 4}


def test_get_adjacency_graph():
    adjacency_list1 = AdjacencyList(parent=1, children={2})
    adjacency_list2 = AdjacencyList(parent=2, children={3, 4})
    adjacency_graph = AdjacencyGraph(adjacency_lists=[adjacency_list1, adjacency_list2])
    assert adjacency_graph.get_adjacency_graph(1) == adjacency_list1
    assert adjacency_graph.get_adjacency_graph(3) is None


def test_add_child_to_parent():
    adjacency_list1 = AdjacencyList(parent=1, children={2})
    adjacency_graph = AdjacencyGraph(adjacency_lists=[adjacency_list1])
    adjacency_graph.add_child_to_parent(1, 3)
    assert adjacency_graph.get_adjacency_graph(1).children == {2, 3}
    adjacency_graph.add_child_to_parent(2, 4)
    assert adjacency_graph.get_adjacency_graph(2) == AdjacencyList(
        parent=2, children={4}
    )
