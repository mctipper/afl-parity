from models import SeasonResults, GameResult
from algo.data_structures import AdjacencyGraph, HamiltonianCycle, DFSTraversalOutput
from typing import Set, List
import json
from pathlib import Path
import logging


class DFS:
    season_results: SeasonResults
    adjacency_graph: AdjacencyGraph
    traversal_output: DFSTraversalOutput
    dfs_steps: int = 0
    full_paths_not_hamiltonian: int = 0
    hamiltonian_cycles_found: int = 0
    output_file_debug: bool = False

    def __init__(
        self, season_results: SeasonResults, output_file_debug: bool = False
    ) -> None:
        self.season_results = season_results
        self.adjacency_graph = AdjacencyGraph()
        self.traversal_output = DFSTraversalOutput()
        self.output_file_debug = output_file_debug
        self.logger = logging.getLogger(f"{self.season_results.season}_main")

    def _build_adjacency_graph(self, up_to_round: int) -> None:
        """dynmically build adjacency graph up to the supplied round"""
        self.adjacency_graph = AdjacencyGraph()
        for round_results in self.season_results:
            for game_result in round_results:
                if game_result.round <= up_to_round:
                    if game_result.winnerteamid and game_result.loserteamid:
                        self.adjacency_graph.add_child_to_parent(
                            game_result.winnerteamid, game_result.loserteamid
                        )

    def _save_output_to_file(self) -> None:
        """save the traversal output to a json file in the output directory"""
        try:
            project_root: Path = Path(__file__).parents[2]  # yueck

            output_dir: Path = project_root / "output" / str(self.season_results.season)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file: Path = output_dir / "dfs_traversal_output.json"

            with open(output_file, "w") as f:
                json.dump(
                    json.loads(self.traversal_output.model_dump_json()), f, indent=2
                )

            self.logger.info(f"Traversal results stored in {output_file}")

        except Exception as e:
            self.logger.error(f"Failed to save output: {e}")

    def _hamiltonian_cycle_permutation_logger(self, force: bool = False) -> None:
        """helper function to log permutation progress, just helpful for eyeballing/ensuring compute is progressing"""
        thresholds = [10_000, 100_000, 500_000, 1_000_000]

        log_me: bool = False
        if self.dfs_steps > thresholds[-1]:
            if self.dfs_steps % thresholds[-1] == 0:
                log_me = True
        else:
            for threshold in thresholds:
                if self.dfs_steps < threshold * 10:
                    if self.dfs_steps % threshold == 0:
                        log_me = True
                    break
        if log_me or force:
            self.logger.info(
                f"Season: {self.season_results.season}\t | DFS Steps: {self.dfs_steps}\t| Hamiltonian Cycles Found: {self.hamiltonian_cycles_found}"
            )

    def _validate_hamiltonian_cycle_possible(self) -> bool:
        """helper method to first check all teams have either won or lost at least one game"""
        parents_count = len(self.adjacency_graph.parents)
        children_count = len(self.adjacency_graph.children)
        nteams = self.season_results.nteams
        if nteams == parents_count and nteams == children_count:
            return True
        else:
            return False

    def _dfs(
        self,
        cur_winner: int,
        visited: Set[int],
        path: List[int],
        games: List[GameResult],
        first_parent_in_path: int,
    ) -> None:
        """recursive method to perform DFS. Exits early upon successfull hamiltonian cycle being found"""
        self.dfs_steps += 1
        self._hamiltonian_cycle_permutation_logger()

        # gets the losers for the current winner
        adjacency_list = self.adjacency_graph.get_adjacency_graph(cur_winner)
        if not adjacency_list:
            # this should never occur...
            return

        # once all teams have been visited, can inspect for hamiltonian cycle
        if len(visited) == self.season_results.nteams:
            adjacency_list = self.adjacency_graph.get_adjacency_graph(cur_winner)
            if adjacency_list and first_parent_in_path in adjacency_list.children:
                self.logger.debug("Found Hamiltonian Cycle")
                game = self.season_results.get_first_game_result(
                    cur_winner, first_parent_in_path
                )
                if game:
                    games.append(game)
                cur_hamiltonian_cycle = HamiltonianCycle(
                    cycle=path.copy(), games=games.copy()
                )
                if self.traversal_output.first_hamiltonian_cycle:
                    self.logger.debug(
                        f"Cur: {cur_hamiltonian_cycle.max_date} Current First: {self.traversal_output.first_hamiltonian_cycle.max_date}"
                    )
                # determine if update call need to be made to first_cycle
                if (
                    not self.traversal_output.first_hamiltonian_cycle
                    or cur_hamiltonian_cycle.max_date
                    < self.traversal_output.first_hamiltonian_cycle.max_date
                ):
                    logger_msg: str
                    if self.traversal_output.first_hamiltonian_cycle:
                        self.logger.debug(
                            f"Current: {self.traversal_output.first_hamiltonian_cycle.max_date} | New: {cur_hamiltonian_cycle.max_date}"
                        )
                        logger_msg = "Updated Hamiltonian Cycle"
                    else:
                        logger_msg = "First Hamiltonian Cycle"
                    # this method double-validates if applicable to update, as a safety
                    self.traversal_output.update_first_hamiltonian_cycle(
                        cur_hamiltonian_cycle
                    )
                    self.logger.info(
                        f"{logger_msg} | {self.traversal_output.first_hamiltonian_cycle.max_date} | {self.traversal_output.first_hamiltonian_cycle.cycle}"  # type: ignore[union-attr]
                    )
                    self.logger.debug(logger_msg)
                else:
                    self.logger.debug("Did not update the first Hamiltonian Cycle")
                self.hamiltonian_cycles_found += 1
                # remove appended game upon successful hamiltonian cycle discovery ( as this game.append is done outside of my cur_loser loop below)
                games.pop()
            else:
                self.full_paths_not_hamiltonian += 1
            return

        for cur_loser in adjacency_list.children:
            if cur_loser not in visited:
                visited.add(cur_loser)
                path.append(cur_loser)
                game = self.season_results.get_first_game_result(cur_winner, cur_loser)
                if game:
                    games.append(game)
                self.logger.debug(
                    f"games: {len(games)} path: {len(path)}\t{'Fwd:'.ljust(8)} {path}"
                )
                self._dfs(cur_loser, visited, path, games, first_parent_in_path)
                # traversal ended - backtrack
                path.pop()
                games.pop()
                visited.remove(cur_loser)
                self.logger.debug(
                    f"games: {len(games)} path: {len(path)}\t{'Back:'.ljust(8)} {path}"
                )
            else:
                # explicit "do nothing" the cur_loser already visited in this path
                pass

    def _find_hamiltonian_cycles(self, up_to_round: int) -> None:
        """setup and start dfs search for hamiltonian cycles"""
        self._build_adjacency_graph(up_to_round)
        largest_adjacency_list_parents = self.adjacency_graph.parents_with_most_children
        # just pick one of them bigguns
        largest_parent: int = largest_adjacency_list_parents[0]
        self._dfs(
            cur_winner=largest_parent,
            visited={largest_parent},
            path=[largest_parent],
            games=[],
            first_parent_in_path=largest_parent,
        )

    def process_season(self) -> None:
        """lets gooooo"""
        # iterate over round in sequential order to prevent unecessary compute/searching
        for round in self.season_results.rounds_list:
            self._build_adjacency_graph(up_to_round=round)

            if self._validate_hamiltonian_cycle_possible():
                self.logger.info(f"Begin search for round {round}")
                self._find_hamiltonian_cycles(up_to_round=round)
                self.traversal_output.total_dfs_steps = self.dfs_steps
                self.traversal_output.total_full_paths_not_hamiltonian = (
                    self.full_paths_not_hamiltonian
                )
                self.traversal_output.total_hamiltonian_cycles = (
                    self.hamiltonian_cycles_found
                )
                self._hamiltonian_cycle_permutation_logger(force=True)
                if self.traversal_output.first_hamiltonian_cycle:
                    self.logger.info("Hamiltonian Cycle Found")
                    self.logger.info(
                        self.traversal_output.first_hamiltonian_cycle.cycle_names
                    )
                    self.logger.info(
                        self.traversal_output.first_hamiltonian_cycle.hamiltonian_cycle_game_details_pprint()
                    )
                    break
                else:
                    self.logger.info("Hamiltonian Cycle Not Found")
            else:
                self.logger.info(
                    f"Round {round}: Hamiltonian Cycle is not possible, team(s) without wins or losses present"
                )

        # save resultsaaahhh
        self._save_output_to_file()
