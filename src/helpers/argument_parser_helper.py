import argparse
import logging
import sys
from dataclasses import dataclass

logger = logging.getLogger("main")


@dataclass
class Args:
    season: int
    clearcache: bool


class ArgumentParserHelper:
    """class to handle definition, validation, and parsing of command line arguments"""

    args: Args

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(description="Season argument")
        self.parser.add_argument(
            "-s",
            "--season",
            type=str,
            required=True,
            help="Season (Year) to be assessed",
        )
        self.parser.add_argument(
            "-c",
            "--clearcache",
            action="store_true",
            help="Clear cached files/resources for this season",
        )

        # log verbatims
        logger.debug(f"Command line arguments: \n{' '.join(sys.argv[1:])}")

        self.args = self.process_args()

    def process_args(self) -> Args:
        parsed_args = self.parser.parse_args()
        # log parsed
        logger.debug(f"Command line arguments parsed: \n{parsed_args}")
        self.validate_season(parsed_args.season)
        return Args(season=parsed_args.season, clearcache=parsed_args.clearcache)

    def validate_season(self, season: str) -> None:
        """custom validator for 'season'"""
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
