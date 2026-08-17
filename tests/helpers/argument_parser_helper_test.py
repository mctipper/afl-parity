from datetime import datetime
from unittest.mock import patch

import pytest

from afl_parity.helpers import ArgumentParserHelper
from afl_parity.helpers.argument_parser_helper import Args


def test_argument_parser_helper():
    test_args = ["run_pytest_script.py", "--season", "2025", "--debug"]
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.season == 2025
        assert helper.args.all is False
        assert helper.args.debug is True


def test_argument_parser_no_debug_helper():
    test_args = ["run_pytest_script.py", "--season", "2025"]
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.season == 2025
        assert helper.args.all is False
        assert helper.args.debug is False


def test_argument_parser_all_helper():
    test_args = ["run_pytest_script.py", "--all"]
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.all is True
        assert helper.args.debug is False


def test_argument_parser_all_and_season_mutually_exclusive():
    test_args = ["run_pytest_script.py", "--all", "--season", "2025"]
    with patch("sys.argv", test_args):
        with pytest.raises(SystemExit):
            ArgumentParserHelper()


def test_argument_parser_no_season_helper():
    test_args = ["run_pytest_script.py", "--debug"]
    cur_year = datetime.now().year
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.season == cur_year
        assert helper.args.all is False
        assert helper.args.debug is True


def test_argument_parser_no_arguments_helper():
    test_args = ["run_pytest_script.py"]
    cur_year = datetime.now().year
    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()
        assert isinstance(helper.args, Args)
        assert helper.args.season == cur_year
        assert helper.args.all is False
        assert helper.args.debug is False


def test_validate_season():
    test_args = ["run_pytest_script.py"]

    with patch("sys.argv", test_args):
        helper = ArgumentParserHelper()

    helper.args.season = 2020
    helper.validate_season(helper.args.season)
    assert helper.args.season == 2020

    helper.args.season = 1800
    with pytest.raises(SystemExit):
        helper.validate_season(helper.args.season)
