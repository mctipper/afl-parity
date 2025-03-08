from pydantic import BaseModel
from models import GameResult
from datetime import datetime
from typing import List, Dict, Any
import json


class HamiltonianCycle(BaseModel):
    cycle: List[int]
    games: List[GameResult]

    def __str__(self) -> str:
        return f"Hamiltonian Cycle: {self.cycle_names}"

    @property
    def max_date(self) -> datetime:
        return max(game.date for game in self.games)

    @property
    def max_round(self) -> int:
        return max(game.round for game in self.games)

    @property
    def cycle_names(self) -> List[str]:
        """apply team names to the hamiltonian cycle"""
        return [game.wteamname for game in self.games if game.wteamname]

    def hamiltonian_cycle_game_details_pprint(self) -> str:
        """just make the output look nice and legible"""
        result: str = "Hamiltonian Cycle Details\n"
        result += f"Rd. {self.max_round} - {self.max_date:%Y-%m-%d %H:%M:%S}\n"
        for teamid in self.cycle:
            for game in self.games:
                if game.winnerteamid == teamid:
                    formatted_string = f"Rd. {game.round}: {game.wteamname} def. {game.lteamname} ({game.wscore} - {game.lscore})\n"
                    result += formatted_string
        return result

    def model_dump_json(self) -> str:  # type: ignore[override]
        data: Dict[str, Any] = {}
        data["cycle"] = self.cycle
        data["cycle_names"] = self.cycle_names
        data["date"] = self.max_date
        data["round"] = self.max_round
        data["games"] = [json.loads(game.model_dump_json()) for game in self.games]
        return json.dumps(data, default=str)
