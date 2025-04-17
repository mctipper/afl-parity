from helpers import ArgumentParserHelper, LoggerHelper, OutputHelper
from api.squiggle_api import SquiggleAPI
from algo.dfs import DFS
from render.infographic import Infographic
from datetime import datetime
from typing import List
import time
import asyncio


async def main() -> None:
    start_time: float = time.time()
    prev_checkpoint_time: float = start_time
    argument_parser_helper = ArgumentParserHelper()

    seasons: List[int]
    if argument_parser_helper.args.season == "all":
        FIRST_SEASON: int = 1897
        CURRENT_SEASON: int = datetime.now().year
        seasons = [yr for yr in range(FIRST_SEASON, CURRENT_SEASON + 1)]
    else:
        seasons = [int(argument_parser_helper.args.season)]

    for season in seasons:
        # universal logging
        logger = LoggerHelper.setup(
            current_datetime=datetime.now(),
            logname=f"{season}_main",
            output_file_debug=argument_parser_helper.args.debug,
        )

        logger.info(f"\n\n{'*' * 8} Starting {season} {'*' * 8}\n")

        # get data
        squiggle_api = SquiggleAPI(season)
        await squiggle_api.populate_data()

        # determine if hamiltonian cycle exists via DFS algorithm
        dfs = DFS(squiggle_api.season_results, argument_parser_helper.args.debug)
        dfs.process_season()

        # create infographic of the result (if any)
        infographic = Infographic(
            season_results=dfs.season_results, traversal_output=dfs.traversal_output
        )
        infographic.create_infographic()

        # admin
        checkpoint_time: float = time.time()

        logger.info(
            f"Season {season} in {(checkpoint_time - prev_checkpoint_time):.2f} seconds"
        )

        prev_checkpoint_time = checkpoint_time

    # post loop admin
    OutputHelper.combine_all_json_outputs()

    end_time: float = time.time()
    logger.info(f"Complete in {(end_time - start_time):.2f} seconds")


if __name__ == "__main__":
    # Big Tarp logging pattern
    try:
        ue_logger = LoggerHelper.setup(datetime.now(), "UNHANDLED_ERROR")
        asyncio.run(main())
    except Exception:
        ue_logger.exception("Fatal unhandled error in main()")
