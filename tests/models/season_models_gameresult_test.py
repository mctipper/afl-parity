from datetime import datetime
from models import GameResult


def test_game_result_initialisation():
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
    assert game.id == 1
    assert game.round == 1
    assert game.roundname == "Round 1"
    assert game.hteamid == 1
    assert game.ateamid == 2
    assert game.hscore == 100
    assert game.ascore == 90
    assert game.winnerteamid == 1
    assert game.hteamname == "Team A"
    assert game.ateamname == "Team B"
    assert game.wteamname == "Team A"
    assert game.date == datetime(2025, 3, 10)


def test_game_result_properties():
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
    assert game.loserteamid == 2
    assert game.lteamname == "Team B"
    assert game.wscore == 100
    assert game.lscore == 90


def test_game_result_model_dump_json():
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
    json_data = game.model_dump_json()
    assert "loserteamid" in json_data
    assert "lteamname" in json_data
    assert "wscore" in json_data
    assert "lscore" in json_data
