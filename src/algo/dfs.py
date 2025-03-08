from models import SeasonResults
from algo.data_structures import AdjacencyGraph, HamiltonianCycle, DFSTraversalOutput
from typing import List
from datetime import datetime
import json
from pathlib import Path
import logging


class DFS:
    season_results: SeasonResults
    adjacency_graph: AdjacencyGraph
    traversal_output: DFSTraversalOutput
    early_exit: bool = False
    early_exit_date: datetime
    dfs_steps: int = 0
    skipped_steps: int = 0
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

    def _build_adjacency_graph(self, cur_round: int) -> None:
        """dynmically build adjacency graph up to the supplied cur_round"""
        self.adjacency_graph = AdjacencyGraph()
        for round_results in self.season_results:
            for game_result in round_results:
                if game_result.round <= cur_round:
                    if game_result.winnerteamid and game_result.loserteamid:
                        self.adjacency_graph.add_child_to_parent(
                            game_result.winnerteamid, game_result.loserteamid
                        )

    def _populate_hamiltonian_cycle_with_game_data(
        self, hamiltonian_cycle: HamiltonianCycle
    ) -> None:
        # populate with game data
        for i, cur_winner in enumerate(hamiltonian_cycle.cycle):
            try:
                cur_loser = hamiltonian_cycle.cycle[i + 1]
            except IndexError:
                # if reached end of list, return first in list
                cur_loser = hamiltonian_cycle.cycle[0]

            cur_game = self.season_results.get_first_game_result_between_teams(
                winner=cur_winner, loser=cur_loser
            )
            if cur_game:
                hamiltonian_cycle.games.append(cur_game)

    def _save_output_to_file(self) -> None:
        """save the traversal output to a json file in the output directory"""
        try:
            project_root: Path = Path(__file__).parents[2]  # yueck

            output_dir: Path = project_root / "output" / str(self.season_results.season)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file: Path = (
                output_dir / f"{self.season_results.season}_dfs_traversal_output.json"
            )

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
                f"Season: {self.season_results.season} | DFS Steps: {self.dfs_steps:<2} | Skipped Steps: {self.skipped_steps:<2} | Hamiltonian Cycles Found: {self.hamiltonian_cycles_found}"
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

    def _dfs(self, cur_winner: int, path: List[int]) -> None:
        """recursive method to perform DFS. Exits early upon successfull hamiltonian cycle being found"""
        if self.early_exit:
            # early_exit trigger made, lets get out of here
            return

        self.dfs_steps += 1
        self._hamiltonian_cycle_permutation_logger()

        # gets the losers for the current winner
        adjacency_list = self.adjacency_graph.get_adjacency_graph(cur_winner)
        if not adjacency_list:
            # this should never occur...
            return

        # once all teams have been visited, can inspect for hamiltonian cycle
        if len(path) == self.season_results.nteams:
            adjacency_list = self.adjacency_graph.get_adjacency_graph(cur_winner)
            if adjacency_list and path[0] in adjacency_list.children:
                self.logger.debug("Found Hamiltonian Cycle")
                self.hamiltonian_cycles_found += 1
                cur_hamiltonian_cycle = HamiltonianCycle(cycle=path.copy())
                self._populate_hamiltonian_cycle_with_game_data(cur_hamiltonian_cycle)
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
                    if self.traversal_output.first_hamiltonian_cycle:
                        if (
                            self.traversal_output.first_hamiltonian_cycle.max_date
                            <= self.early_exit_date
                        ):
                            self.early_exit = True
                            # the first game of the round is already part of the hamiltonian path, we
                            # can stop travesing now but just escaping the queued recursions early
                            self.logger.debug(
                                f"Hamiltonian Cycle includes first game this round - early exit: {self.traversal_output.first_hamiltonian_cycle.max_date} <= {self.early_exit_date}"
                            )
                            return
                else:
                    self.logger.debug("Did not update the first Hamiltonian Cycle")
            else:
                self.full_paths_not_hamiltonian += 1
            return

        for cur_loser in adjacency_list.children:
            if cur_loser not in path and not self.early_exit:
                game = self.season_results.get_first_game_result_between_teams(
                    cur_winner, cur_loser
                )
                if game:
                    # check if this game was before the max date of all games in the current first hamiltonian cycle
                    # to allow for skipping pointless combinations
                    if (
                        self.traversal_output.first_hamiltonian_cycle
                        and (
                            game.date
                            < self.traversal_output.first_hamiltonian_cycle.max_date
                        )
                    ) or not self.traversal_output.first_hamiltonian_cycle:
                        path.append(cur_loser)
                        self.logger.debug(
                            f"path: {len(path):<2}\t{'Fwd:'.ljust(8)} {path}"
                        )
                        self._dfs(cur_loser, path)
                        # check for early exit before backtracking
                        if self.early_exit:
                            return
                        # traversal ended - backtrack
                        path.pop()
                        self.logger.debug(
                            f"path: {len(path):<2}\t{'Back:'.ljust(8)} {path}"
                        )
                    else:
                        # can skip this game, as it occured after the last game of the current hamiltonian cycle, no point checking it
                        self.skipped_steps += 1
                        if self.traversal_output.first_hamiltonian_cycle:
                            self.logger.debug(
                                f"{cur_winner}-{cur_loser} Gamedate {game.date} Found Hamiltonian Cycle Maxdate {self.traversal_output.first_hamiltonian_cycle.max_date} - Skipped"
                            )
                        pass
            else:
                # explicit "do nothing" the cur_loser already visited in this path
                pass

    def _find_hamiltonian_cycles(self, cur_round: int) -> None:
        """setup and start dfs search for hamiltonian cycles"""
        # build the adjanecy graph for results up to this cur_round
        self._build_adjacency_graph(cur_round)
        adjacency_list_parents = self.adjacency_graph.parents_with_least_children
        # just pick one
        cur_parent: int = adjacency_list_parents[0]
        # get the early exit date (ie first game of the round)
        cur_round_results = self.season_results.get_round_results(cur_round)
        if cur_round_results:
            self.early_exit_date = cur_round_results.min_date_of_round
        self.logger.info(
            f"Begin search for round {cur_round}, using parent {cur_parent}, with earlyexitdate {self.early_exit_date}"
        )
        self._dfs(
            cur_winner=cur_parent,
            path=[cur_parent],
        )

    def process_season(self) -> None:
        """lets gooooo"""
        # iterate over cur_round in sequential order to prevent unecessary compute/searching
        for cur_round in self.season_results.rounds_list:
            self._build_adjacency_graph(cur_round=cur_round)

            if self._validate_hamiltonian_cycle_possible():
                self._find_hamiltonian_cycles(cur_round=cur_round)

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
                    f"Round {cur_round}: Hamiltonian Cycle is not possible, team(s) without wins or losses present"
                )

        # save resultsaaahhh
        self._save_output_to_file()
