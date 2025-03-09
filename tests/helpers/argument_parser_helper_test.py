import pytest
from unittest.mock import patch
from datetime import datetime
from helpers import ArgumentParserHelper
from helpers.argument_parser_helper import Args


def test_argument_parser_helper():
    test_args = ["run_pytest_script.py", "--season", "2025", "--debug"]
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.season == "2025"
        assert helper.args.debug is True


def test_argument_parser_no_debug_helper():
    test_args = ["run_pytest_script.py", "--season", "2025"]
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.season == "2025"
        assert helper.args.debug is False


def test_argument_parser_no_season_helper():
    test_args = ["run_pytest_script.py", "--debug"]
    cur_year = datetime.now().year
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.season == str(cur_year)
        assert helper.args.debug is True


def test_argument_parser_no_arguments_helper():
    test_args = ["run_pytest_script.py"]
    cur_year = datetime.now().year
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.season == str(cur_year)
        assert helper.args.debug is False


def test_validate_season():
    test_args = ["run_pytest_script.py"]

    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()

    helper.args.season = "2020"
    helper.validate_season(helper.args.season)
    assert helper.args.season == "2020"

    helper.args.season = "all"
    helper.validate_season(helper.args.season)
    assert helper.args.season == "all"

    helper.args.season = "1800"
    with pytest.raises(SystemExit):
        helper.validate_season(helper.args.season)

    helper.args.season = "invalid"
    with pytest.raises(SystemExit):
        helper.validate_season(helper.args.season)
