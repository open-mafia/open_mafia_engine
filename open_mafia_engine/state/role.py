from typing import List

from pydantic import BaseModel, validator

from open_mafia_engine.state.ability import Ability


class Role(BaseModel):
    """"""

    name: str
    desc: str = ""
    alignment: str
    abilities: List[Ability]

    _chk_abilities = validator(
        "abilities", pre=True, each_item=True, always=True, allow_reuse=True
    )(Ability.parse_single)
