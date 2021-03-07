from __future__ import annotations

from typing import Any, Dict, List, Union

from pydantic import parse_obj_as, validator

from open_mafia_engine.built_in.load import prefabs
from open_mafia_engine.state.actor import Actor
from open_mafia_engine.state.alignment import Alignment
from open_mafia_engine.state.phase import Phase
from open_mafia_engine.state.prefab import Prefab

from .base import StateModel


class GameState(StateModel):
    """Defines the entire state of a game.

    Attributes
    ----------
    alignments: List[Alignment]
        The alignments in the game.
    phases : List[Phase]
        The possible phases in the game.
    phase_num : int
        The current phase number. Default is 0.
    actors : List[Actor]
        The various actor entities in the game.
    status : Dict[str, Any]
        Current game status.
    """

    alignments: List[Alignment]
    phases: List[Phase]
    phase_num: int = 0
    actors: List[Actor]
    status: Dict[str, Any] = {}

    @property
    def current_phase(self) -> Phase:
        return self.phases[self.phase_num]

    @classmethod
    def from_prefab(
        cls, names: List[str], prefab: Union[str, Prefab], variant: str = None
    ) -> GameState:
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

        # Get phases and alignments directly from the prefab
        phases = prefab.phases
        alignments = prefab.alignments

        # Assign roles from the chosen variant
        gv = prefab.get_variant(name=variant, players=n)
        n2r = gv.assign_roles(names)
        actors = []
        for name, role_name in n2r.items():
            poss_roles = [r for r in prefab.roles if r.name == role_name]
            if len(poss_roles) != 1:
                raise ValueError("Could not determine a unique role.")
            role = poss_roles[0].copy(deep=True)
            actors.append(Actor(name=name, role=role))

        return cls(actors=actors, alignments=alignments, phases=phases)

    @validator("actors", always=True)
    def _chk_actor_names(cls, v):
        """Makes sures actors have unique names."""
        names = [a.name for a in v]
        if len(names) < len(set(names)):
            raise ValueError(f"Actor names contain duplicates: {names!r}")
        return v

    @validator("actors", always=True)
    def _chk_actor_alignments(cls, v, values):
        """Makes sures actor alignments exist."""
        al_names = [al.name for al in values.get("alignments")]
        for a in v:
            a: Actor
            al = a.role.alignment
            if al not in al_names:
                raise ValueError(f"Could not find alignment {al!r} from {al_names!r}")
        return v

    _chk_phases = validator(
        "phases", pre=True, always=True, each_item=True, allow_reuse=True
    )(Phase.parse_single)
