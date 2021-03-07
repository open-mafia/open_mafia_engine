from .wincon import Wincon
from typing import Union
from pydantic import BaseModel, validator


class Alignment(BaseModel):
    """An alignment is basically a "team", that specifies a victory condition."""

    name: str
    wincon: Union[Wincon]  # str converts to Wincon

    _chk_wincon = validator("wincon", pre=True, always=True, allow_reuse=True)(
        Wincon.parse_single
    )
