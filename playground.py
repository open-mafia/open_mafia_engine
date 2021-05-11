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


# Create the game

game = Game(current_phase=Phase("day", action_resolution="instant"))

town = Alignment(game, name="town")
mafia = Alignment(game, name="mafia")

alice = Actor(game, name="alice", alignments=[town])
av = VoteAbility(owner=alice, name="vote")

bob = Actor(game, name="bob", alignments=[mafia])
bv = VoteAbility(owner=bob, name="vote")

charlie = Actor(game, name="charlie", alignments=[town])
cv = VoteAbility(owner=charlie, name="vote")

# Run stuff

game.process_event(EActivateAbility(av))
game.process_event(EActivateAbility(av, target="bob"))
print(game.action_queue)
print("Done.")
