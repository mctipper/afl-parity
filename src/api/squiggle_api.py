import aiohttp
import asyncio
from datetime import datetime
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

    async def _get_api_response(self, url: str) -> Any:
        """helper method to get data from the API asynchronously"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as response:
                if response.status >= 400:
                    self.logger.error(f"{url} - {response.status} - {response.reason}")
                    raise APIRequestError(
                        f"API request failed with status code {response.status}",
                        Exception(response.reason),
                    )
                elif response.status >= 300:
                    self.logger.info(f"{url} - {response.status} - {response.reason}")
                else:
                    self.logger.debug(f"{url} - {response.status} - {response.reason}")

                if "json" in response.headers["Content-Type"]:
                    return await response.json()
                else:
                    raise APIResponseTypeError(
                        f"{response.headers['Content-Type']} is not a supported API response type"
                    )

    async def _populate_teams(self) -> None:
        """get team data from squiggs asynchronously"""
        team_data: Any = await self._get_api_response(self.team_data_url)

        self.logger.info("Received teams data from squiggle API successfully")

        for team in team_data["teams"]:
            cur_team = Team(
                id=int(team["id"]),
                name=team["name"],
                abbrev=team["abbrev"],
                logo_url=f"{self.RESOURCE_URL}{team['logo']}",
            )

            self.season_results.add_team(cur_team)

        self.logger.info("Parsed teams data from squiggle API successfully")

    async def _populate_season_results(self) -> None:
        """get season result data from squiggs asynchronously"""
        season_result_data: Any = await self._get_api_response(self.season_result_url)

        self.logger.info("Received season results data from squiggle API successfully")

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

    async def _download_logos(self) -> None:
        """download the logos from squiggs asynchronously"""
        try:
            project_root: Path = Path(__file__).parents[
                2
            ]  # yuck (but keeping this as is)
            output_dir: Path = project_root / "output" / "logos"
            output_dir.mkdir(parents=True, exist_ok=True)

            async def download_logo(team: Team) -> None:
                """download a single teams logo"""
                output_file: Path = output_dir / team.logo_filename
                if not output_file.exists():
                    async with aiohttp.ClientSession() as session:
                        async with session.get(team.logo_url) as response:
                            response.raise_for_status()
                            with open(output_file, "wb") as f:
                                f.write(await response.read())
                    self.logger.info(
                        f"Downloaded logo for {team.name} in season {self.season}"
                    )

            tasks = [download_logo(team) for team in self.season_results.team_list]

            await asyncio.gather(*tasks)

            self.logger.info("Downloaded team logos from squiggle successfully")

        except aiohttp.ClientError as e:
            self.logger.error(f"An error occurred while downloading logos: {str(e)}")
            raise e

    async def populate_data(self) -> None:
        """builder method, get all the goodies from squiggs asynchronously"""
        # get the data
        await asyncio.gather(self._populate_teams(), self._populate_season_results())
        # small tidy-up
        self._tidy_up_teams()
        # download logos of teams from that season
        await self._download_logos()
