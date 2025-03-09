from models import GameResult, RoundResults
from datetime import datetime


def test_round_results_initialisation():
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
    round_results = RoundResults(round=1, results=[game])
    assert round_results.round == 1
    assert len(round_results.results) == 1
    assert round_results.results[0].id == 1


def test_round_results_iteration():
    game1 = GameResult(
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
    game2 = GameResult(
        id=2,
        round=1,
        roundname="Round 1",
        hteamid=3,
        ateamid=4,
        hscore=110,
        ascore=95,
        winnerteamid=3,
        hteamname="Team C",
        ateamname="Team D",
        wteamname="Team C",
        date=datetime(2025, 3, 11),
    )
    round_results = RoundResults(round=1, results=[game1, game2])
    games = list(round_results)
    assert len(games) == 2
    assert games[0].id == 1
    assert games[1].id == 2
