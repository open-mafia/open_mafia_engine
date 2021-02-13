"""
TODO: Resolve abilities...

Action system? Event like before? So many questions... :D

Core problems:
- day actions (generally) are executed immediately, i.e. in time order
- night actions (generally) are queued, then executed at the end of the night
  depending on the priorities, targets, etc.
- auto/passive/triggered abilities are hard to do, because they can cancel or
  alter abilities, their flow, etc.

In the original system, I used events and pre-/post-handlers, and it was super
flexible, yet felt super hacky.

I'm not sure how to allow that level of flexibility without essentially allowing
each ability type/function to modify the execution flow. Allowing them to
modify the stack AT WILL is definitely a no-no; that path leads to madness.
On the other hand, just having a priority queue + responses creating sub-queues
is already reasonably effective...
"""
