"""Tests for building games."""


def test_the_test_build():
    """Tests building the game."""

    from open_mafia_engine.builders.for_testing import test_builder  # noqa
    from open_mafia_engine.core.builder import GameBuilder

    builder = GameBuilder.load("test")
    game = builder.build(["Alice", "Bob"])
    assert game.actor_names == ["Alice", "Bob"]
