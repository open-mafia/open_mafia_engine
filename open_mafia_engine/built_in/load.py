"""Loads all built-ins."""

__all__ = ["prefabs"]

from pathlib import Path

from open_mafia_engine.core.ability import Ability
from open_mafia_engine.core.constraint import Constraint
from open_mafia_engine.core.phase import Phase
from open_mafia_engine.core.prefab import Prefab
from open_mafia_engine.core.wincon import Wincon
from open_mafia_engine.util.yaml import load_yaml

_p = Path(__file__).parent

Ability.update_builtins(load_yaml(_p / "ability.yml"))
Constraint.update_builtins(load_yaml(_p / "constraint.yml"))
Phase.update_builtins(load_yaml(_p / "phase.yml"))
Wincon.update_builtins(load_yaml(_p / "wincon.yml"))

prefabs = {}
for _f in (_p / "prefab").glob("*.yml"):
    _pf = Prefab(**load_yaml(_f))
    prefabs[_pf.name] = _pf
