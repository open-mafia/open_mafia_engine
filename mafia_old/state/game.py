"""State of the Mafia game.

This is heavily WIP. Technically, this should hold all info 
about current state, possibly including queued up actions. 
"""

from mafia.core import GameObject
from mafia.core.action import Action

# from mafia.core.event import EventManager


class PhaseChangeAction(Action):
    """Action that changes phases.
    
    Attributes
    ----------
    phase_state : PhaseState
        The target state that will be changed.
    new_phase : int
        The phase being changed to.
    """

    def __init__(self, phase_state, new_phase):
        self.phase_state = phase_state
        self.new_phase = new_phase

    @classmethod
    def next_phase(cls, phase_state):
        """Creates action that increments the phase (with wrap-around).
        
        Parameters
        ----------
        phase_state : PhaseState
            The target state that will be changed.
        """
        new_phase = (phase_state.current + 1) % len(phase_state.states)
        return cls(phase_state, new_phase)

    def _execute(self):
        self.phase_state.current = self.new_phase
        return True


class PhaseState(GameObject):
    """Specifies current "phase" of the game state and progression.
    
    Attributes
    ----------
    states : list
        List of phases. Defaults to `['day', 'night']`.
    current : int
        Index of current phase. Defaults to 0. 
    """

    def __init__(self, states=["day", "night"], current=0):
        states = list(states)
        self.current = current % len(states)
        self.states = states

    def __next__(self):
        self.try_change_phase()

    def try_change_phase(self, new_phase=None):
        """Attempts to change phase to new one.
        
        Parameters
        ----------
        new_phase : int or None
            The new phase. If None, tries to increment. 
        """

        if new_phase is None:
            action = PhaseChangeAction.next_phase(self)
        else:
            action = PhaseChangeAction(self, new_phase)
        action.execute()


class GameState(GameObject):
    """Object that records game state.
    
    Attributes
    ----------
    phase_state : PhaseState
        The game phase object. Typically day/night.
    alignments : list
        List of game :class:`Alignment`'s. Typically town/mafia/etc.
    """

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
