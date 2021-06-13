import inspect
from typing import Callable, Type

from open_mafia_engine.util.repr import ReprMixin


class MafiaError(Exception, ReprMixin):
    """Base class for Mafia exceptions."""


class MafiaAmbiguousTypeName(MafiaError):
    """The type name conficts with an existing name."""

    def __init__(self, existing_type: Type[object], new_type: Type[object]) -> None:
        self.existing_type = existing_type
        self.new_type = new_type
        self.type_name = type_name = existing_type.__qualname__
        
        super().__init__(
            f"""Type {type_name!r} conficts with existing type.
            Existing type defined in: {inspect.getmodule(existing_type)}
            New type defined in: {inspect.getmodule(new_type)}            
            """
        )


class MafiaTypeNotFound(MafiaError):
    """The type was not found."""

    def __init__(self, type_name: str) -> None:
        self.type_name = type_name
        super().__init__(f"Couldn't find GameObject subtype {type_name!r}")


class MafiaConverterError(MafiaError, TypeError):
    """Could not convert object to the requested type."""

    def __init__(self, obj: str, type_: Type):
        self.obj = obj
        self.type_ = type_
        super().__init__(f"Couldn't convert {obj!r} to {type_!r}")


class MafiaBadHandler(MafiaError, TypeError):
    """Function can't be used as an event handler."""

    def __init__(self, func: Callable):
        self.func = func
        super().__init__(f"Function isn't a legal event handler: {func!r}")


class MafiaBadBuilder(MafiaError, TypeError):
    """Function can't be used as a game builder."""

    def __init__(self, func: Callable):
        self.func = func
        super().__init__(f"Function isn't a legal game builder: {func!r}")
