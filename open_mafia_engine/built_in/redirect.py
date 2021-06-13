from typing import List, Optional
import warnings
from open_mafia_engine.core.all import (
    Ability,
    Action,
    ActionInspector,
    Actor,
    ATBase,
    EPreAction,
    Game,
    GameObject,
    handler,
)
from open_mafia_engine.util.matcher import FuzzyMatcher

from .auxiliary import TempPhaseAux


class BaseRedirectAction(Action):
    """Action that redirects another action to a new target.

    Note that actions can have multiple targets.
    This redirects the one closest to `field_name`
    """

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: Action,
        new_target: GameObject,
        field_name: str = "target",
        *,
        priority: float = 50.0,
        canceled: bool = False,
    ):
        self._target = target
        self._field_name = str(field_name)
        self._new_target = new_target
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def target(self) -> Action:
        return self._target

    @target.setter
    def target(self, v: Action):
        if not isinstance(v, Action):
            raise TypeError(f"Can only redirect Actions, but got {v!r}")
        self._target = v

    @property
    def new_target(self) -> GameObject:
        return self._new_target

    # setter?

    @property
    def field_name(self) -> str:
        return self._field_name

    def doit(self):
        action = self.target
        ai = ActionInspector(action)

        # Look for name match, with high confidence
        p1 = {p: p for p in ai.param_names}
        found = FuzzyMatcher(p1, score_cutoff=80).get(self.field_name, None)

        if found is None:
            # If not, check for exact type matches
            type_matches = ai.params_of_type(type(self.new_target))
            p2 = {p: p for p in type_matches}
            found = FuzzyMatcher(p2, score_cutoff=0).get(self.field_name, None)

        if found is None:
            # Meh - we failed, lets set it anyways for history.
            warnings.warn(
                f"Could not redirect. Field name: {self.field_name!r}."
                f" Action: {action!r}. New target: {self.new_target!r}."
            )
            found = self.field_name

        ai.set_value(found, self.new_target)


class ActorRedirectAction(BaseRedirectAction):
    """Redirects actions to"""

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: Action,
        new_target: Actor,
        field_name: str = "target",
        *,
        priority: float = 50.0,
        canceled: bool = False,
    ):
        super().__init__(
            game,
            source,
            target=target,
            new_target=new_target,
            field_name=field_name,
            priority=priority,
            canceled=canceled,
        )

    @property
    def new_target(self) -> Actor:
        return self._new_target

    # setter?


class ActorRedirectorAux(TempPhaseAux):
    """Aux object that redirects actions made by the target to another actor.

    It removes itself after the end of the phase.

    Attributes
    ----------
    game : Game
    target : Actor
        The target to redirect.
    new_target : Actor
        The resulting target.
    field_name : str
        The field name to search for.
    key : None or str
        Safely ignore this (?).
    only_abilities : bool
        If True, only blocks Ability activations, and lets Triggers through.
        Default is True.
    """

    def __init__(
        self,
        game: Game,
        /,
        target: Actor,
        new_target: Actor,
        field_name: str = "target",
        key: str = None,
        *,
        only_abilities: bool = True,
        use_default_constraints: bool = True,
    ):
        self._only_abilities = bool(only_abilities)
        self._target = target
        self._new_target = new_target
        self._field_name = str(field_name)
        super().__init__(
            game, key=None, use_default_constraints=use_default_constraints
        )

    @property
    def target(self) -> Actor:
        return self._target

    @property
    def new_target(self) -> Actor:
        return self._new_target

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def only_abilities(self) -> bool:
        return self._only_abilities

    @handler
    def handle_to_cancel(
        self, event: EPreAction
    ) -> Optional[List[ActorRedirectAction]]:
        """Cancels the action if it came from the target."""
        if isinstance(event, EPreAction):
            src = event.action.source
            if isinstance(src, ATBase):
                if self.only_abilities and not isinstance(src, Ability):
                    # Skip
                    return
                if src.owner == self.target:
                    return [
                        ActorRedirectAction(
                            self.game,
                            self,
                            target=event.action,
                            new_target=self.new_target,
                            field_name=self.field_name,
                        )
                    ]


class CreateRedirectAction(Action):
    """Action that redirects all actions from the target to new_target."""

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: Actor,
        new_target: Actor,
        field_name: str = "target",
        *,
        priority: float = 90,
        canceled: bool = False,
    ):
        self.target = target
        self.new_target = new_target
        self._field_name = str(field_name)
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def field_name(self) -> str:
        return self._field_name

    def doit(self):
        ActorRedirectorAux(
            self.game,
            target=self.target,
            new_target=self.new_target,
            field_name=self.field_name,
            only_abilities=True,
        )


CreateRedirectAbility = Ability.generate(
    CreateRedirectAction,
    params=["target", "new_target"],
    name="CreateRedirectAbility",
    doc="Ability to redirect others.",
    desc="Redirects the target to another target.",
)