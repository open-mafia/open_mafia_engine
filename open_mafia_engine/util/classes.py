from typing import Type


def class_name(cls: Type[object]) -> str:
    """Returns the class name."""
    return cls.__qualname__
