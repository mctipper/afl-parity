from api.response_models import SeasonResults, GameResult
from algo.data_structures import AdjacencyGraph, HamiltonianCycle, DFSTraversalOutput
from typing import Set, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import threading

logger = logging.getLogger("main")


class DFS:
    season_results: SeasonResults
    adjacency_graph: AdjacencyGraph
    traversal_output: DFSTraversalOutput
    dfs_steps: int = 0
    full_paths_not_hamiltonian: int = 0
    hamiltonian_paths_found: int = 0

    def __init__(self, season_results: SeasonResults) -> None:
        self.season_results = season_results
        self.adjacency_graph = AdjacencyGraph()
        self.traversal_output = DFSTraversalOutput()

    def _build_adjacency_graph(self) -> None:
        self.adjacency_graph = AdjacencyGraph()
        for round_results in self.season_results:
            for game_result in round_results:
                if game_result.round > 9:  # temp
                    continue
                if game_result.winnerteamid:
                    self.adjacency_graph.add_child_to_parent(
                        game_result.winnerteamid, game_result.loserteamid
                    )

    def _validate_hamiltonian_cycle_possible(self) -> bool:
        parents_count = len(self.adjacency_graph.parents)
        children_count = len(self.adjacency_graph.children)
        nteams = self.season_results.nteams
        if nteams == parents_count and nteams == children_count:
            return True
        else:
            return False

    def _hamiltonian_cycle_permutation_logger(self) -> None:
        """helper function to log permutation progress, just helpful for eyeballing/ensuring compute is progressing"""
        thresholds: List[int] = [10, 100, 1000, 10000, 100000, 500000, 1000000]
        log_this: bool = False

        if self.dfs_steps > thresholds[-1]:
            # exit early once largest reached
            if self.dfs_steps % thresholds[-1] == 0:
                log_this = True
        else:
            for threshold in thresholds:
                if self.dfs_steps < threshold * 10:
                    if self.dfs_steps % threshold == 0:
                        log_this = True
                    break

        if log_this:
            logger.info(
                f"Thread: {threading.current_thread().name}\t| DFS Steps: {self.dfs_steps}\t| Hamiltonian Paths Found: {self.hamiltonian_paths_found}"
            )

    def _dfs(
        self,
        current_node: int,
        visited: Set[int],
        path: List[int],
        games: List[GameResult],
        start_node: int,
    ) -> None:
        self.dfs_steps += 1

        # propgress logging for sanity
        self._hamiltonian_cycle_permutation_logger()

        if len(visited) == len(self.adjacency_graph.adjacency_lists):
            adjacency_list = self.adjacency_graph.get_adjacency_graph(current_node)
            if adjacency_list and start_node in adjacency_list.children:
                game = next(
                    (
                        game
                        for game in self.season_results
                        for game in game.results
                        if game.winnerteamid == current_node
                        and game.loserteamid == start_node
                    ),
                    None,
                )
                if game:
                    games.append(game)
                cur_hamiltonian_cycle = HamiltonianCycle(
                    cycle=path.copy(), games=games.copy()
                )
                self.traversal_output.update_first_hamiltonian_cycle(
                    cur_hamiltonian_cycle
                )
                self.hamiltonian_paths_found += 1
            else:
                self.full_paths_not_hamiltonian += 1
            return

        adjacency_list = self.adjacency_graph.get_adjacency_graph(current_node)
        if not adjacency_list:
            return

        for neighbor in adjacency_list.children:
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                game = next(
                    (
                        game
                        for game in self.season_results
                        for game in game.results
                        if game.winnerteamid == current_node
                        and game.loserteamid == neighbor
                    ),
                    None,
                )
                if game:
                    games.append(game)
                self._dfs(neighbor, visited, path, games, start_node)
                path.pop()
                if game:
                    games.pop()
                visited.remove(neighbor)

    def _find_hamiltonian_cycles(self) -> None:
        with ThreadPoolExecutor() as executor:
            futures = []
            largest_adjacency_list_parent = (
                self.adjacency_graph.parents_with_most_children[0]
            )
            adjacency_list = self.adjacency_graph.get_adjacency_graph(
                largest_adjacency_list_parent
            )
            for child in adjacency_list.children:
                start_node = child
                visited = {largest_adjacency_list_parent, start_node}
                path = [largest_adjacency_list_parent, start_node]
                games = []
                game = next(
                    (
                        game
                        for game in self.season_results
                        for game in game.results
                        if game.winnerteamid == largest_adjacency_list_parent
                        and game.loserteamid == child
                    ),
                    None,
                )
                if game:
                    games.append(game)
                futures.append(
                    executor.submit(
                        self._dfs,
                        start_node,
                        visited,
                        path,
                        games,
                        largest_adjacency_list_parent,
                    )
                )

            for future in as_completed(futures):
                future.result()

    def process_season(self) -> None:
        """Sequentially (by round) build adjacency graph and traverse each as we go."""
        self._build_adjacency_graph()
        if self._validate_hamiltonian_cycle_possible():
            self.dfs_steps = 0
            self.full_paths_not_hamiltonian = 0
            self._find_hamiltonian_cycles()
            self.traversal_output.total_dfs_steps = self.dfs_steps
            self.traversal_output.total_full_paths_not_hamiltonian = (
                self.full_paths_not_hamiltonian
            )
            self.traversal_output.total_hamiltonian_paths = self.hamiltonian_paths_found
            logger.info(self.traversal_output)
            if self.traversal_output.first_hamiltonian_cycle:
                logger.info("Hamiltonian Cycle Found")
                logger.info(self.traversal_output.first_hamiltonian_cycle.cycle_names)
                logger.info(
                    self.traversal_output.first_hamiltonian_cycle.hamiltonian_cycle_game_details_pprint()
                )
            else:
                logger.info("Hamiltonian Cycle Not Found")
