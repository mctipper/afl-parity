from api.response_models import SeasonResults, GameResult
from algo.data_structures import AdjacencyGraph, HamiltonianCycle, FirstCycle
from typing import Set, List, Dict
import logging

logger = logging.getLogger("main")


class DFS:
    season_results: SeasonResults
    adjacency_graph: AdjacencyGraph
    hamiltonian_cycles: List[HamiltonianCycle]
    first_cycle: FirstCycle
    stats_by_round: Dict[int, Dict[str, int]]

    def __init__(self, season_results: SeasonResults) -> None:
        self.season_results = season_results
        self.adjacency_graph = AdjacencyGraph()
        self.hamiltonian_cycles = []
        self.first_cycle = FirstCycle()
        self.stats_by_round = {}

    def _build_adjacency_graph(self, up_to_round: int) -> None:
        self.adjacency_graph = AdjacencyGraph()

        for round_idx, round_results in enumerate(self.season_results):
            if round_idx <= up_to_round:
                for game_result in round_results:
                    if game_result.winnerteamid:
                        self.adjacency_graph.add_child_to_parent(
                            game_result.wteamid, game_result.lteamid
                        )

    def validate_hamiltonian_cycle_possible(self) -> bool:
        parents_count = len(self.adjacency_graph.parents)
        children_count = len(self.adjacency_graph.children)
        nteams = self.season_results.nteams

        if nteams == parents_count and nteams == children_count:
            return True
        else:
            return False

    def find_hamiltonian_cycles(self) -> bool:
        def dfs(
            current_node: int,
            visited: Set[int],
            path: List[int],
            games: List[GameResult],
            start_node: int,
        ) -> bool:
            self.dfs_steps += 1
            if len(visited) == len(self.adjacency_graph.adjacency_lists):
                adjacency_list = self.adjacency_graph._get_adjacency_graph(current_node)
                if adjacency_list and start_node in adjacency_list.children:
                    game = next(
                        (
                            game
                            for game in self.season_results
                            for game in game.results
                            if game.wteamid == current_node
                            and game.lteamid == start_node
                        ),
                        None,
                    )
                    if game:
                        games.append(game)
                    hamiltonian_cycle = HamiltonianCycle(
                        cycle=path.copy(), games=games.copy()
                    )
                    self.hamiltonian_cycles.append(hamiltonian_cycle)
                    self.first_cycle.update(hamiltonian_cycle)
                    return True
                else:
                    self.full_paths_not_hamiltonian += 1
                return False

            adjacency_list = self.adjacency_graph._get_adjacency_graph(current_node)
            if not adjacency_list:
                return False

            for neighbor in adjacency_list.children:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    game = next(
                        (
                            game
                            for game in self.season_results
                            for game in game.results
                            if game.wteamid == current_node and game.lteamid == neighbor
                        ),
                        None,
                    )
                    if game:
                        games.append(game)
                    if dfs(neighbor, visited, path, games, start_node):
                        return True
                    path.pop()
                    if game:
                        games.pop()
                    visited.remove(neighbor)
            return False

        for adjacency_list in self.adjacency_graph.adjacency_lists:
            start_node = adjacency_list.parent
            visited = {start_node}
            path = [start_node]
            if dfs(start_node, visited, path, [], start_node):
                return True
        return False

    def process_season(self) -> None:
        for cur_round in self.season_results.rounds_list:
            self._build_adjacency_graph(cur_round)
            if self.validate_hamiltonian_cycle_possible():
                self.hamiltonian_cycles = []
                self.dfs_steps = 0
                self.full_paths_not_hamiltonian = 0
                found: bool = self.find_hamiltonian_cycles()
                self.stats_by_round[cur_round] = {
                    "dfs_steps": self.dfs_steps,
                    "full_paths_not_hamiltonian": self.full_paths_not_hamiltonian,
                }
                print(f"After round {cur_round}:")
                print(f"Number of DFS steps: {self.dfs_steps}")
                print(
                    f"Number of full-length paths not Hamiltonian cycles: {self.full_paths_not_hamiltonian}"
                )
                if found:
                    print(
                        f"Number of Hamiltonian cycles found: {len(self.hamiltonian_cycles)}"
                    )
                    self.print_first_cycle()
                    self.print_total_stats()
                    break
            else:
                print(f"Hamiltonian cycle not possible after Round {cur_round}")

    def print_stats_by_round(self) -> None:
        for round_number, stats in self.stats_by_round.items():
            print(
                f"Round {round_number}: DFS Steps: {stats['dfs_steps']}, Full-Length Paths Not Hamiltonian: {stats['full_paths_not_hamiltonian']}"
            )

    def print_total_stats(self) -> None:
        total_dfs_steps = sum(
            stats["dfs_steps"] for stats in self.stats_by_round.values()
        )
        total_full_paths_not_hamiltonian = sum(
            stats["full_paths_not_hamiltonian"]
            for stats in self.stats_by_round.values()
        )
        print(
            f"Total DFS Steps: {total_dfs_steps}, Total Full-Length Paths Not Hamiltonian: {total_full_paths_not_hamiltonian}"
        )

    def print_hamiltonian_cycles(self) -> None:
        for cycle in self.hamiltonian_cycles:
            print(cycle)

    def print_first_cycle(self) -> None:
        if self.hamiltonian_cycles:
            if self.first_cycle.first_hamiltonian_cycle:
                print(
                    f"First Hamiltonian Cycle: {self.first_cycle.first_hamiltonian_cycle.cycle}"
                )
        else:
            print("No Hamiltonian cycles found.")
