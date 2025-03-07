from pydantic import BaseModel
from api.response_models import GameResult
from datetime import datetime
from typing import List
import json
import logging

logger = logging.getLogger("main")


class HamiltonianCycle(BaseModel):
    cycle: List[int]
    games: List[GameResult]

    def __str__(self) -> str:
        return f"Hamiltonian Cycle: {self.cycle_names}"

    @property
    def max_date(self) -> datetime:
        return max(game.date for game in self.games)  # type: ignore

    @property
    def max_round(self) -> int:
        return max(game.round for game in self.games)  # type: ignore

    @property
    def cycle_names(self) -> List[str]:
        return [game.wteamname for game in self.games]

    def hamiltonian_cycle_game_details_pprint(self) -> str:
        result: str = "Hamiltonian Cycle Details\n"
        result += f"Rd. {self.max_round} - {self.max_date:%Y-%m-%d %H:%M:%S}\n"
        for teamid in self.cycle:
            for game in self.games:
                if game.winnerteamid == teamid:
                    formatted_string = f"Rd. {game.round}: {game.wteamname} def. {game.lteamname} ({game.wscore} - {game.lscore})\n"
                    result += formatted_string
        return result

    def model_dump_json(self) -> str:
        data = self.model_dump(exclude={"games"})
        data["games"] = [json.loads(game.model_dump_json()) for game in self.games]
        data["cycle_names"] = self.cycle_names
        return json.dumps(data, default=str)
