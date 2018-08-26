""""""

import uuid


class GameObject:
    """Base class for all game objects."""

    def __init__(self):
        self.ID = uuid.uuid1()

    def __repr__(self):
        its = self.__dict__.items()
        kw = ", ".join(
            "{}={}".format(k, repr(v)) for k, v in its
            if k[0] != "_"
        )
        return "{}({})".format(self.__class__.__name__, kw)
