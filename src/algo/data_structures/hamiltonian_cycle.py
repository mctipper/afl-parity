from pydantic import BaseModel
from api.response_models import GameResult, Team
from datetime import datetime
import logging
from typing import List, Optional

logger = logging.getLogger("main")


class HamiltonianCycle(BaseModel):
    cycle: List[int]
    cycle_names: List[str] = []
    games: List[GameResult]

    def __str__(self) -> str:
        return f"Hamiltonian Cycle: {self.cycle_names}"

    @property
    def max_date(self) -> datetime:
        return max(game.date for game in self.games)  # type: ignore

    @property
    def max_round(self) -> int:
        return max(game.round for game in self.games)  # type: ignore

    def update_cycle_names(self, teams: List[Team]) -> None:
        team_id_to_name = {team.id: team.name for team in teams}
        self.cycle_names = [
            team_id_to_name.get(team_id, "Unknown") for team_id in self.cycle
        ]


class FirstCycle(BaseModel):
    first_hamiltonian_cycle: Optional[HamiltonianCycle] = None

    def update(self, new_cycle: HamiltonianCycle) -> None:
        if (
            not self.first_hamiltonian_cycle
            or new_cycle.max_date < self.first_hamiltonian_cycle.max_date
        ):
            self.first_hamiltonian_cycle = new_cycle
