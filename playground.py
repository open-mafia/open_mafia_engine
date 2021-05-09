from open_mafia_engine.core import *

e = GameEngine.current()


class FakeAction(Action):
    def __call__(self) -> None:
        print(f"Running fake action, priority={self.priority}")


i_al = e.add_object(Alignment("test_alignment"))
i_act = e.add_object(Actor(name="tester", alignment_id=i_al, ability_ids=[]))
i1 = e.add_object(FakeAction(source_id=i_act, priority=10))
i2 = e.add_object(FakeAction(source_id=i_act, priority=20))

ac = e.root_context
ac.enqueue(i1, i2)
ac.process_all()
e
