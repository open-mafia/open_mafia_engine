from open_mafia_engine.core.engine import Event, PostActionEvent, PreActionEvent  # noqa


class DeathEvent(Event):
    """The target is dead."""

    def __init__(self, target: str):
        self.target = target
