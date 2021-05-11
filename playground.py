from open_mafia_engine.core import *


class VoteAction(Action):
    def doit(self, game: Game) -> None:
        print("I voted!")


class VoteAbility1(ActivatedAbility):
    def make_action(self, game: Game, **params) -> Optional[Action]:
        return VoteAction(self)


VoteAbility2 = ActivatedAbility[VoteAction]  # equivalent to VoteAbility1

VoteAbility = VoteAbility2

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
print(game.action_queue)
print("Done.")