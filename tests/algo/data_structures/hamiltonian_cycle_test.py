from algo.data_structures import HamiltonianCycle
from models import GameResult
from datetime import datetime


def test_hamiltonian_cycle_initialisation():
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
        round=2,
        roundname="Round 2",
        hteamid=3,
        ateamid=4,
        hscore=110,
        ascore=95,
        winnerteamid=3,
        hteamname="Team C",
        ateamname="Team D",
        wteamname="Team C",
        date=datetime(2025, 3, 17),
    )
    cycle = HamiltonianCycle(cycle=[1, 3])
    cycle.games.append(game1)
    cycle.games.append(game2)
    assert cycle.cycle == [1, 3]
    assert cycle.games == [game1, game2]


def test_hamiltonian_cycle_max_date():
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
        round=2,
        roundname="Round 2",
        hteamid=3,
        ateamid=4,
        hscore=110,
        ascore=95,
        winnerteamid=3,
        hteamname="Team C",
        ateamname="Team D",
        wteamname="Team C",
        date=datetime(2025, 3, 17),
    )
    cycle = HamiltonianCycle(cycle=[1, 3])
    cycle.games.append(game1)
    cycle.games.append(game2)
    assert cycle.max_date == datetime(2025, 3, 17)


def test_hamiltonian_cycle_max_round():
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
        round=2,
        roundname="Round 2",
        hteamid=3,
        ateamid=4,
        hscore=110,
        ascore=95,
        winnerteamid=3,
        hteamname="Team C",
        ateamname="Team D",
        wteamname="Team C",
        date=datetime(2025, 3, 17),
    )
    cycle = HamiltonianCycle(cycle=[1, 3])
    cycle.games.append(game1)
    cycle.games.append(game2)
    assert cycle.max_round == 2


def test_hamiltonian_cycle_cycle_names():
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
        round=2,
        roundname="Round 2",
        hteamid=3,
        ateamid=4,
        hscore=110,
        ascore=95,
        winnerteamid=3,
        hteamname="Team C",
        ateamname="Team D",
        wteamname="Team C",
        date=datetime(2025, 3, 17),
    )
    cycle = HamiltonianCycle(cycle=[1, 3])
    cycle.games.append(game1)
    cycle.games.append(game2)
    assert cycle.cycle_names == ["Team A", "Team C"]


def test_hamiltonian_cycle_game_details_pprint():
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
        round=2,
        roundname="Round 2",
        hteamid=3,
        ateamid=4,
        hscore=110,
        ascore=95,
        winnerteamid=3,
        hteamname="Team C",
        ateamname="Team D",
        wteamname="Team C",
        date=datetime(2025, 3, 17),
    )
    cycle = HamiltonianCycle(cycle=[1, 3])
    cycle.games.append(game1)
    cycle.games.append(game2)
    expected_output = (
        "Hamiltonian Cycle Details\n"
        "Rd. 2 - 2025-03-17 00:00:00\n"
        "Rd. 1: Team A def. Team B (100 - 90)\n"
        "Rd. 2: Team C def. Team D (110 - 95)\n"
    )
    assert cycle.hamiltonian_cycle_game_details_pprint() == expected_output


def test_hamiltonian_cycle_model_dump_json():
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
        round=2,
        roundname="Round 2",
        hteamid=3,
        ateamid=4,
        hscore=110,
        ascore=95,
        winnerteamid=3,
        hteamname="Team C",
        ateamname="Team D",
        wteamname="Team C",
        date=datetime(2025, 3, 17),
    )
    cycle = HamiltonianCycle(cycle=[1, 3])
    cycle.games.append(game1)
    cycle.games.append(game2)
    json_data = cycle.model_dump_json()
    assert "cycle" in json_data
    assert "cycle_names" in json_data
    assert "date" in json_data
    assert "round" in json_data
    assert "games" in json_data
