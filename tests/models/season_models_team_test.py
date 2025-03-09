from models import Team


def test_team_initialisation():
    team = Team(
        id=1, name="Team A", abbrev="TA", logo_url="http://example.com/logo.png"
    )
    assert team.id == 1
    assert team.name == "Team A"
    assert team.abbrev == "TA"
    assert team.logo_url == "http://example.com/logo.png"


def test_team_logo_filename():
    team = Team(
        id=1, name="Team A", abbrev="TA", logo_url="http://example.com/logo.png"
    )
    assert team.logo_filename == "logo.png"
