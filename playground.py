from open_mafia_engine.core import *

game = Game(current_phase=Phase("day"))

town = Alignment(game, name="town")
mafia = Alignment(game, name="mafia")

alice = Actor(game, name="alice", alignments=[town])

alice.remove_alignment(town)
mafia.add_actor(alice)

print(town.actors, mafia.actors)


class VoteAbility(ActivatedAbility):
    def make_action(self, game: Game, **params) -> Optional[Action]:
        print("TEMP - it activated.")  # targets: List[str]
        return None


print(alice)
va = VoteAbility(owner=alice, name="vote")
print(alice)


# TODO: Figure out how to auto subscribe?
# va.subscribe(game)

game.broadcast_event(EActivateAbility(va))  # OMG it works!

print(game.subscribers)
print("Done.")