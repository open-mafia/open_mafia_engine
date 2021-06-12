from open_mafia_engine.builders.for_testing import make_test_game
from open_mafia_engine.core.game import Game
from open_mafia_engine.core.game_object import inject_converters
from open_mafia_engine.core.state import Actor


def test_fuzzy_actor_converter():
    """Tests fuzzy matching for Actor converter."""

    game = make_test_game(["Alice", "Bob"])

    @inject_converters
    def hey(game: Game, actor: Actor) -> str:
        return f"Hello, {actor.name}"

    assert hey(game, "alice") == "Hello, Alice"
