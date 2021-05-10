from open_mafia_engine.core import *

e = GameEngine.current()


class FakeAction(Action):
    def __call__(self) -> None:
        print(f"Running fake action, priority={self.priority}")


i_al = e.add_object(Alignment("test_alignment"))
i_act1 = e.add_object(Actor(name="a1", alignment_id=i_al, ability_ids=[]))
i_act2 = e.add_object(Actor(name="a2", alignment_id=i_al, ability_ids=[]))
i1 = e.add_object(FakeAction(source_id=i_act1, priority=10))
i2 = e.add_object(FakeAction(source_id=i_act2, priority=20))
tid = e.add_object(VoteTally())
v1 = e.add_object(VoteAction(source_id=i_act1, target_ids=[i_act2], tally_id=tid))
v2 = e.add_object(VoteAction(source_id=i_act1, target_ids=[], tally_id=tid))

ac = e.root_context
# ac.enqueue(i1, i2)
ac.enqueue(v1, v2)
ac.process_all()
e
