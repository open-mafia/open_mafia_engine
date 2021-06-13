from open_mafia_engine.core.all import ATBase, Ability, Action, Actor, Game, GameObject


class BaseInformationAction(Action):
    """Action that gives information to a player.

    Only ATBase (e.g. Ability or Trigger) may create this action,
    so we always know the "owner" (who to inform).

    Inherit from this action.
    """

    def __init__(
        self, game: Game, source: ATBase, /, *, priority: float, canceled: bool
    ):
        if not isinstance(source, ATBase):
            raise TypeError(f"Information actions require players.")
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def source(self) -> ATBase:
        return self._source

    @property
    def owner(self) -> Actor:
        return self.source.owner

    @classmethod
    def status_key(self) -> str:
        """Returns the key where results will be stored."""
        return "info_results"

    def inform(self, msg: str):
        """Helper function to inform the user.

        This will trigger `EStatusChanged`.
        """
        msg = str(msg)

        key = self.status_key()
        st = self.owner.status
        old = st.get(key)
        if old is None:
            st[key] = [msg]
        elif isinstance(old, list):
            st[key] = old + [msg]
        else:
            raise TypeError(f"Expected previous status to be list, but got: {old!r}")

    # doit()


class BaseInspectAction(BaseInformationAction):
    """Action that inspects an Actor.

    Inherit from this action.
    """

    def __init__(
        self,
        game: Game,
        source: ATBase,
        /,
        target: Actor,
        *,
        priority: float = 0.0,
        canceled: bool = False,
    ):
        self._target = target
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def target(self) -> Actor:
        return self._target

    @target.setter
    def target(self, v: Actor):
        self._target = v

    # doit()


class FactionInspectAction(BaseInspectAction):
    """Inspect the factions of a player."""

    def doit(self):
        found = [f.name for f in self.target.factions]
        msg = "Your target is part of these factions: " + ", ".join(found)
        self.inform(msg)


FactionInspectAbility = Ability.generate(
    FactionInspectAction,
    params=["target"],
    name="FactionInspectAbility",
    doc="Ability to inspect someone's faction(s).",
    desc="Inspect target's faction(s).",
)
