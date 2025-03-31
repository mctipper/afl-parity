from datetime import datetime
import requests
from pathlib import Path
from typing import Dict, Any
from models import SeasonResults, GameResult, Team
import logging


class APIRequestError(Exception):
    """generic API request error"""

    def __init__(self, message: str, exception: Exception) -> None:
        super().__init__(message)
        self.original_exception = exception

    def __str__(self) -> str:
        return f"{super().__str__()} (caused by {repr(self.original_exception)})"


class APIResponseTypeError(Exception):
    """generic exception for unexpected API response types, probs wont happen"""

    pass


class SquiggleAPI:
    """thx squiggle this is awesome API v helpful 10/10"""

    API_URL: str = "https://api.squiggle.com.au/"
    RESOURCE_URL: str = "https://squiggle.com.au"
    headers: Dict[str, Any] = {"User-Agent": "mctipper(at)github:afl-parity"}
    season_results: SeasonResults

    def __init__(self, season: int) -> None:
        self.season = season
        self.season_result_url = (
            f"{self.API_URL}?q=games;year={str(self.season)};complete=100"
        )
        self.team_data_url = f"{self.API_URL}?q=teams;year={str(self.season)}"
        self.season_results = SeasonResults(season=season, round_results={}, teams={})
        self.logger = logging.getLogger(f"{self.season}_main")

    def set_header(self, key: str, value: Any) -> None:
        self.headers[key] = value

    def update_headers(self, new_headers: Dict[str, Any]) -> None:
        for k, v in new_headers.items():
            self.headers[k] = v

    def __get_api_response(self, url: str) -> Any:
        """helper method to get data from the API"""
        response = requests.get(url, headers=self.headers)

        if response.status_code >= 400:
            # response failed
            self.logger.error(f"{url} - {response.status_code} - {response.reason}")
            raise APIRequestError(
                f"API request failed with status code {response.status_code}",
                response.raise_for_status(),
            )
        elif response.status_code >= 300:
            # response redirected, can continue but logging event
            self.logger.info(f"{url} - {response.status_code} - {response.reason}")
        else:
            # response successful
            self.logger.debug(f"{url} - {response.status_code} - {response.reason}")

        # parse the data into json
        resp_content_type: str = response.headers["Content-Type"]
        if "json" in resp_content_type:
            data = response.json()
        else:
            raise APIResponseTypeError(
                f"{response.headers['Content-Type']} is not an implemented API response type"
            )

        return data

    def _populate_teams(self) -> None:
        """get team data from squiggs"""

        team_data: Any = self.__get_api_response(self.team_data_url)

        for team in team_data["teams"]:
            cur_team = Team(
                id=int(team["id"]),
                name=team["name"],
                abbrev=team["abbrev"],
                logo_url=f"{self.RESOURCE_URL}{team['logo']}",
            )

            self.season_results.add_team(cur_team)

    def _populate_season_results(self) -> None:
        """get seaosn result data from squiggs"""

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

    def _tidy_up_teams(self) -> None:
        """ during the war years teams exist but were not able to play games, this method
        removes those from the team list
        """
        self.season_results.remove_unused_teams()

    def _download_logos(self) -> None:
        """download the logos from squiggs"""
        try:
            project_root: Path = Path(__file__).parents[2]  # yueck

            output_dir: Path = project_root / "output" / "logos"
            output_dir.mkdir(parents=True, exist_ok=True)

            for team in self.season_results.team_list:
                output_file: Path = output_dir / team.logo_filename

                if not output_file.exists():
                    response = requests.get(team.logo_url)
                    response.raise_for_status()
                    with open(output_file, "wb") as f:
                        f.write(response.content)
                    self.logger.info(
                        f"Downloaded logo for {team.name} in season {self.season}"
                    )
        except requests.exceptions.RequestException as re:
            raise re

    def populate_data(self) -> None:
        """builder method, get all the goodies from squiggs"""
        self._populate_teams()
        self._populate_season_results()
        self._tidy_up_teams()
        self._download_logos()
