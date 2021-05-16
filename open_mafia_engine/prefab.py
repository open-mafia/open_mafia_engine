from __future__ import annotations

import logging
import random
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Type, Union

from pydantic import BaseModel, root_validator, validator
from pydantic_yaml import YamlModel

from open_mafia_engine.core import (
    Ability,
    AbstractPhaseCycle,
    ActivatedAbility,
    Actor,
    Alignment,
    AuxGameObject,
    Constraint,
    Game,
    get_type,
)
from open_mafia_engine.util.yaml import load_yaml

default_search_paths: List[Path] = [Path(__file__).parent / "prefabs"]
logger = logging.getLogger(__name__)


class XModel(BaseModel):
    """Base class for classes used in prefabs."""

    class Config:
        allow_mutation = False


class XPhaseCycle(XModel):
    """Cycle definition. Defaults to a default SimplePhaseCycle."""

    type: str = "SimplePhaseCycle"
    params: Dict[str, Any] = {}

    @validator("type", always=True)
    def _chk_type(cls, v):
        T = get_type(v)
        if not issubclass(T, AbstractPhaseCycle):
            raise ValueError(f"Is not an AbstractPhaseCycle subclass: {v!r}")
        return v

    @property
    def T(self) -> Type[AbstractPhaseCycle]:
        return get_type(self.type)


class XAlignment(XModel):
    """Alignment definition."""

    name: str
    # TODO: wincons


class XConstraint(XModel):
    """Ability usage constraint."""

    type: str
    params: Dict[str, Any] = {}

    @validator("type", always=True)
    def _chk_type(cls, v):
        T = get_type(v)
        if not issubclass(T, Constraint):
            raise ValueError(f"Is not a Constraint subclass: {v!r}")
        return v

    @property
    def T(self) -> Type[Constraint]:
        return get_type(self.type)


class XAbility(XModel):
    """Ability definition."""

    # TODO: Add descriptions
    name: str
    type: str
    params: Dict[str, Any]
    constraints: List[XConstraint] = []

    @validator("type", always=True)
    def _chk_type(cls, v):
        T = get_type(v)
        if not issubclass(T, Ability):
            raise ValueError(f"Is not an Ability subclass: {v!r}")
        return v

    @property
    def T(self) -> Type[Ability]:
        return get_type(self.type)


class XRole(XModel):
    """A role (Actor prototype)."""

    name: str
    # TODO: descriptions
    alignments: List[str] = []  # can also do a single str, which will be normalized
    abilities: List[XAbility] = []

    @validator("alignments", pre=True)
    def _chk_single_alignment(cls, v):
        """Allow alignments to be a single string, for 1 alignment (as typical)."""
        if isinstance(v, str):
            return [v]
        elif v is None:
            return []
        return v

    @validator("abilities", always=True)
    def _chk_abils(cls, v, values):
        if len(v) == 0:
            warnings.warn(f"No abilities specified for {values['name']!r}")
        names = [a.name for a in v]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate ability names found: {v!r}")
        return v


class XAux(XModel):
    """Auxiliary objects."""

    # TODO: Add name and descriptions?
    type: str
    params: Dict[str, Any]

    @validator("type", always=True)
    def _chk_type(cls, v):
        T = get_type(v)
        if not issubclass(T, AuxGameObject):
            raise ValueError(f"Is not an AuxGameObject subclass: {v!r}")
        return v

    @property
    def T(self) -> Type[AuxGameObject]:
        return get_type(self.type)


class RoleQty(BaseModel):
    """Defines how many of a given role to add in a game variant.

    At least one of `guaranteed` and `extra_weight` must be positive.

    Attributes
    ----------
    name : str
        The role name.
    guaranteed : int
        How many of this role are guaranteed. Default is 0.
    extra_weight : float
        Weight of this role being added (can be >1). Default is 0.
    """

    name: str  # role name
    guaranteed: int = 0
    extra_weight: float = 0

    @validator("guaranteed", always=True)
    def _chk_qty(cls, v):
        if v < 0:
            raise ValueError(f"guaranteed >= 0 if given, got {v!r}")
        return v

    @validator("extra_weight", always=True)
    def _chk_prob(cls, v):
        if v < 0:
            raise ValueError(f"extra_weight >= 0 if given, got {v!r}")
        return v

    @root_validator
    def _chk_all(cls, values):
        guaranteed = values.get("guaranteed")
        extra_weight = values.get("extra_weight")
        if (guaranteed == 0) and (extra_weight == 0):
            raise ValueError(
                "At least one of `guaranteed` or `extra_weight` must be set."
            )
        return values


