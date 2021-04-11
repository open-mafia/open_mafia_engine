"""This module tests built-in imports."""


def test_builtins():
    from open_mafia_engine.built_in.load import Ability, Constraint, Phase, Wincon

    Ability.parse_single("lynch_vote")
    Constraint.parse_single("alive")
    Phase.parse_single("day")
    Wincon.parse_single("survivor")
