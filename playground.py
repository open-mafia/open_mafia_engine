from open_mafia_engine.core import *


class VoteAction(Action):
    def __init__(
        self,
        source: GameObject,
        target: str = None,
        *,
        priority: float = 1.0,
        canceled: bool = False,
    ):
        super().__init__(source, priority=priority, canceled=canceled)
        self.target = target

    def doit(self, game: Game) -> None:
        print(f"I voted for {self.target}!")


VoteAbility = ActivatedAbility.create_type(VoteAction, name="VoteAbility")
# VoteAbility = ActivatedAbility[VoteAction]  # alternate, but badly named


class Notifier(Subscriber):
    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, Event)

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        print(f"  Saw event: {type(event).__qualname__}")
        return None


# Create the game

game = Game()

town = Alignment(game, name="town")
mafia = Alignment(game, name="mafia")

alice = Actor(game, name="alice", alignments=[town])
av = VoteAbility(owner=alice, name="vote")

bob = Actor(game, name="bob", alignments=[mafia])
bv = VoteAbility(owner=bob, name="vote")

charlie = Actor(game, name="charlie", alignments=[town])
cv = VoteAbility(owner=charlie, name="vote")

# Yell at everything
notifier = Notifier()
notifier.__subscribe__(game)

# Run stuff

# start first day
game.process_event(ETryPhaseChange())

# do some voting
game.process_event(EActivateAbility(av))
game.process_event(EActivateAbility(av, target="bob"))

# start first night
game.process_event(ETryPhaseChange())

# voting at night - these actions should happen at day end
game.process_event(EActivateAbility(av, target="charlie"))
game.process_event(EActivateAbility(av, target="alice", priority=10))

print("This happens before votes for C, A")
# start second day
game.process_event(ETryPhaseChange())

print(game.action_queue)
print("Done.")
