from pydantic import BaseModel
from typing import Optional
import json
from algo.data_structures import HamiltonianCycle


class DFSTraversalOutput(BaseModel):
    total_dfs_steps: int = 0
    total_skipped_steps: int = 0
    early_exit: bool = False
    total_full_paths_not_hamiltonian: int = 0
    total_hamiltonian_cycles: int = 0
    first_hamiltonian_cycle: Optional[HamiltonianCycle] = None

    def update_first_hamiltonian_cycle(self, new_cycle: HamiltonianCycle) -> None:
        """update the hamiltonian cycle object only if its newer"""
        if (
            not self.first_hamiltonian_cycle
            or new_cycle.max_date < self.first_hamiltonian_cycle.max_date
        ):
            self.first_hamiltonian_cycle = new_cycle

    def __str__(self) -> str:
        return f"total_dfs_steps={self.total_dfs_steps} total_full_paths_not_hamiltonian={self.total_full_paths_not_hamiltonian}"

    def model_dump_json(self) -> str:  # type: ignore[override]
        data = self.model_dump()
        if self.first_hamiltonian_cycle:
            data["first_hamiltonian_cycle"] = json.loads(
                self.first_hamiltonian_cycle.model_dump_json()
            )
        return json.dumps(data, default=str)
