from datetime import datetime
import requests
from typing import Dict, Any
from api.response_models import SeasonResults, GameResult, Team

import logging

logger = logging.getLogger("main")


class APIRequestError(Exception):
    """generic API request error"""

    def __init__(self, message: str, exception: Exception) -> None:
        super().__init__(message)
        self.original_exception = exception

    def __str__(self) -> str:
        return f"{super().__str__()} (caused by {repr(self.original_exception)})"


class APIResponseTypeError(Exception):
    """Custom exception for unexpected API response types"""

    pass


class SquiggleAPI:
    API_URL: str = "https://api.squiggle.com.au/"
    RESOURCE_URL: str = "https://squiggle.com.au"
    headers: Dict[str, Any] = {"User-Agent": "dummy@email.com"}
    season_results: SeasonResults

    def __init__(self, season: int) -> None:
        self.season = season
        self.season_result_url = (
            f"{self.API_URL}?q=games;year={str(self.season)};complete=100"
        )
        self.team_data_url = f"{self.API_URL}?q=teams;year={str(self.season)}"
        self.season_results = SeasonResults(season=season, round_results={}, teams={})

    def set_header(self, key: str, value: Any) -> None:
        self.headers[key] = value

    def update_headers(self, new_headers: Dict[str, Any]) -> None:
        for k, v in new_headers.items():
            self.headers[k] = v

    def __get_api_response(self, url: str) -> Any:
        """Helper method to get data from the API"""
        response = requests.get(url, headers=self.headers)

        if response.status_code >= 400:
            # response failed
            logger.error(f"{url} - {response.status_code} - {response.reason}")
            raise APIRequestError(
                f"API request failed with status code {response.status_code}",
                response.raise_for_status(),
            )
        elif response.status_code >= 300:
            # response redirected, can continue but logging event
            logger.info(f"{url} - {response.status_code} - {response.reason}")
        else:
            # response successful
            logger.debug(f"{url} - {response.status_code} - {response.reason}")

        # parse the data into json
        resp_content_type: str = response.headers["Content-Type"]
        if "json" in resp_content_type:
            data = response.json()
        else:
            raise APIResponseTypeError(
                f"{response.headers['Content-Type']} is not an implemented API response type"
            )

        return data

    def populate_teams(self) -> None:
        """ """

        team_data: Any = self.__get_api_response(self.team_data_url)

        for team in team_data["teams"]:
            cur_team = Team(
                id=int(team["id"]),
                name=team["name"],
                abbrev=team["abbrev"],
                logo_url=f"{self.RESOURCE_URL}{team['logo']}",
            )

            self.season_results.add_team(cur_team)

    def populate_season_results(self) -> None:
        """ """

        season_result_data: Any = self.__get_api_response(self.season_result_url)

        for game in season_result_data["games"]:
            cur_game = GameResult(
                round=int(game["round"]),
                roundname=game["roundname"],
                id=int(game["id"]),
                hteamid=game["hteamid"],
                ateamid=game["ateamid"],
                hscore=int(game["hscore"]),
                ascore=int(game["ascore"]),
                hteamname=game["hteam"],
                ateamname=game["ateam"],
                winnerteamid=int(game["winnerteamid"])
                if game["winnerteamid"]
                else None,
                wteamname=game["winner"],
                date=datetime.strptime(game["date"], "%Y-%m-%d %H:%M:%S"),
            )

            self.season_results.add_game_result(cur_game)

    def populate_data(self) -> None:
        self.populate_teams()
        self.populate_season_results()
