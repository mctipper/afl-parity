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
    round: int
    results: List[GameResult]

    def __iter__(self) -> Iterator[GameResult]:  # type: ignore[override]
        return iter(sorted(self.results, key=lambda game: game.date))


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

    def get_round_results(self, round: int) -> RoundResults:
        try:
            return self.round_results[round]
        except KeyError:
            raise KeyError(f"Cannot find round {round}")

    def get_team(self, teamid: int) -> Team:
        try:
            return self.teams[teamid]
        except KeyError:
            raise KeyError(f"Cannot find team {teamid}")

    def remove_unused_teams(self) -> None:
        """some teams still exist but did not play any games that particular season (mainly
        due to those world war things). This method removes those which permits parity searches
        to execute correctly"""
        referenced_team_ids = set()
        for round_results in self.round_results.values():
            for game in round_results.results:
                referenced_team_ids.add(game.hteamid)
                referenced_team_ids.add(game.ateamid)

        self.teams = {
            team_id: team
            for team_id, team in self.teams.items()
            if team_id in referenced_team_ids
        }

    def get_first_game_result_between_teams(
        self, winner: int, loser: int
    ) -> GameResult:
        for round_results in self.round_results.values():
            for game in round_results:
                if game.winnerteamid == winner and game.loserteamid == loser:
                    return game
        raise ValueError(f'Unable to find game where {winner} defeated {loser}')

    def __iter__(self) -> Iterator[RoundResults]:  # type: ignore[override]
        for round_id in self.rounds_list:
            yield self.round_results[round_id]
