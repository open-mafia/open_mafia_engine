from typing import Dict
from open_mafia_engine.util.repr import ReprMixin


class GameObject(ReprMixin):
    """Base class for game objects."""
    

class GameState(ReprMixin):
    """Game state."""

    def __init__(self, objects: Dict[str, GameObject] = None):
        if objects is None:
            objects = {}
        self.objects: Dict[str, GameObject] = objects
