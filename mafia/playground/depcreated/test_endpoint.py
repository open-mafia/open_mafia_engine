"""Test FastAPI endpoint."""

import typing
import logging

logging.basicConfig(level=logging.INFO)  # noqa


from mafia.state.access import AccessError

# from mafia.api.py import PyAPI, AbilityInfo, ActorInfo, AlignmentInfo

from mafia.playground.test_stuff import *  # noqa
from mafia.playground.test_stuff import game


from fastapi import FastAPI, Depends, Security  # noqa
from pydantic import BaseModel

# from fastapi.security import OAuth2PasswordBearer
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


# game, lynch_tally, phase_state, mafia_kill_tracker,
# Alignment: mafia, town, etc.
# Players: mod, a - g
# Non-API functions: vote, mafiakill, change_phase, print_status

gg = game.api  # TODO: Remove references to "gg"
# pyapi = PyAPI(game)

app = FastAPI(
    title="Test Endpoint",
    description="This is for testing what needs to be in a FastAPI endpoint.",
    swagger_js_url="",
    swagger_css_url="",
)


@app.get("/")
async def index():
    return "Hello World."


class PlayerInfo(BaseModel):
    alignment_name: str = "???"
    abilities: dict = {}
    status: dict = {}


class TeamInfo(BaseModel):
    name: str
    players: typing.List[str] = []


def current_player(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    return credentials.username


@app.get("/players")
async def get_players_list() -> typing.List[str]:
    """Returns list of all players."""
    return gg.get_actor_names()


@app.get("/player/{selected_player}/")
async def get_player_info(
    selected_player: str, me: str = Depends(current_player)
) -> PlayerInfo:
    """Gets information on a player."""

    result = PlayerInfo()

    a_api = gg.get_actor_api(selected_player)(["public", me])

    # Get alignment
    try:
        aligns = a_api.get_alignment_names()
        if len(aligns) == 0:
            result.alignment_name = "none"
        else:
            result.alignment_name = aligns[0]
    except AccessError:
        result.alignment_name = "???"

    #
    try:
        result.abilities = a_api.get_ability_info_all()
    except AccessError:
        pass

    # Get status
    for key in a_api.get_status_keys():
        try:
            result.status[key] = a_api.get_status_value(key)
        except AccessError:
            pass

    return result


@app.get("/teams")
async def get_team_names() -> typing.List[str]:
    """Gets names of all available teams."""
    return gg.get_alignment_names()


@app.get("/team/{team_name}/")
async def get_team_info(team_name: str) -> TeamInfo:
    """Gets information on a specific team."""

    al_api = gg.get_alignment_api(team_name)(["public", team_name])
    members = al_api.get_actor_names()
    return TeamInfo(name=team_name, players=members)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
