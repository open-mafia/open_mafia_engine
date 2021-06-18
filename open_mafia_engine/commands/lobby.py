from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Mapping

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .raw import TUser

__all__ = ["AbstractLobby", "SimpleLobby"]


class AbstractLobby(Mapping, Generic[TUser]):
    """A lobby, with mappings to user-defined objects.

    Attributes
    ----------
    admins : dict
        Mapping of admin names to user objects. Override this.
    players : dict
        Mapping of player names to user objects. Override this.
    """

    @property
    @abstractmethod
    def players(self) -> Dict[str, TUser]:
        """Return mapping of str to players."""

    @property
    @abstractmethod
    def admins(self) -> Dict[str, TUser]:
        """Return mapping of str to admins."""

    @abstractmethod
    def add_player(self, name: str, user: TUser):
        """Add the player to the game."""

    @abstractmethod
    def add_admin(self, name: str, user: TUser):
        """Add the player to the game."""

    @property
    def player_names(self) -> List[str]:
        return list(self.players.keys())

    @property
    def admin_names(self) -> List[str]:
        return list(self.admins.keys())

    @property
    def all_names(self) -> List[str]:
        return list(set(self.player_names).union(self.admin_names))

    def __getitem__(self, k: str) -> TUser:
        res = self.admins.get(k, None)
        if res is None:
            res = self.players.get(k, None)
        if res is None:
            raise KeyError(k)
        return res

    def __iter__(self):
        keys = set(self.all_names)
        return iter(keys)

    def __len__(self):
        keys = set(self.all_names)
        return len(keys)


class SimpleLobby(AbstractLobby[TUser]):
    """Simple lobby implementation."""

    def __init__(
        self,
        admins: Dict[str, TUser] = None,
        players: Dict[str, TUser] = None,
    ) -> None:
        if admins is None:
            admins = {}
        if players is None:
            players = {}
        self._admins = dict(admins)
        self._players = dict(players)

    @property
    def players(self) -> Dict[str, TUser]:
        return dict(self._players)

    @property
    def admins(self) -> Dict[str, TUser]:
        return dict(self._admins)

    def add_admin(self, name: str, user: TUser):
        self._admins[name] = user

    def add_player(self, name: str, user: TUser):
        self._players[name] = user