class GameVariant(BaseModel):
    """One variant of the game, with role counts, for a specific number of players.

    Attributes
    ----------
    name : str
        The name of the variant (will be used to look it up).
    role_counts : list or dict
        How many of each role will be added (possibly randomly).
        If given as a dict, maps the role name to their guaranteed quantity.
        See the `RollQty` class for more details.
    players : int
        How many players can be supported. If all quantities are deterministic,
        this can be inferred, but it's best to specify anyways.
    """

    name: str
    role_counts: List[RoleQty]
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
        for rq in self.role_counts:
            guaranteed += [rq.name] * rq.guaranteed
            randomized.append(rq.name)
            probs.append(rq.extra_weight)
        n_g = len(guaranteed)

        # Sample what roles will be used, then shuffle to map them to names
        roles = []
        if n_g > 0:
            roles += random.sample(guaranteed, k=n_g)
        if n > n_g:
            roles += random.choices(randomized, probs, k=n - n_g)
        random.shuffle(roles)
        res = {n: r for (n, r) in zip(names, roles)}
        return res

    @validator("role_counts", pre=True)
    def _role_dict(cls, v):
        """Converts a dict into list of guaranteed roles."""
        if isinstance(v, dict):
            v = [RoleQty(name=key, guaranteed=val) for key, val in v.items()]
        return v

    @validator("players", always=True)
    def _chk_qty(cls, v, values) -> int:
        """Checks (and possibly sets) quantity of players."""

        players = v
        role_counts = values.get("role_counts")

        # If deterministic, we can figure out how many players there should be
        if sum(rc.extra_weight for rc in role_counts) == 0:
            n = sum(rc.guaranteed for rc in role_counts)
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


