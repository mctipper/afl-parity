from datetime import datetime
from algo.data_structures import HamiltonianCycle, DFSTraversalOutput
from models import GameResult


def test_dfstraversaloutput_initialisation():
    traversal_output = DFSTraversalOutput()
    assert traversal_output.total_dfs_steps == 0
    assert traversal_output.first_hamiltonian_cycle is None


def test_update_first_hamiltonian_cycle():
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
        date=datetime(2025, 3, 9),
    )
    cycle1 = HamiltonianCycle(cycle=[1, 3])
    cycle2 = HamiltonianCycle(cycle=[1, 3])
    cycle1.games.append(game1)
    cycle2.games.append(game2)
    traversal_output = DFSTraversalOutput()
    # update will apply
    traversal_output.update_first_hamiltonian_cycle(cycle1)
    assert traversal_output.first_hamiltonian_cycle == cycle1
    # earlier one will update again
    traversal_output.update_first_hamiltonian_cycle(cycle2)
    assert traversal_output.first_hamiltonian_cycle == cycle2
    # later one (the first one again), will not update
    traversal_output.update_first_hamiltonian_cycle(cycle1)
    assert traversal_output.first_hamiltonian_cycle == cycle2


def test_dfstraversaloutput_str():
    traversal_output = DFSTraversalOutput(total_dfs_steps=10)
    assert str(traversal_output) == "total_dfs_steps=10"


def test_model_dump_json():
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
    cycle = HamiltonianCycle(cycle=[1, 2])
    cycle.games.append(game)
    traversal_output = DFSTraversalOutput(
        total_dfs_steps=10,
        first_hamiltonian_cycle=cycle,
    )
    json_data = traversal_output.to_json()
    assert "total_dfs_steps" in json_data
    assert "first_hamiltonian_cycle" in json_data
