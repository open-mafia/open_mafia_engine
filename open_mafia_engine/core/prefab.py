from typing import List, Union, Optional
from pydantic import BaseModel, validator
from pydantic.class_validators import root_validator

from .alignment import Alignment
from .phase import Phase
from .role import Role


class RoleQty(BaseModel):
    """Defines how many of a given role to add in a game variant.

    At least one of `qty` and `prob` must be given and nonnegative.
    """

    name: str  # role name
    qty: Optional[int] = None
    prob: Optional[float] = None

    @validator("qty")
    def _chk_qty(cls, v):
        if v is None:
            return None
        elif v < 0:
            raise ValueError(f"qty >= 0 if given, got {v!r}")
        return v

    @validator("prob")
    def _chk_prob(cls, v):
        if v is None:
            return None
        elif v < 0:
            raise ValueError(f"prob >= 0 if given, got {v!r}")
        return v

    @root_validator
    def _chk_all(cls, values):
        qty = values.get("qty")
        prob = values.get("prob")
        if (qty is None) and (prob is None):
            raise ValueError("At least one of `qty` or `prob` must be set.")
        return values


class GameVariant(BaseModel):
    """One variant of the game, with role counts, for a specific number of players."""

    name: str
    roles_counts: List[RoleQty]
    players: int = None

    @validator("players", always=True)
    def _chk_qty(cls, v, values):

        players = v
        roles_counts = values.get("roles_counts")

        # If deterministic, we can figure out how many players there should be
        if all(rc.prob is None for rc in roles_counts):
            n = sum(rc.qty for rc in roles_counts)
        else:
            n = None

        # Check if None, and set if needed
        if players is None:
            if n is None:
                raise ValueError("Can't estimate player count from roles counts.")
            else:
                players = n

        if players != n:
            raise ValueError(f"Set {players} players, but role counts sum to {n}")
        if players <= 1:
            raise ValueError(f"At least 2 players are required, got {v}")
        return players


class Prefab(BaseModel):
    """Pre-fabricated mafia 'setup', i.e. template game."""

    name: str
    version: str  # Meant to be a schema version or an object version?
    phases: List[Phase]
    alignments: List[Alignment]
    roles: List[Role]
    game_variants: List[GameVariant]

    _chk_phases = validator(
        "phases", pre=True, always=True, each_item=True, allow_reuse=True
    )(Phase.parse_single)

    @validator("alignments", always=True, each_item=True)
    def _chk_alignments(cls, v):
        # Pre-built alignments are difficult to add, due to wincon interaction
        return v

    @validator("roles", always=True, each_item=True)
    def _chk_roles(cls, v):
        # Pre-built roles are hard to add, due to alignments being hard to add
        return v

    @validator("game_variants", each_item=True)
    def _chk_variant(cls, v: GameVariant, values):
        # Most checks are already done in the GameVariant object itself

        # Check if roles in the variant are actually defined
        roles: List[Role] = values.get("roles")
        role_names: List[Role] = [r.name for r in roles]
        for rc in v.roles_counts:
            if rc.name not in role_names:
                raise ValueError(f"Role {v.name!r} not found in {role_names}")

        return v