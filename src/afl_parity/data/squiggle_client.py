from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import logging

import requests

from afl_parity.models import SeasonResults, GameResult, Team
from afl_parity.paths import OUTPUT_DIR
from .raw_models import RawGameResult, RawTeam, parse_raw_game, parse_raw_team


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


def _raw_team_to_team(raw: RawTeam, resource_url: str) -> Team:
    return Team(
        id=int(raw.id),
        name=raw.name,
        abbrev=raw.abbrev,
        logo_url=f"{resource_url}{raw.logo}",
    )


def _raw_game_to_game_result(raw: RawGameResult) -> GameResult:
    return GameResult(
        id=int(raw.id),
        round=int(raw.round),
        roundname=raw.roundname,
        hteamid=raw.hteamid,
        ateamid=raw.ateamid,
        hscore=int(raw.hscore),
        ascore=int(raw.ascore),
        hteamname=raw.hteam,
        ateamname=raw.ateam,
        winnerteamid=int(raw.winnerteamid) if raw.winnerteamid else None,
        wteamname=raw.winner,
        date=datetime.strptime(raw.date, "%Y-%m-%d %H:%M:%S"),
    )


class SquiggleClient:
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

    def _get_api_response(self, url: str) -> Any:
        """helper method to get data from the API"""
        response = requests.get(url, headers=self.headers)

        if response.status_code >= 400:
            self.logger.error(f"{url} - {response.status_code} - {response.reason}")
            raise APIRequestError(
                f"API request failed with status code {response.status_code}",
                Exception(response.reason),
            )
        elif response.status_code >= 300:
            self.logger.info(f"{url} - {response.status_code} - {response.reason}")
        else:
            self.logger.debug(f"{url} - {response.status_code} - {response.reason}")

        if "json" in response.headers["Content-Type"]:
            return response.json()
        else:
            raise APIResponseTypeError(
                f"{response.headers['Content-Type']} is not a supported API response type"
            )

    def _populate_teams(self) -> None:
        """get team data from squiggs"""
        team_data: Any = self._get_api_response(self.team_data_url)

        self.logger.info("Received teams data from squiggle API successfully")

        for raw_team_data in team_data["teams"]:
            raw_team = parse_raw_team(raw_team_data)
            self.season_results.add_team(_raw_team_to_team(raw_team, self.RESOURCE_URL))

        self.logger.info("Parsed teams data from squiggle API successfully")

    def _populate_season_results(self) -> None:
        """get season result data from squiggs"""
        season_result_data: Any = self._get_api_response(self.season_result_url)

        self.logger.info("Received season results data from squiggle API successfully")

        for raw_game_data in season_result_data["games"]:
            raw_game = parse_raw_game(raw_game_data)
            self.season_results.add_game_result(_raw_game_to_game_result(raw_game))

        self.logger.info("Parsed teams data from squiggle API successfully")

    def _tidy_up_teams(self) -> None:
        """during the war years teams exist but were not able to play games, this method
        removes those from the team list
        """
        before_teams_count: int = self.season_results.nteams
        self.season_results.remove_unused_teams()
        after_teams_count: int = self.season_results.nteams
        if after_teams_count < before_teams_count:
            self.logger.info(
                f"Removed {after_teams_count} teams from teams list for this season"
            )

    def _download_logos(self) -> None:
        """download the logos from squiggs, one thread per team"""
        try:
            output_dir: Path = OUTPUT_DIR / "logos"
            output_dir.mkdir(parents=True, exist_ok=True)

            def download_logo(team: Team) -> None:
                """download a single teams logo"""
                output_file: Path = output_dir / team.logo_filename
                if not output_file.exists():
                    response = requests.get(team.logo_url)
                    response.raise_for_status()
                    with open(output_file, "wb") as f:
                        f.write(response.content)
                    self.logger.info(
                        f"Downloaded logo for {team.name} in season {self.season}"
                    )

            with ThreadPoolExecutor() as executor:
                list(executor.map(download_logo, self.season_results.team_list))

            self.logger.info("Downloaded team logos from squiggle successfully")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"An error occurred while downloading logos: {str(e)}")
            raise e

    def populate_data(self) -> None:
        """builder method, get all the goodies from squiggs"""
        # get the data
        self._populate_teams()
        self._populate_season_results()
        # small tidy-up
        self._tidy_up_teams()
        # download logos of teams from that season
        self._download_logos()
