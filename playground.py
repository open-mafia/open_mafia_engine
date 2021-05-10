from open_mafia_engine.core import *

town = Alignment(name="town")
mafia = Alignment(name="mafia")
print(town.actors, mafia.actors)

alice = Actor(name="alice", alignments=[town])
print(town.actors, mafia.actors)

alice.remove_alignment(town)
mafia.add_actor(alice)

print(town.actors, mafia.actors)

print(alice)
Ability(name="abil", owner=alice)
print(alice)

print("Done.")