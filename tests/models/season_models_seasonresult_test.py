from models import SeasonResults, GameResult, Team
from datetime import datetime


def test_season_results_initialisation():
    season_results = SeasonResults(season=2025, round_results={}, teams={})
    assert season_results.season == 2025
    assert season_results.nrounds == 0
    assert season_results.nteams == 0


def test_season_results_add_game_result():
    season_results = SeasonResults(season=2025, round_results={}, teams={})
    game = GameResult(
        id=1,
        round=1,
        roundname="Round 1",
        hteamid=1,
        ateamid=2,
        hscore=100,
        ascore=90,
        winnerteamid=1,
        hteamname="Team A",
        ateamname="Team B",
        wteamname="Team A",
        date=datetime(2025, 3, 10),
    )
    season_results.add_game_result(game)
    assert season_results.nrounds == 1
    assert game in season_results.round_results[1].results


def test_season_results_add_team():
    season_results = SeasonResults(season=2025, round_results={}, teams={})
    team = Team(
        id=1, name="Team A", abbrev="TA", logo_url="http://example.com/logo.png"
    )
    season_results.add_team(team)
    assert season_results.nteams == 1
    assert season_results.teams[1].name == "Team A"


def test_season_results_getters():
    season_results = SeasonResults(season=2025, round_results={}, teams={})
    game = GameResult(
        id=1,
        round=1,
        roundname="Round 1",
        hteamid=1,
        ateamid=2,
        hscore=100,
        ascore=90,
        winnerteamid=1,
        hteamname="Team A",
        ateamname="Team B",
        wteamname="Team A",
        date=datetime(2025, 3, 10),
    )
    team = Team(
        id=1, name="Team A", abbrev="TA", logo_url="http://example.com/logo.png"
    )
    season_results.add_game_result(game)
    season_results.add_team(team)

    assert season_results.get_round_results(1) is not None
    assert season_results.get_team(1) is not None
    assert season_results.get_first_game_result_between_teams(1, 2) is not None


def test_season_results_iteration():
    season_results = SeasonResults(season=2025, round_results={}, teams={})
    game = GameResult(
        id=1,
        round=1,
        roundname="Round 1",
        hteamid=1,
        ateamid=2,
        hscore=100,
        ascore=90,
        winnerteamid=1,
        hteamname="Team A",
        ateamname="Team B",
        wteamname="Team A",
        date=datetime(2025, 3, 10),
    )
    season_results.add_game_result(game)
    rounds = list(season_results)
    assert len(rounds) == 1
    assert rounds[0].round == 1
    assert game in rounds[0].results
