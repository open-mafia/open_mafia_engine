from open_mafia_engine.core.engine import (
    Subscriber,
    Event,
    PreActionEvent,
    ActionContext,
    Action,
)
from open_mafia_engine.built_in.action import CancelAction
from open_mafia_engine.state.game import GameState


def test_cancellation():
    class FakeAction(Action):
        def __call__(self, game, context: ActionContext) -> None:
            pass

    class TstCancel(Subscriber):
        def respond(self, e: Event):
            if isinstance(e, PreActionEvent):
                if isinstance(e.action, FakeAction):
                    return CancelAction(target=e.action)

    game = GameState(actors=[])

    tc = TstCancel()
    tc.subscribe_current(PreActionEvent)

    context = ActionContext()
    context.enqueue(FakeAction())
    context.process(game=game)
    assert len(context.history) == 1


if __name__ == "__main__":
    test_cancellation()
