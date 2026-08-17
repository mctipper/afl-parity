from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import json
from .hamiltonian_cycle import HamiltonianCycle


@dataclass(slots=True)
class DFSTraversalOutput:
    total_dfs_steps: int = 0
    teams_count: int = 0
    first_hamiltonian_cycle: Optional[HamiltonianCycle] = None

    def update_first_hamiltonian_cycle(self, new_cycle: HamiltonianCycle) -> None:
        """update the hamiltonian cycle object only if its newer"""
        if (
            not self.first_hamiltonian_cycle
            or new_cycle.max_date < self.first_hamiltonian_cycle.max_date
        ):
            self.first_hamiltonian_cycle = new_cycle

    def __str__(self) -> str:
        return f"total_dfs_steps={self.total_dfs_steps} teams_count={self.teams_count} first_hamiltonian_cycle={self.first_hamiltonian_cycle}"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.first_hamiltonian_cycle:
            data["first_hamiltonian_cycle"] = self.first_hamiltonian_cycle.to_dict()
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
