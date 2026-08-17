import argparse
from datetime import datetime
from dataclasses import dataclass

FIRST_SEASON: int = 1897


@dataclass(slots=True)
class Args:
    season: int
    all: bool
    debug: bool


class ArgumentParserHelper:
    """helper class to handle definition, validation, and parsing of command line arguments"""

    args: Args

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(description="Season argument")
        season_group = self.parser.add_mutually_exclusive_group()
        season_group.add_argument(
            "-s",
            "--season",
            type=int,
            default=None,
            help="Season (Year) to be assessed. Default is this year. Cannot be used with -a/--all",
        )
        season_group.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="Run for all seasons, 1897 to today. Cannot be used with -s/--season",
        )
        self.parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="Enable debug logging to file",
        )

        self.args = self.process_args()

    def process_args(self) -> Args:
        parsed_args = self.parser.parse_args()
        season = (
            parsed_args.season
            if parsed_args.season is not None
            else datetime.now().year
        )
        self.validate_season(season)
        return Args(season=season, all=parsed_args.all, debug=parsed_args.debug)

    def validate_season(self, season: int) -> None:
        """custom validator for 'season'"""
        if season < FIRST_SEASON:
            self.parser.error(
                f"Invalid season '{season}'. Season year must be >= {FIRST_SEASON}."
            )
