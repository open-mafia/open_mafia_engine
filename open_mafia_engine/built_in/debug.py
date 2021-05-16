"""Built-in objects that are debugging tools."""

from typing import Optional
import logging

from open_mafia_engine.core import Game, Event, Action, EStatusChange, AuxGameObject

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_hldr = logging.StreamHandler()
_hldr.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
_hldr.setLevel(logging.INFO)
logger.addHandler(_hldr)


class DebugNotifier(AuxGameObject):
    """Logs all events."""

    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, Event)

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        logger.info(f"EVENT: {type(event).__qualname__}")
        return None


class DebugMortician(AuxGameObject):
    """Logs death events."""

    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, EStatusChange)

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        if isinstance(event, EStatusChange):
            if event.key == "dead":
                logger.info(f"DEATH of {event.actor.name}")
        return None
