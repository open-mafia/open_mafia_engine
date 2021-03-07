from pydantic import BaseModel


class StateModel(BaseModel):
    """Base class for objects defining game state.

    The `Config` class makes sure Pydantic always enforces constraints
    (unless, of course, overridden by the subclass).

    To add a constraint, create a pydantic validator:
    https://pydantic-docs.helpmanual.io/usage/validators/
    """

    class Config:
        validate_assignment = True
