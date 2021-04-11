from typing import List

from pydantic import BaseModel, validator

from open_mafia_engine.state.ability import Ability


class Role(BaseModel):
    """Role definition.

    Attributes
    ----------
    name : str
    desc : str
    alignment : str
        The role's alignment (e.g. team, faction).
    abilities : List[Ability]
        The role's abilities.
    """

    name: str
    desc: str = ""
    alignment: str
    abilities: List[Ability]

    _chk_abilities = validator(
        "abilities", pre=True, each_item=True, always=True, allow_reuse=True
    )(Ability.parse_single)

    def ability_by_name(self, name: str) -> Ability:
        """Returns the ability with the given name."""

        x = [a for a in self.abilities if a.name == name]
        if len(x) != 1:
            raise ValueError(f"Could not determine ability for name {name!r}")
        return x[0]
