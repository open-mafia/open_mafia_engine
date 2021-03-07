"""Loads all built-ins."""

__all__ = ["prefabs"]

from pathlib import Path

from open_mafia_engine.state.ability import Ability
from open_mafia_engine.state.constraint import Constraint
from open_mafia_engine.state.phase import Phase
from open_mafia_engine.state.prefab import Prefab
from open_mafia_engine.state.wincon import Wincon
from open_mafia_engine.util.yaml import load_yaml

from .ability import *  # noqa

_p = Path(__file__).parent

Ability.update_builtins(load_yaml(_p / "ability.yml"))
Constraint.update_builtins(load_yaml(_p / "constraint.yml"))
Phase.update_builtins(load_yaml(_p / "phase.yml"))
Wincon.update_builtins(load_yaml(_p / "wincon.yml"))

prefabs = {}
for _f in (_p / "prefab").glob("*.yml"):
    _pf = Prefab(**load_yaml(_f))
    prefabs[_pf.name] = _pf
