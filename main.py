import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from helpers import ArgumentParserHelper, LoggerHelper, OutputHelper  # noqa: E402
from helpers.argument_parser_helper import Args  # noqa: E402
from data.squiggle_client import SquiggleClient  # noqa: E402
from algo.dfs import DFS  # noqa: E402
from render.infographic import Infographic  # noqa: E402
from datetime import datetime  # noqa: E402
from types import TracebackType  # noqa: E402
from typing import List, Type  # noqa: E402
import logging  # noqa: E402
import time  # noqa: E402

FIRST_SEASON: int = 1897


def _seasons_to_process(args: Args) -> List[int]:
    if args.all:
        return list(range(FIRST_SEASON, datetime.now().year + 1))
    return [args.season]


def _process_season(season: int, debug: bool, run_logger: logging.Logger) -> None:
    season_logger = LoggerHelper.setup(
        current_datetime=datetime.now(),
        logname=f"{season}_main",
        output_file_debug=debug,
    )
    run_logger.info(f"Starting season {season}")

    squiggle_api = SquiggleClient(season)
    squiggle_api.populate_data()

    dfs = DFS(squiggle_api.season_results, debug)
    traversal_output = dfs.run()

    infographic = Infographic(
        season_results=dfs.season_results, traversal_output=traversal_output
    )
    infographic.create_infographic()

    season_logger.info(f"Season {season} complete")
    run_logger.info(f"Season {season} complete")


def main() -> None:
    start_time = time.time()
    run_logger = logging.getLogger("run")
    argument_parser_helper = ArgumentParserHelper()

    seasons = _seasons_to_process(argument_parser_helper.args)

    for season in seasons:
        checkpoint_time = time.time()
        _process_season(season, argument_parser_helper.args.debug, run_logger)
        run_logger.info(f"Season {season} in {(time.time() - checkpoint_time):.2f}s")

    OutputHelper.combine_all_json_outputs()

    run_logger.info(f"Complete in {(time.time() - start_time):.2f} seconds")


def _log_uncaught_exception(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: TracebackType | None,
) -> None:
    logging.getLogger("run").critical(
        "Fatal unhandled error", exc_info=(exc_type, exc_value, exc_tb)
    )
    sys.__excepthook__(exc_type, exc_value, exc_tb)


if __name__ == "__main__":
    LoggerHelper.setup(datetime.now(), "run")
    sys.excepthook = _log_uncaught_exception
    main()
