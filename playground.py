from open_mafia_engine.core import *

town = Alignment(name="town")
mafia = Alignment(name="mafia")
print(town.actors, mafia.actors)

alice = Actor(name="alice", alignments=[town])
print(town.actors, mafia.actors)

alice.remove_alignment(town)
mafia.add_actor(alice)

print(town.actors, mafia.actors)


class VoteAbility(ActivatedAbility):
    def make_action(self, game: Game, **params) -> Optional[Action]:
        print("TEMP - it activated.")  # targets: List[str]
        return None


print(alice)
va = VoteAbility(name="vote", owner=alice)
print(alice)


game = Game(current_phase=Phase("day"), alignments=[town, mafia], actors=[alice])

# TODO: Figure out how to auto subscribe?
va.subscribe(game)

game.broadcast_event(EActivateAbility(va))  # OMG it works!

print("Done.")