class Prefab(YamlModel):
    """Template for a game.

    Parameters
    ----------
    version : str
    name : str
    phases : XPhaseCycle
        By default, uses day and night phases.
    alignments : List[XAlignment]
        Specify all alignments.
    roles : List[XRole]
        Specify all roles, including constraints.
    aux : List[XAux]
    variants : GameVariant
        Different variants of this game prefab.
    """

    version: str
    name: str
    phases: XPhaseCycle = XPhaseCycle()
    alignments: List[XAlignment]
    roles: List[XRole]
    aux: List[XAux] = []  # TODO
    variants: List[GameVariant]

    def create_game(
        self, player_names: List[str], variant: Union[None, str, GameVariant] = None
    ) -> Game:
        """Creates a game from the player name list.

        Parameters
        ----------
        player_names : List[str]
            Player names, which will become the Actor names.
        variant : None or str or GameVariant
            Which variant to select.
            If None, will select a random variant with the same number of players.
        """
        N = len(player_names)
        if variant is None:
            possible_variants = [v for v in self.variants if v.players == N]
            if len(possible_variants) == 0:
                raise ValueError(f"No variants available for {N} players.")
            elif len(possible_variants) > 1:
                logger.info(f"Selecting a variant from {possible_variants}")
            variant = random.choice(possible_variants)
        elif isinstance(variant, str):
            found = [v for v in self.variants if v.name == variant]
            if len(found) == 0:
                raise ValueError(f"No such variant found: {variant!r}")
            variant = found[0]
        elif isinstance(variant, GameVariant):
            if variant not in self.variants:
                warnings.warn(
                    "Passed variant is not one of the included ones!"
                    " Proceeding, but this may be risky."
                )
        else:
            raise TypeError(f"Expected None, str or GameVariant, got {variant!r}")

        # Finalize what role each player is getting
        variant: GameVariant
        role_map = variant.assign_roles(player_names)

        # Now for the fun stuff!
        game = Game()

        # Add alignments
        alignments = {}
        for xal in self.alignments:
            # automatically attaches to the game
            alignments[xal.name] = Alignment(game, name=xal.name)

        # Add actors
        actors = {}
        for actor_name, role_name in role_map.items():
            xrole = [r for r in self.roles if r.name == role_name][0]
            my_aligns = [alignments[alname] for alname in xrole.alignments]
            # automatically attaches to the game and alignments
            actors[actor_name] = act = Actor(
                game, name=actor_name, alignments=my_aligns
            )
            # Add abilities to the actor
            for xabil in xrole.abilities:
                # automatically attaches to owner
                abil = xabil.T(owner=act, name=xabil.name, **xabil.params)
                for xcon in xabil.constraints:
                    # automatically attaches to parent
                    con = xcon.T(parent=abil, **xcon.params)

        # Add aux things to the game
        for xaux in self.aux:
            aux = xaux.T(**xaux.params)
            game.aux.add(aux)

        return game

    @validator("alignments", always=True)
    def _chk_duplicate_names(cls, v):
        names = [x.name for x in v]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate alignment found: {names!r}")
        return v

    @validator("roles", always=True, each_item=True)
    def _chk_role_alignments(cls, v: XRole, values):
        anames = set(a.name for a in values["alignments"])
        for aname in v.alignments:
            if aname not in anames:
                raise ValueError(f"Alignment {aname!r} not found in {anames!r}")
        return v

    @validator("roles", always=True)
    def _chk_role_names(cls, v: List[XRole]):
        """Make sure role names are unique."""
        names = [r.name for r in v]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate role names found: {names}")
        return v

    @validator("variants", each_item=True)
    def _chk_variant(cls, v: GameVariant, values):
        """Make sure the variant's roles are actually in the game."""
        role_names: List[str] = [r.name for r in values["roles"]]
        for rc in v.role_counts:
            if rc.name not in role_names:
                raise ValueError(f"Role {rc.name!r} not found in {role_names}")
        return v

    @classmethod
    def load(cls, name: str, *, extra_search_paths: List[Path] = None):
        """Loads the prefab given the name.

        Parameters
        ----------
        name : str
            Either a file name (with ".yml" or ".yaml" ending) or a prefab name.
            Note that giving a prefab name will require loading ALL possible
            yaml files in the search paths!
        extra_search_paths : List[Path]
            List of paths to search for prefabs in.
        """

        if extra_search_paths is None:
            extra_search_paths = []
        else:
            extra_search_paths = [Path(x).resolve() for x in extra_search_paths]
        search_paths = default_search_paths + extra_search_paths

        found_files = []
        if (".yml" in name) or (".yaml" in name):
            # Look for the file name
            for sp in search_paths:
                found_files += list(sp.rglob(name))
        else:
            # Find all possible files (e.g. yaml files)
            possible_files = []
            for sp in search_paths:
                possible_files += list(sp.rglob("*.yml")) + list(sp.rglob("*.yaml"))

            # Look for prefab name key within these files (ignore if it doesn't parse)
            for pf in possible_files:
                try:
                    z = load_yaml(pf)
                    if z["name"] == name:
                        found_files.append(pf)
                except Exception:
                    pass

        if len(found_files) == 0:
            raise ValueError(f"Could not find prefab with file name {name!r}")
        elif len(found_files) > 1:
            raise ValueError(f"Multiple files found: {found_files}")
        return cls.load_file(found_files[0])

    @classmethod
    def load_file(cls, file: Union[Path, TextIO, str]) -> Prefab:
        """Loads the prefab from a given file (either Path, open file, or YAML text)."""

        if isinstance(file, Path):
            with file.open(mode="r") as f:
                txt = f.read()
        elif isinstance(file, str):
            txt = file
        else:
            txt = file.read()
        return cls.parse_raw(txt, content_type="application/yaml")


if __name__ == "__main__":

    pf = Prefab.load("vanilla.yml")
    # Other ways:
    # yp = Path(__file__).parent / "vanilla.yml"
    # pf = Prefab.parse_file(yp, content_type="application/yaml")
    # pf = Prefab(**load_yaml(yp))
    print("Loaded prefab:", pf.name)
    game = pf.create_game(list("ABCDE"))
