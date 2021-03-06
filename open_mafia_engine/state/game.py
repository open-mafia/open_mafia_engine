from __future__ import annotations

from typing import List, Union

from pydantic import parse_obj_as

from open_mafia_engine.built_in.load import prefabs
from open_mafia_engine.core.prefab import Prefab
from open_mafia_engine.state.actor import Actor

from .base import StateModel


class Game(StateModel):
    """Defines the entire state of a game.

    Attributes
    ----------
    actors : List[Actor]
        The various actor entities in the game.
    """

    actors: List[Actor]

    @classmethod
    def from_prefab(
        cls, names: List[str], prefab: Union[str, Prefab], variant: str = None
    ) -> Game:
        """Creates a game based on a prefab.

        Parameters
        ----------
        prefab : Prefab or str
            If a string, will select from built-in prefabs.
        names : list
            List of actor names to assign.
        variant : str
            The variant to use. If None, uses a random applicable variant.
        """

        names = parse_obj_as(List[str], names)
        n = len(names)

        if isinstance(prefab, str):
            if prefab not in prefabs:
                raise ValueError(f"Could not find prefab named {prefab!r}")
            return cls.from_prefab(names, prefab=prefabs[prefab], variant=variant)
        elif not isinstance(prefab, Prefab):
            prefab = Prefab(**prefab)

        gv = prefab.get_variant(name=variant, players=n)
        n2r = gv.assign_roles(names)

        actors = []
        for name, role_name in n2r.items():
            poss_roles = [r for r in prefab.roles if r.name == role_name]
            if len(poss_roles) != 1:
                raise ValueError("Could not determine a unique role.")
            role = poss_roles[0].copy(deep=True)
            actors.append(Actor(name=name, role=role))

        return cls(actors=actors)
