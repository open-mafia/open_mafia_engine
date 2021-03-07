from typing import Dict, List
from pydantic import BaseModel, validator
from pydantic.class_validators import root_validator
import random

from .alignment import Alignment
from .phase import Phase
from .role import Role


class RoleQty(BaseModel):
    """Defines how many of a given role to add in a game variant.

    At least one of `qty` and `prob` must be positive.

    Attributes
    ----------
    name : str
        The role name.
    qty : int
        How many of this role are guaranteed. Default is 0.
    prob : float
        Weight of this role being added (can be >1). Default is 0.
    """

    name: str  # role name
    qty: int = 0
    prob: float = 0

    @validator("qty", always=True)
    def _chk_qty(cls, v):
        if v < 0:
            raise ValueError(f"qty >= 0 if given, got {v!r}")
        return v

    @validator("prob", always=True)
    def _chk_prob(cls, v):
        if v < 0:
            raise ValueError(f"prob >= 0 if given, got {v!r}")
        return v

    @root_validator
    def _chk_all(cls, values):
        qty = values.get("qty")
        prob = values.get("prob")
        if (qty == 0) and (prob == 0):
            raise ValueError("At least one of `qty` or `prob` must be set.")
        return values


class GameVariant(BaseModel):
    """One variant of the game, with role counts, for a specific number of players.

    Attributes
    ----------
    name : str
        The name of the variant (will be used to look it up).
    role_counts : list
        How many of each role will be added (possibly randomly).
        See the `RollQty` class for more details.
    players : int
        How many players can be supported. If all quantities are deterministic,
        this can be inferred, but it's best to specify anyways.
    """

    name: str
    roles_counts: List[RoleQty]
    players: int = None

    def assign_roles(self, names: List[str]) -> Dict[str, str]:
        """Assigns roles of this variant to the given (player) names."""

        n = len(names)
        if len(names) != self.players:
            raise ValueError(f"Require {self.players} players, but got {n}.")

        # Select roles to use
        guaranteed = []
        randomized = []
        probs = []
        for rq in self.roles_counts:
            guaranteed += [rq.name] * rq.qty
            randomized.append(rq.name)
            probs.append(rq.prob)
        n_g = len(guaranteed)

        # Sample what roles will be used, then shuffle to map them to names
        roles = random.sample(guaranteed, k=n_g)
        roles += random.choices(randomized, probs, k=n - n_g)
        random.shuffle(roles)
        res = {n: r for (n, r) in zip(names, roles)}
        return res

    @validator("players", always=True)
    def _chk_qty(cls, v, values):

        players = v
        roles_counts = values.get("roles_counts")

        # If deterministic, we can figure out how many players there should be
        if sum(rc.prob for rc in roles_counts) == 0:
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

    def get_variant(self, name: str = None, players: int = None) -> GameVariant:
        """Finds the variant given a name or player count."""
        if name is None:
            if players is None:
                raise ValueError("Require at least one of `name` or `players`.")
            available = [gv for gv in self.game_variants if gv.players == players]
            if len(available) == 0:
                raise ValueError(f"No variants found for {players} players.")
            return random.choice(available)
        for gv in self.game_variants:
            if gv.name == name:
                return gv
        raise ValueError(f"No variant found for name={name!r} and players={players!r}")

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
