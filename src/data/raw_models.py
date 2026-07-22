from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True, slots=True)
class RawTeam:
    """the exact fields read off the Squiggle 'teams' API response, unconverted"""

    id: Any
    name: Any
    abbrev: Any
    logo: Any


@dataclass(frozen=True, slots=True)
class RawGameResult:
    """the exact fields read off the Squiggle 'games' API response, unconverted"""

    id: Any
    round: Any
    roundname: Any
    hteamid: Any
    ateamid: Any
    hscore: Any
    ascore: Any
    winnerteamid: Any
    hteam: Any
    ateam: Any
    winner: Any
    date: Any


def parse_raw_team(data: Dict[str, Any]) -> RawTeam:
    return RawTeam(
        id=data["id"],
        name=data["name"],
        abbrev=data["abbrev"],
        logo=data["logo"],
    )


def parse_raw_game(data: Dict[str, Any]) -> RawGameResult:
    return RawGameResult(
        id=data["id"],
        round=data["round"],
        roundname=data["roundname"],
        hteamid=data["hteamid"],
        ateamid=data["ateamid"],
        hscore=data["hscore"],
        ascore=data["ascore"],
        winnerteamid=data["winnerteamid"],
        hteam=data["hteam"],
        ateam=data["ateam"],
        winner=data["winner"],
        date=data["date"],
    )
