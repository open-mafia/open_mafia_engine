"""REST API (based on FastAPI) for the mafia game.

"""

import typing
from fastapi import FastAPI, Body, Depends, Security  # noqa
from fastapi.security import HTTPBasic, HTTPBasicCredentials  # noqas
from mafia.api.py import (
    Game,
    PyAPI,
    ActorInfo,
    AbilityInfo,
    AlignmentInfo,
    AbilityParameters,
)  # noqa


class RestAPI(FastAPI):
    def __init__(self, game: Game, **kwargs):
        super().__init__(**kwargs)
        self.py: PyAPI = PyAPI.with_full_access(game=game)
        self._assign_endpoints()

    def _assign_endpoints(self):
        api: PyAPI = self.py

        # Alignments
        self.get("/alignments")(api.get_alignment_names)
        self.get("/alignment/{alignment_name}")(self.get_alignment_info)
        self.get("/alignment/{alignment_name}/members")(self.get_alignment_member_names)

        # Actors
        self.get("/actors")(api.get_actor_names)
        self.get("/actors/alive")(self.get_alive_actor_names)
        self.get("/actor/{actor_name}")(self.get_actor_info)
        self.get("/actor/{actor_name}/{ability_name}")(self.get_ability_info)
        self.post("/actor/{actor_name}/{ability_name}")(self.use_actor_ability)

        # Game status
        self.get("/phases")(api.get_all_phase_names)
        self.get("/phase/current")(api.get_current_phase_name)

    def get_alive_actor_names(self) -> typing.List[str]:
        api = self.py
        actors_names = api.get_actor_names()
        res = []
        for name in actors_names:
            # TODO: Test for "aliveness"
            ai = self.get_actor_info(name)  # noqa
            if True:
                res.append(name)
        return res

    def get_actor_info(self, actor_name: str) -> ActorInfo:
        """Gets all information for a particular Actor."""

        api = self.py.actor(actor_name)
        alignment_names = api.get_alignment_names()
        ability_names = api.get_ability_names()
        all_abil_info = [api.get_ability_info(abil) for abil in ability_names]
        return ActorInfo(
            actor_name=actor_name,
            alignment_names=alignment_names,
            abilities=all_abil_info,
        )

    def get_ability_info(self, actor_name: str, ability_name: str) -> AbilityInfo:
        api = self.py.actor(actor_name)
        res = api.get_ability_info(ability_name=ability_name)
        return res

    def use_actor_ability(
        self, actor_name: str, ability_name: str, ability_args: AbilityParameters
    ):
        api = self.py.actor(actor_name)
        # NOTE: Will we be able to use kwargs???
        api.do_use_activated_ability(ability_name, **ability_args.parameters)

    def get_alignment_info(self, alignment_name: str) -> AlignmentInfo:
        """Gets info object for the given alignment.
        
        Required levels: [alignment_name]
        """
        api = self.py.alignment(alignment_name)
        res = AlignmentInfo(
            alignment_name=alignment_name, member_names=api.get_actor_names()
        )
        return res

    def get_alignment_member_names(self, alignment_name: str) -> typing.List[str]:
        """Gets members for the given alignment.
        
        Required levels: [alignment_name]
        """
        return self.py.alignment(alignment_name).get_actor_names()
