"""Python classes for interacting with

These present the API for interacting with the game."""

import typing
import inspect

from mafia.state.game import Game
from mafia.state.actor import Alignment, Actor
from mafia.state.access import AccessError
from mafia.core.ability import ActivatedAbility, TryActivateAbility  # Ability
from mafia.util import name_of, intersect

from mafia.api.models import (
    AbilityInfo,
    AbilityParameters,
    AlignmentInfo,
    ActorInfo,
)  # noqa


class PyAPI(object):
    """Python API for a Mafia game.
    
    Parameters
    ----------
    game : mafia.state.game.Game
        Main game object to interface to.
    access_levels : list
        List of strings representing access levels. 
        Defaults to ["public"].
    """

    def __init__(self, game: Game, access_levels: typing.List[str] = ["public"]):
        self.game = game
        self.access_levels = list(access_levels)

    @classmethod
    def with_full_access(cls, game: Game) -> "PyAPI":
        """Creates a PyAPI with full game access.
        
        Parameters
        ----------
        game : mafia.state.game.Game
            Main game object to interface to.
        """

        actor_names = list(name_of(a) for a in game.actors)
        align_names = list(name_of(a) for a in game.alignments)
        lvls = ["public", "game"] + actor_names + align_names
        return cls(game=game, access_levels=lvls)

    def get_alignment_names(self) -> typing.List[str]:
        """Returns sorted list of alignment names.
        
        Required levels: None
        """
        return sorted(name_of(a) for a in self.game.alignments)

    def get_actor_names(self) -> typing.List[str]:
        """Returns sorted list of actor (player) names.
        
        Required levels: None
        """
        return sorted(name_of(a) for a in self.game.actors)

    def do_start_game(self) -> None:
        """Starts the current game. Currently a no-op!
        
        Required levels: ['game']
        """
        if "game" not in self.access_levels:
            raise AccessError(required=["game"], given=self.access_levels)
        # TODO: Currently a No-Op

    def do_end_game(self) -> None:
        """Forcefully ends the current game. Currently a no-op!
        
        Required levels: ['game']
        """
        if "game" not in self.access_levels:
            raise AccessError(required=["game"], given=self.access_levels)
        # TODO: Currently a No-Op

    def alignment(self, alignment_name: str) -> "_AlignmentAPI":
        """Gets Alignment API helper."""

        al = [a for a in self.game.alignments if name_of(a) == alignment_name]
        if len(al) == 0:
            raise KeyError("No such alignment: %r" % alignment_name)
        return _AlignmentAPI(self, al[0])

    def actor(self, actor_name: str) -> "_ActorAPI":
        """Gets Actor API helper."""

        ac = [a for a in self.game.actors if name_of(a) == actor_name]
        if len(ac) == 0:
            raise KeyError("No such actor: %r" % actor_name)
        return _ActorAPI(self, ac[0])

    def get_current_phase_name(self) -> str:
        """Returns current phase name.
        
        Required access levels: None
        """
        phase_state = self.game.status.phase.value
        return phase_state.current

    def get_all_phase_names(self) -> typing.List[str]:
        """Returns all possible phase names in list, sorted by internal order.
        
        Required access levels: None
        """
        phase_state = self.game.status.phase.value
        return list(str(s) for s in phase_state.states)

    def get_alignment_info(self, alignment_name: str) -> AlignmentInfo:
        """Gets info object for the given alignment.
        
        Required levels: [alignment_name]
        """
        api = self.alignment(alignment_name)
        res = AlignmentInfo(
            alignment_name=alignment_name, member_names=api.get_actor_names()
        )
        return res

    def get_alignment_member_names(self, alignment_name: str) -> typing.List[str]:
        """Gets members for the given alignment.
        
        Required levels: [alignment_name]
        """
        return self.alignment(alignment_name).get_actor_names()

    def get_actor_info(self, actor_name: str) -> ActorInfo:
        """Gets all information for a particular Actor."""

        api = self.actor(actor_name)
        alignment_names = api.get_alignment_names()
        ability_names = api.get_ability_names()
        all_abil_info = [api.get_ability_info(abil) for abil in ability_names]
        return ActorInfo(
            actor_name=actor_name,
            alignment_names=alignment_names,
            abilities=all_abil_info,
        )

    def get_ability_info(self, actor_name: str, ability_name: str) -> AbilityInfo:
        """Gets information for a particular Ability of an Actor.

        Parameters
        ----------
        actor_name : str
            Name of the :class:`Actor` (player) to inspect.
        ability_name : str
            Name of the :class:`Ability` to inspect.
        
        Returns
        -------
        AbilityInfo
            Pydantic model for ability information.
        """
        api = self.actor(actor_name)
        res = api.get_ability_info(ability_name=ability_name)
        return res

    def use_actor_ability(
        self, actor_name: str, ability_name: str, ability_args: AbilityParameters
    ):
        """Makes an Actor use one of their ActivatedAbility's (with the passed parameters).
        
        Parameters
        ----------
        actor_name : str
            Name of the :class:`Actor` (player) that will be performing the action.
        ability_name : str
            Name of the :class:`ActivatedAbility` to use.
        ability_args : AbilityParameters
            Parameters to pass to the ability. 
            Currently, just uses `ability_args.parameters` as keyword arguments.
        """
        api = self.actor(actor_name)
        # NOTE: Will we be able to use kwargs???
        api.do_use_activated_ability(ability_name, **ability_args.parameters)

    def get_alive_actor_names(self) -> typing.List[str]:
        """Gets list of actors that are currently alive.
        
        TODO
        ----
        Implement!
        """
        actors_names = self.get_actor_names()
        res = []
        for name in actors_names:
            # TODO: Test for "aliveness"
            ai = self.get_actor_info(name)  # noqa
            if True:
                res.append(name)
        return res


