"""REST API (based on FastAPI) for the mafia game.

"""

import typing  # noqa
from fastapi import FastAPI, Body, Depends, Security  # noqa
from fastapi.security import HTTPBasic, HTTPBasicCredentials  # noqas
from mafia.api.py import PyAPI, Game


class RestAPI(FastAPI):
    """RESTful API server for Mafia games.
    
    This is based on (and inherits from) the :class:`FastAPI` class of FastAPI.

    Parameters
    ----------
    game : mafia.state.game.Game
        Main game object to keep track of.
    
    TODO
    ----
    Add (common) keyword arguments for FastAPI.
    """

    def __init__(self, game: Game, **kwargs):
        super().__init__(**kwargs)
        self.py_api: PyAPI = PyAPI.with_full_access(game=game)
        self._assign_endpoints()

    def _assign_endpoints(self):
        api: PyAPI = self.py_api

        # Alignments
        self.get("/alignments")(api.get_alignment_names)
        self.get("/alignment/{alignment_name}")(api.get_alignment_info)
        self.get("/alignment/{alignment_name}/members")(api.get_alignment_member_names)

        # Actors
        self.get("/actors")(api.get_actor_names)
        self.get("/actors/alive")(api.get_alive_actor_names)
        self.get("/actor/{actor_name}")(api.get_actor_info)
        self.get("/actor/{actor_name}/{ability_name}")(api.get_ability_info)
        self.post("/actor/{actor_name}/{ability_name}")(api.use_actor_ability)

        # Game status
        self.get("/phases")(api.get_all_phase_names)
        self.get("/phase/current")(api.get_current_phase_name)
