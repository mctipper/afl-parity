from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Iterator
import logging

logger = logging.getLogger("main")


class Team(BaseModel):
    """the team model - api results for the team must be parsed into this format."""

    id: int
    name: str
    abbrev: str
    logo_url: str


class GameResult(BaseModel):
    """individual games"""

    id: int
    round: int
    roundname: str
    hteamid: int
    ateamid: int
    hscore: int
    ascore: int
    winnerteamid: Optional[int]
    date: datetime

    @property
    def wteamid(self) -> int | None:
        if not self.winnerteamid:
            return None
        if self.hteamid == self.winnerteamid:
            return self.hteamid
        if self.ateamid == self.winnerteamid:
            return self.ateamid
        return None

    @property
    def lteamid(self) -> int | None:
        if not self.winnerteamid:
            return None
        if self.hteamid != self.winnerteamid:
            return self.hteamid
        if self.ateamid != self.winnerteamid:
            return self.ateamid
        return None

    @property
    def wscore(self) -> int | None:
        if not self.winnerteamid:
            return None
        if self.hteamid == self.winnerteamid:
            return self.hscore
        if self.ateamid == self.winnerteamid:
            return self.ascore
        return None

    @property
    def lscore(self) -> int | None:
        if not self.winnerteamid:
            return None
        if self.hteamid != self.winnerteamid:
            return self.hscore
        if self.ateamid != self.winnerteamid:
            return self.ascore
        return None


class RoundResults(BaseModel):
    round: int
    results: List[GameResult]

    def __iter__(self) -> Iterator[GameResult]:
        return iter(self.results)


class SeasonResults(BaseModel):
    """individual season, with a list of GameResult objects for that season and
    also a list of Team objects that participated in that reason
    """

    season: int
    round_results: Dict[int, RoundResults]
    teams: Dict[int, Team]

    @property
    def nrounds(self) -> int:
        """number of rounds downloaded so far"""
        return len(self.round_results)

    @property
    def nteams(self) -> int:
        """number of teams this season"""
        return len(self.teams)

    @property
    def rounds_list(self) -> List[int]:
        """sorted list of round ids"""
        return sorted(list(self.round_results.keys()))

    @property
    def team_ids(self) -> List[int]:
        """list of team id integers"""
        return sorted(list(self.teams.keys()))

    def add_game_result(self, cur_game: GameResult) -> None:
        if cur_game.round not in self.round_results:
            self.round_results[cur_game.round] = RoundResults(
                round=cur_game.round, results=[]
            )
        self.round_results[cur_game.round].results.append(cur_game)

    def add_team(self, cur_team: Team) -> None:
        if cur_team.id not in self.teams:
            self.teams[cur_team.id] = cur_team

    def get_round_results(self, round: int) -> Optional[RoundResults]:
        try:
            return self.round_results[round]
        except KeyError:
            print(f"Round '{round}' not found in list '{self.rounds_list}'")
            return None

    def __iter__(self) -> Iterator[RoundResults]:
        for round_id in self.rounds_list:
            yield self.round_results[round_id]
