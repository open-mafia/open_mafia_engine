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

__all__ = ["AbstractLobby", "SimpleDictLobby", "AutoAddStrLobby"]


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
    def remove_player(self, name: str, user: TUser):
        """Remove the player from the game."""

    @abstractmethod
    def add_admin(self, name: str, user: TUser):
        """Add the admin to the game."""

    @abstractmethod
    def remove_admin(self, name: str, user: TUser):
        """Remove the admin from the game."""

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


class SimpleDictLobby(AbstractLobby[TUser]):
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

    def remove_admin(self, name: str, user: TUser):
        if name in self._admins:
            del self._admins[name]

    def add_player(self, name: str, user: TUser):
        self._players[name] = user

    def remove_player(self, name: str, user: TUser):
        if name in self._players:
            del self._players[name]


class AutoAddStrLobby(AbstractLobby[str]):
    """String-based lobby that adds any users automatically."""

    def __init__(self, admin_names: List[str] = [], player_names: List[str] = []):
        self._admin_names = set(admin_names)
        self._player_names = set(player_names)

    @property
    def players(self) -> Dict[str, str]:
        return {x: x for x in self._player_names}

    @property
    def admins(self) -> Dict[str, str]:
        return {x: x for x in self._admin_names}

    @property
    def player_names(self) -> List[str]:
        return sorted(self.players.keys())

    @property
    def admin_names(self) -> List[str]:
        return sorted(self.admins.keys())

    def add_admin(self, name: str, user: str):
        assert name == user
        self._admin_names.add(name)

    def remove_admin(self, name: str, user: str):
        self._admin_names.discard(name)

    def add_player(self, name: str, user: str):
        assert name == user
        self._player_names.add(name)

    def remove_player(self, name: str, user: str):
        self._player_names.discard(name)

    def __getitem__(self, k: str) -> str:
        return k
