from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Iterator
import json


class Team(BaseModel):
    """the team model - api results for the team must be parsed into this format"""

    id: int
    name: str
    abbrev: str
    logo_url: str

    @property
    def logo_filename(self) -> str:
        return self.logo_url.split("/")[-1]


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
    hteamname: str
    ateamname: str
    wteamname: Optional[str]
    date: datetime

    @property
    def loserteamid(self) -> int | None:
        if not self.winnerteamid:
            return None
        if self.hteamid != self.winnerteamid:
            return self.hteamid
        if self.ateamid != self.winnerteamid:
            return self.ateamid
        return None

    @property
    def lteamname(self) -> str | None:
        if not self.winnerteamid:
            return None
        if self.hteamid != self.winnerteamid:
            return self.hteamname
        if self.ateamid != self.winnerteamid:
            return self.ateamname
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

    def model_dump_json(self) -> str:  # type: ignore[override]
        data = self.model_dump()
        data["loserteamid"] = self.loserteamid
        data["lteamname"] = self.lteamname
        data["wscore"] = self.wscore
        data["lscore"] = self.lscore
        return json.dumps(data, default=str)


class RoundResults(BaseModel):
    """as per title..."""

    round: int
    results: List[GameResult]

    @property
    def min_date_of_round(self) -> datetime:
        """used for early escaping hamilton cycle searches"""
        if not self.results:
            return datetime.now()
        return min(game.date for game in self.results)

    @property
    def first_game(self) -> Optional[GameResult]:
        """"""
        for game in self.results:
            if game:
                if game.date == self.min_date_of_round:
                    return game
        return None

    def __iter__(self) -> Iterator[GameResult]:  # type: ignore[override]
        return iter(self.results)


class SeasonResults(BaseModel):
    """individual season, with all the round results and games and
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

    @property
    def team_list(self) -> List[Team]:
        return [team for _, team in self.teams.items()]

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
            return None

    def get_team(self, teamid: int) -> Optional[Team]:
        try:
            return self.teams[teamid]
        except KeyError:
            return None

    def get_first_game_result_between_teams(
        self, winner: int, loser: int
    ) -> Optional[GameResult]:
        first_game: Optional[GameResult] = None
        for round_results in self.round_results.values():
            for game in round_results:
                if game.winnerteamid == winner and game.loserteamid == loser:
                    if first_game is None or game.round < first_game.round:
                        first_game = game
        return first_game

    def get_team_from_first_game_of_round(self, round: int) -> int:
        cur_round: Optional[RoundResults] = self.get_round_results(round)
        if cur_round:
            if cur_round.first_game:
                return cur_round.first_game.hteamid
        return 0

    def __iter__(self) -> Iterator[RoundResults]:  # type: ignore[override]
        for round_id in self.rounds_list:
            yield self.round_results[round_id]
