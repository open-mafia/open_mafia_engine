from open_mafia_engine.core.all import (
    Action,
    Actor,
    CancelAction,
    ConditionalCancelAction,
    EPreAction,
    Trigger,
    handler,
)

from .kills import KillAction, LynchAction


class UnkillableTrigger(Trigger):
    """Cancels kill actions against the owner."""

    @handler
    def cancel_self_kills(self, event: EPreAction):
        if isinstance(event, EPreAction) and isinstance(event.action, KillAction):
            # NOTE: This does almost the same, but we need to check ourselves.
            # if event.action.target == self.owner:
            #     return [CancelAction(self.game, self, target=event.action)]

            def cond(action: KillAction) -> bool:
                """Cancel only if the final target is self."""
                return action.target == self.owner

            return [
                ConditionalCancelAction(
                    self.game, self, target=event.action, condition=cond
                )
            ]


class UnlynchableTrigger(Trigger):
    """Cancels lynch actions against the owner."""

    @handler
    def cancel_self_kills(self, event: EPreAction):
        if isinstance(event, EPreAction) and isinstance(event.action, LynchAction):
            # NOTE: This does almost the same, but we need to check ourselves.
            # if event.action.target == self.owner:
            #     return [CancelAction(self.game, self, target=event.action)]

            def cond(action: LynchAction) -> bool:
                """Cancel only if the final target is self."""
                return action.target == self.owner

            return [
                ConditionalCancelAction(
                    self.game, self, target=event.action, condition=cond
                )
            ]
