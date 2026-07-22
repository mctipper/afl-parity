from models import GameResult, RoundResults, SeasonResults
from helpers import LoggerHelper
from algo.data_structures import (
    AdjacencyGraph,
    AdjacencyList,
    HamiltonianCycle,
    DFSTraversalOutput,
)
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import copy


@dataclass(slots=True)
class _DFSCounters:
    """pure step counters, copied into DFSTraversalOutput at the end of each round"""

    dfs_steps: int = 0
    round_dfs_steps: int = 0


@dataclass(slots=True)
class _EarlyExitState:
    """the reason + trigger data for finishing a traversal early - first class, loggable"""

    triggered: bool = False
    exit_date: Optional[datetime] = None
    reason: Optional[str] = None
    thread_start_pairs: List[List[int]] = field(default_factory=list)


class DFS:
    season_results: SeasonResults
    adjacency_graph: AdjacencyGraph
    traversal_output: DFSTraversalOutput
    output_file_debug: bool

    def __init__(
        self, season_results: SeasonResults, output_file_debug: bool = False
    ) -> None:
        self.season_results = season_results
        self.adjacency_graph = AdjacencyGraph()
        self.traversal_output = DFSTraversalOutput()
        self.output_file_debug = output_file_debug
        self.logger = logging.getLogger(f"{self.season_results.season}_main")
        self._counters = _DFSCounters()
        self._early_exit = _EarlyExitState()
        self._graph_lock = threading.Lock()

    def run(self) -> DFSTraversalOutput:
        """single public entry point: search every round in order, save output, return it"""
        # iterate over cur_round in sequential order to prevent unecessary compute/searching
        for cur_round in self.season_results.rounds_list:
            self._rebuild_adjacency_graph_for_round(cur_round)

            if not self._hamiltonian_cycle_possible():
                self._log_round_not_possible(cur_round)
                continue

            self._counters.round_dfs_steps = 0
            self._determine_early_exit_strategy(cur_round)
            self._search_round_for_hamiltonian_cycles(cur_round)
            self._sync_counters_to_traversal_output()
            self._log_round_summary(cur_round)

            if self.traversal_output.first_hamiltonian_cycle is not None:
                self._log_cycle_found()
                break
            else:
                self.logger.info("Hamiltonian Cycle Not Found")

        self._save_output_to_file()
        return self.traversal_output

    # graph construction / validation -----------------------------------
    def _rebuild_adjacency_graph_for_round(self, cur_round: int) -> None:
        """dynmically build adjacency graph up to the supplied cur_round"""
        self.adjacency_graph = AdjacencyGraph()
        for round_results in self.season_results:
            for game_result in round_results:
                if game_result.round <= cur_round:
                    if game_result.winnerteamid and game_result.loserteamid:
                        self.adjacency_graph.add_child_to_parent(
                            game_result.winnerteamid, game_result.loserteamid
                        )

    def _hamiltonian_cycle_possible(self) -> bool:
        """helper method to first check all teams have either won or lost at least one game"""
        parents_count = len(self.adjacency_graph.parents)
        children_count = len(self.adjacency_graph.children)
        nteams = self.season_results.nteams
        return nteams == parents_count == children_count

    def _trim_adjacency_graph_after_cycle(self, max_date: datetime) -> None:
        """remove any edge whose game occured after max_date - it can never
        improve on the current best hamiltonian cycle, so no point keeping it"""
        trimmed = 0
        for adjacency_list in self.adjacency_graph.adjacency_lists:
            for child in list(adjacency_list.children):
                game = self.season_results.get_first_game_result_between_teams(
                    adjacency_list.parent, child
                )
                if game.date > max_date:
                    adjacency_list.children.discard(child)
                    trimmed += 1
        if trimmed:
            self.logger.debug(f"Trimmed {trimmed} games occurring after {max_date}")

    # early exit strategy -------------------------------------------------
    def _determine_early_exit_strategy(self, cur_round: int) -> None:
        """picks the starting (parent, child) pairs for this round and the date
        beyond which a cycle cannot be beaten"""
        cur_round_results = self.season_results.get_round_results(cur_round)
        self._early_exit = _EarlyExitState()

        exit_date, pairs, reason = self._find_early_exit_pairs_from_single_result_teams(
            cur_round_results
        )
        if exit_date is None:
            exit_date, pairs, reason = self._find_early_exit_pair_from_first_game(
                cur_round_results
            )

        self._early_exit.exit_date = exit_date
        self._early_exit.thread_start_pairs = pairs
        self._early_exit.reason = reason

    def _find_early_exit_pairs_from_single_result_teams(
        self, cur_round_results: RoundResults
    ) -> Tuple[Optional[datetime], List[List[int]], Optional[str]]:
        """a team with only one win, or only one loss, recorded so far gives us
        an early-exit date: any cycle beating that date can't be bettered"""
        exit_date: Optional[datetime] = None
        pairs: List[List[int]] = []
        reason: Optional[str] = None

        if not (
            self.adjacency_graph.parents_with_one_child
            or self.adjacency_graph.children_with_one_parent
        ):
            return exit_date, pairs, reason

        # we have a game(s) that was the first win for a team(s) - that is our target "early exit" date
        if self.adjacency_graph.parents_with_one_child:
            # multiple teams may have won their first game in this round, so worth a thread for each; but the 'first' is the early_exit date
            for this_parent in self.adjacency_graph.parents_with_one_child:
                for game in cur_round_results:
                    if (
                        game.winnerteamid
                        and game.loserteamid
                        and game.winnerteamid == this_parent
                    ):
                        if not exit_date or game.date < exit_date:
                            exit_date = game.date
                            pairs.append([game.winnerteamid, game.loserteamid])
                            reason = "first win for a team this round"

        # we have a game(s) that was the lost for a team(s) - that is our target "early exit" date
        if self.adjacency_graph.children_with_one_parent:
            # multiple teams may have lost their first game in this round, so worth a thread for each; but the 'first' is the early_exit date
            for this_child in self.adjacency_graph.children_with_one_parent:
                for game in cur_round_results:
                    if (
                        game.winnerteamid
                        and game.loserteamid
                        and game.loserteamid == this_child
                    ):
                        if not exit_date or game.date < exit_date:
                            exit_date = game.date
                            pairs.append([game.winnerteamid, game.loserteamid])
                            reason = "first loss for a team this round"

        return exit_date, pairs, reason

    def _find_early_exit_pair_from_first_game(
        self, cur_round_results: RoundResults
    ) -> Tuple[Optional[datetime], List[List[int]], Optional[str]]:
        """fallback: no team had a first win/loss this round, so use the first
        game of the round as the early-exit date"""
        for game in cur_round_results:
            if game and game.winnerteamid and game.loserteamid:  # ensure not a draw
                return (
                    game.date,
                    [[game.winnerteamid, game.loserteamid]],
                    "first game of the round",
                )  # only want the first game
        return None, [], None

    def _check_early_exit_condition(self, thread_logger: logging.Logger) -> None:
        best = self.traversal_output.first_hamiltonian_cycle
        if (
            best is not None
            and self._early_exit.exit_date is not None
            and best.max_date <= self._early_exit.exit_date
        ):
            self._early_exit.triggered = True
            # the first game of the round is already part of the hamiltonian path, we
            # can stop travesing now but just escaping the queued recursions early
            self.logger.info(
                f"Early exit ({self._early_exit.reason}): "
                f"{best.max_date} <= {self._early_exit.exit_date}"
            )
            thread_logger.debug(f"Early exit triggered: {self._early_exit.reason}")

    # threaded search driver ----------------------------------------------
    def _search_round_for_hamiltonian_cycles(self, cur_round: int) -> None:
        """setup and start dfs search for hamiltonian cycles"""
        cpu_count: int = os.cpu_count() or 1  # mypy annoyances with max() function
        thread_pairs = self._early_exit.thread_start_pairs

        # one thread per parent-child relationship, by appending to the pre-determined ones
        for parent_child in list(thread_pairs):
            parent = parent_child[0]
            children = self.adjacency_graph.get_children_for_parent(parent)
            for child in children:
                new_tp: List[int] = [parent, child]
                if new_tp not in thread_pairs:
                    thread_pairs.append(new_tp)

        start_paths = self._expand_thread_start_paths(thread_pairs)

        with ThreadPoolExecutor(max_workers=max(cpu_count - 2, 1)) as executor:
            futures = []
            for path in start_paths:
                # setup to mimick the 'first steps' of the dfs search, allowing this parallel action to happen
                path_copy = copy.deepcopy(path)
                thread_logger = LoggerHelper.setup(
                    datetime.now(),
                    f"{self.season_results.season}_R{cur_round}_{'-'.join(map(str, path))}",
                    self.output_file_debug,
                )
                futures.append(
                    executor.submit(
                        self._dfs_search,
                        path[-1],
                        path_copy,
                        thread_logger,
                        len(path_copy),
                    )
                )
            # smash it out
            for future in as_completed(futures):
                future.result()

    def _expand_thread_start_paths(
        self, thread_pairs: List[List[int]]
    ) -> List[List[int]]:
        """runs every (parent, child) starting pair through the shallow-bfs chain
        walk, de-duplicating identical resulting paths (different pairs can walk
        forward into the same deeper path)"""
        start_paths: List[List[int]] = []
        seen: set[Tuple[int, ...]] = set()
        for parent_child in thread_pairs:
            for expanded_path in self._shallow_bfs_expand(list(parent_child)):
                key = tuple(expanded_path)
                if key not in seen:
                    seen.add(key)
                    start_paths.append(expanded_path)
        return start_paths

    def _shallow_bfs_expand(self, path: List[int]) -> List[List[int]]:
        """walk forward through forced single-successor moves, only forking into
        multiple starting paths at the first real branch point - avoids handing
        a thread a chain with no actual decision to make"""
        while len(path) < self.season_results.nteams:
            candidates = [
                child
                for child in self.adjacency_graph.get_children_for_parent(path[-1])
                if child not in path
            ]
            if len(candidates) == 1:
                path = path + candidates
                continue
            if not candidates:
                return [path]
            return [path + [candidate] for candidate in candidates]
        return [path]

    # recursive dfs core -------------------------------------------------
    def _dfs_search(
        self,
        cur_winner: int,
        path: List[int],
        thread_logger: logging.Logger,
        min_path_len: int,
    ) -> None:
        """recursive method to perform DFS. Exits early upon successfull hamiltonian cycle being found"""
        if self._early_exit.triggered:
            # early_exit trigger made, lets get out of here
            return

        self._counters.dfs_steps += 1
        self._counters.round_dfs_steps += 1

        # gets the losers for the current winner
        adjacency_list = self.adjacency_graph.get_adjacency_graph(cur_winner)
        if not adjacency_list:
            # this should never occur...
            return

        # once all teams have been visited, can inspect for hamiltonian cycle
        if len(path) == self.season_results.nteams:
            self._handle_full_path(cur_winner, path, thread_logger)
            return

        self._visit_children(
            cur_winner, adjacency_list, path, thread_logger, min_path_len
        )

    def _handle_full_path(
        self, cur_winner: int, path: List[int], thread_logger: logging.Logger
    ) -> None:
        adjacency_list = self.adjacency_graph.get_adjacency_graph(cur_winner)
        if adjacency_list and path[0] in adjacency_list.children:
            thread_logger.debug("Found Hamiltonian Cycle")
            thread_logger.debug(f"path: {len(path):<2}\t{''.ljust(8)} {path}")
            self._register_hamiltonian_cycle(path, thread_logger)

    def _register_hamiltonian_cycle(
        self, path: List[int], thread_logger: logging.Logger
    ) -> None:
        cur_hamiltonian_cycle = HamiltonianCycle(cycle=path.copy())
        self._populate_hamiltonian_cycle_with_game_data(cur_hamiltonian_cycle)
        self._maybe_update_best_cycle(cur_hamiltonian_cycle, thread_logger)

    def _maybe_update_best_cycle(
        self, candidate: HamiltonianCycle, thread_logger: logging.Logger
    ) -> None:
        current = self.traversal_output.first_hamiltonian_cycle
        if current is None or candidate.max_date < current.max_date:
            logger_msg = (
                "Updated Hamiltonian Cycle" if current else "First Hamiltonian Cycle"
            )
            if current:
                thread_logger.debug(
                    f"Current: {current.max_date} | New: {candidate.max_date}"
                )
            # this method double-validates if applicable to update, as a safety
            self.traversal_output.update_first_hamiltonian_cycle(candidate)
            best = self.traversal_output.first_hamiltonian_cycle
            assert best is not None
            self.logger.info(f"{logger_msg} | {best.max_date} | {best.cycle}")
            thread_logger.debug(logger_msg)

            with self._graph_lock:
                self._trim_adjacency_graph_after_cycle(best.max_date)

            self._check_early_exit_condition(thread_logger)
        else:
            thread_logger.debug("Did not update the first Hamiltonian Cycle")

    def _should_skip_game(self, game: GameResult) -> bool:
        """a game occurring after the current best cycle's max_date can never
        improve on it, so it's pointless to traverse"""
        best = self.traversal_output.first_hamiltonian_cycle
        return best is not None and game.date > best.max_date

    def _visit_children(
        self,
        cur_winner: int,
        adjacency_list: AdjacencyList,
        path: List[int],
        thread_logger: logging.Logger,
        min_path_len: int,
    ) -> None:
        for cur_loser in list(adjacency_list.children):
            if cur_loser in path or self._early_exit.triggered:
                # explicit "do nothing" the cur_loser already visited in this path
                continue

            game = self.season_results.get_first_game_result_between_teams(
                cur_winner, cur_loser
            )
            if not game:
                continue

            if self._should_skip_game(game):
                # can skip this game, as it occured after the last game of the current hamiltonian cycle, no point checking it
                best = self.traversal_output.first_hamiltonian_cycle
                if best:
                    thread_logger.debug(
                        f"{cur_winner}-{cur_loser} Gamedate {game.date} Found Hamiltonian Cycle Maxdate {best.max_date} - Skipped"
                    )
                continue

            self._advance_path(cur_loser, path, thread_logger, min_path_len)

    def _advance_path(
        self,
        cur_loser: int,
        path: List[int],
        thread_logger: logging.Logger,
        min_path_len: int,
    ) -> None:
        path.append(cur_loser)
        thread_logger.debug(f"path: {len(path):<2}\t{'Fwd:'.ljust(8)} {path}")
        self._dfs_search(cur_loser, path, thread_logger, min_path_len)
        # check for early exit before backtracking
        if self._early_exit.triggered:
            return
        # never unwind past the original seed path handed to this thread -
        # those steps belong to the pre-computed bfs chain, not this dfs's own stack
        if len(path) <= min_path_len:
            return
        # traversal ended - backtrack
        path.remove(
            cur_loser
        )  # only remove the current_loser, prevent backtracking over original input path
        thread_logger.debug(f"path: {len(path):<2}\t{'Back:'.ljust(8)} {path}")

    # hamiltonian cycle enrichment / output ---------------------------
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

    def _sync_counters_to_traversal_output(self) -> None:
        self.traversal_output.total_dfs_steps = self._counters.dfs_steps

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
                json.dump(json.loads(self.traversal_output.to_json()), f, indent=2)

            self.logger.info(f"Traversal results stored in {output_file}")

        except Exception as e:
            self.logger.error(f"Failed to save output: {e}")

    # logging --------------------------------------------------------------
    def _log_round_not_possible(self, cur_round: int) -> None:
        self.logger.info(
            f"Round {cur_round}: Hamiltonian Cycle is not possible, team(s) without wins or losses present"
        )

    def _log_round_summary(self, cur_round: int) -> None:
        self.logger.info(
            f"Season: {self.season_results.season} | Round: {cur_round} | "
            f"Round DFS Steps: {self._counters.round_dfs_steps:<2} | Season DFS Steps: {self._counters.dfs_steps:<2}"
        )

    def _log_cycle_found(self) -> None:
        best = self.traversal_output.first_hamiltonian_cycle
        assert best is not None
        self.logger.info("Hamiltonian Cycle Found")
        self.logger.info(best.cycle_names)
        self.logger.info(best.hamiltonian_cycle_game_details_pprint())
