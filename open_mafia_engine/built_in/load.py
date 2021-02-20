"""Loads all built-ins."""

from pathlib import Path

from open_mafia_engine.core.ability import Ability
from open_mafia_engine.core.constraint import Constraint
from open_mafia_engine.core.phase import Phase
from open_mafia_engine.core.wincon import Wincon
from open_mafia_engine.util.yaml import load_yaml

Ability.update_builtins(load_yaml(Path(__file__).parent / "ability.yml"))
Constraint.update_builtins(load_yaml(Path(__file__).parent / "constraint.yml"))
Phase.update_builtins(load_yaml(Path(__file__).parent / "phase.yml"))
Wincon.update_builtins(load_yaml(Path(__file__).parent / "wincon.yml"))