class _AlignmentAPI(object):
    """Helper object for Alignment API."""

    def __init__(self, parent: PyAPI, alignment: Alignment):
        self.parent = parent
        self.alignment = alignment

    @property
    def game(self):
        return self.parent.game

    @property
    def access_levels(self) -> typing.List[str]:
        return self.parent.access_levels

    def get_member_names(self) -> typing.List[str]:
        """Returns sorted list of actor (player) names for this Alignment.
        
        Required levels: [alignment.name]

        TODO
        ----
        Add alignments that let you see other members. Maybe a flag?...
        """
        al_name = name_of(self.alignment)
        if al_name not in self.access_levels:
            raise AccessError(required=[al_name], given=self.access_levels)
        return sorted(name_of(a) for a in self.alignment.members)

    def actor(self, actor_name: str) -> "_ActorAPI":
        """Gets Actor API helper, only for a member."""

        ac = [a for a in self.alignment.members if name_of(a) == actor_name]
        if len(ac) == 0:
            raise KeyError(
                "Alignment %r has no such actor: %r"
                % (name_of(self.alignment), actor_name)
            )
        return _ActorAPI(self.parent, ac[0])


class _ActorAPI(object):
    """Helper object for Actor API."""

    def __init__(self, parent: PyAPI, actor: Actor):
        self.parent = parent
        self.actor = actor

    @property
    def game(self) -> Game:
        return self.parent.game

    @property
    def access_levels(self) -> typing.List[str]:
        return self.parent.access_levels

    def alignment(self, alignment_name: str) -> "_AlignmentAPI":
        """Gets Alignment API helper, only for own alignments."""

        al = [a for a in self.actor.alignments if name_of(a) == alignment_name]
        if len(al) == 0:
            raise KeyError(
                "Actor %r has no such alignment: %r"
                % (name_of(self.actor), alignment_name)
            )
        return _AlignmentAPI(self.parent, al[0])

    def get_alignment_names(self) -> typing.List[str]:
        """Returns sorted list of alignment names for this Actor.
        
        Required levels: [actor.name]

        TODO
        ----
        Maybe allow co-members to see subset of alignments?...
        """
        required = [name_of(self.actor)]
        if not intersect(required, self.access_levels):
            raise AccessError(required=required, given=self.access_levels)
        return sorted(name_of(a) for a in self.actor.alignments)

    def get_ability_names(self) -> typing.List[str]:
        """Returns list of ability names.
        
        Required levels: [actor.name]
        """
        return sorted(name_of(a) for a in self.actor.abilities)

    def get_ability_info(self, ability_name: str) -> AbilityInfo:
        """Gets information for the given ability.
        
        Raises
        ------
        KeyError
            If no such ability (for this actor) has that name.
        """

        abil = self.actor.get_ability_by_name(ability_name)
        sig = inspect.signature(abil.activate)

        res = AbilityInfo(
            ability_name=name_of(abil),
            is_activated=isinstance(abil, ActivatedAbility),
            py_signature=str(sig),
            parameters=list(sig.parameters),
            py_type=str(type(abil)),
            docstring=abil.__doc__,
        )
        return res

    def do_use_activated_ability(
        self, ability_name: str, **kwargs: typing.Dict[str, str]
    ):
        """Uses an activated ability given the keyword arguments.

        Parameters
        ----------
        ability_name : str
            The name of the ability you want to use.
        kwargs : dict
            Keyword arguments for the activated ability.
            Note that string arguments are attempted to be converted to 
            first player names, then alignment names. If those fail, then 
            we fall back to using the string representation.

        Notes
        -----
        Problems that had to be solved:
        
        * How do you send extra information (e.g. a target) without actually 
            sending an Actor object? (Answer: search for it by name.)
        
        * How do you actually execute the action? 
            (Answer: :meth:`game.handle_event`)
        """
        game = self.game

        abil = self.actor.get_ability_by_name(ability_name)
        if not isinstance(abil, ActivatedAbility):
            raise TypeError("Ability is not an activated ability.")

        # Create new keyword arguments
        new_kw = {}
        for key, val in kwargs.items():
            if isinstance(val, str):
                # search for actor or alignment with the given name
                try:
                    actor = game.get_actor_by_name(val)
                    val = actor
                except KeyError:
                    try:
                        align = game.get_alignment_by_name(val)
                        val = align
                    except KeyError:
                        # Give up, use string
                        val = val
            new_kw[key] = val

        # Create and handle event with new kwargs
        tae = TryActivateAbility(abil, **new_kw)
        game.handle_event(tae)


