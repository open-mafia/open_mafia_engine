from typing import List

PATH_SEP = "/"  # Separates paths in hierarchical structures
# TODO: Consider other separators.

ABILITY = "ability"
TRIGGER = "trigger"


def get_parts(path: str) -> List[str]:
    if not isinstance(path, str):
        raise TypeError(f"Expected str, got {path!r}")
    return path.split(PATH_SEP)


def get_path(*parts: List[str]) -> str:
    return PATH_SEP.join(parts)
