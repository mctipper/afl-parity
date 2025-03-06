from helpers import ArgumentParserHelper, LoggerHelper
from datetime import datetime

# universal logging
logger = LoggerHelper.setup(current_datetime=datetime.now())


def main() -> None:
    argument_parser_helper = ArgumentParserHelper()
    print(argument_parser_helper.args.season)


if __name__ == "__main__":
    # Big Tarp logging pattern
    try:
        main()
    except Exception:
        logger.exception("Fatal error in main()")
