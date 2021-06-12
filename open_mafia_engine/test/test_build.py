"""Tests for building games."""

from open_mafia_engine.builders.for_testing import make_test_game
from open_mafia_engine.core.builder import GameBuilder


def test_builder_direct():
    """Tests the `test_builder()` function directly."""

    actor_names = ["Wendy", "Pickle"]
    game = make_test_game(actor_names)
    assert game.actor_names == actor_names


def test_builder_by_name():
    """Tests building the game."""
    from open_mafia_engine.builders.for_testing import make_test_game  # noqa

    builder = GameBuilder.load("test")
    game = builder.build(["Alice", "Bob"])
    assert game.actor_names == ["Alice", "Bob"]
