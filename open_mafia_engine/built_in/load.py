"""Loads all built-ins."""

from pathlib import Path

from open_mafia_engine.core.ability import Ability
from open_mafia_engine.core.constraint import Constraint
from open_mafia_engine.util.yaml import load_yaml

Constraint.update_builtins(load_yaml(Path(__file__).parent / "constraint.yml"))
Ability.update_builtins(load_yaml(Path(__file__).parent / "ability.yml"))
