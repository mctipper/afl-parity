from afl_parity.helpers import ArgumentParserHelper, LoggerHelper, OutputHelper
from afl_parity.helpers.argument_parser_helper import Args
from afl_parity.data.squiggle_client import SquiggleClient
from afl_parity.algo.dfs import DFS
from afl_parity.render.infographic import Infographic
from datetime import datetime
from types import TracebackType
from typing import List, Type
import logging
import sys
import time

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


def _log_uncaught_exception(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: TracebackType | None,
) -> None:
    logging.getLogger("run").critical(
        "Fatal unhandled error", exc_info=(exc_type, exc_value, exc_tb)
    )
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main() -> None:
    # logger setup lives here, not in a __main__ guard - the console script calls
    # main() directly so a guard would never fire and we'd lose all run logging
    LoggerHelper.setup(datetime.now(), "run")
    sys.excepthook = _log_uncaught_exception

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


if __name__ == "__main__":
    main()
