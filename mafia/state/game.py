"""State of the Mafia game.

This is heavily WIP. Technically, this should hold all info 
about current state, possibly including queued up actions. 
"""

from mafia.core import GameObject
from mafia.core.action import Action


class PhaseChangeAction(Action):
    """Base class for `PhaseState` update events."""

    def __init__(self, phase_state, new_phase):
        self.phase_state = phase_state
        self.new_phase = new_phase

    @classmethod
    def next_phase(cls, phase_state):
        """Increments the phase (with wrap-around)."""
        new_phase = (phase_state.current + 1) % len(phase_state.states)
        return cls(phase_state, new_phase)

    def _execute(self):
        self.phase_state.current = self.new_phase
        

class PhaseState(GameObject):
    """Specifies current "phase" of the game state and progression."""

    def __init__(self, states=[], current=0):
        states = list(states)
        if len(states) == 0:
            states = ['unset']
        self.current = current % len(states) 
        self.states = states 


class GameState(GameObject):
    """Object that records game state."""

    def __init__(self, phase_state, alignments=[]):
        super().__init__()
        self.phase_state = phase_state 
        self.alignments = list(alignments)

    @property
    def actors(self):
        """Returns all actor objects."""
        res = set()
        for align in self.alignments:
            res = res.union(align.members)
        return sorted(res, key=lambda x: x.ID) 
