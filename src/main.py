from helpers import ArgumentParserHelper, LoggerHelper
from api.squiggle_api import SquiggleAPI
from algo.dfs import DFS
from datetime import datetime

# universal logging
logger = LoggerHelper.setup(current_datetime=datetime.now())


def main() -> None:
    argument_parser_helper = ArgumentParserHelper()

    squiggle_api = SquiggleAPI(argument_parser_helper.args.season)
    squiggle_api.populate_data()

    print(squiggle_api.season_results.nteams)

    dfs = DFS(squiggle_api.season_results)

    dfs.process_season()

    print((dfs.hamiltonian_cycles))


if __name__ == "__main__":
    # Big Tarp logging pattern
    # try:
    #     main()
    # except Exception:
    #     logger.exception("Fatal error in main()")
    main()
