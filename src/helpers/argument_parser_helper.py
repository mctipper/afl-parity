import argparse
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Args:
    season: int | str
    debug: bool


class ArgumentParserHelper:
    """helper class to handle definition, validation, and parsing of command line arguments"""

    args: Args

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(description="Season argument")
        self.parser.add_argument(
            "-s",
            "--season",
            type=str,
            default=str(datetime.now().year),
            help="Season (Year) to be assessed, can be individual or 'all' to do 1897 to today. Default is this year",
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
        self.validate_season(parsed_args.season)
        return Args(season=parsed_args.season, debug=parsed_args.debug)

    def validate_season(self, season: str) -> None:
        """custom validator for 'season'"""
        if season.lower() == "all":
            return
        try:
            season_year = int(season)
            if season_year >= 1897:
                return
            else:
                self.parser.error(
                    f"Invalid season '{season}'. Season year must be >= 1897."
                )
        except ValueError:
            self.parser.error(
                f"Invalid season '{season}'. Season must be a valid year."
            )