# TODO: Add API for vote tally or other stuff!
# class VoteTallyAPI(AccessAPI):
#     """API for a VoteTally."""

#     def __init__(
#         self, _parent: "VoteTally", access_levels: typing.List[str] = ["public"]
#     ):
#         super().__init__(_parent=_parent, access_levels=access_levels)

#     def get_vote_leader_names(self) -> typing.List[str]:
#         """Gets list of players with the current most votes."""
#         return [name_of(itm) for itm in self._parent.vote_leaders]

#     def get_current_votes(self) -> typing.Dict[str, typing.List[str]]:
#         """Gets list of players with the current most votes."""
#         res = {}
#         for k, v in self._parent.votes_for.items():
#             source = name_of(k)
#             targets = [name_of(x) for x in v]
#             res[source] = targets
#         return res

#     def get_who_voted_for(self, target: str) -> typing.List[str]:
#         """Gets list of votes for the target."""
#         vb = self._parent.voted_by
#         t_cand = [x for x in vb if name_of(x) == target]
#         if len(t_cand) == 0:
#             return []
#         elif len(t_cand) > 1:
#             warnings.warn(
#                 AmbiguousName(
#                     f"Found {len(t_cand)} candidates with the same name: {target}, "
#                     f"selecting first one of {t_cand}."
#                 )
#             )
#         t = t_cand[0]
#         return [name_of(x) for x in vb[t]]
