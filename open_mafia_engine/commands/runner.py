from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    NoReturn,
    Optional,
    Tuple,
    Type,
    Union,
)
import warnings

from makefun import partial

from open_mafia_engine.core.all import ABILITY, EActivate, Game, GameBuilder, get_path
from open_mafia_engine.util.matcher import FuzzyMatcher

from .lobby import AbstractLobby, SimpleDictLobby
from .parser import AbstractCommandParser, ShellCommandParser
from .raw import RawCommand, TUser, MafiaBadCommand

__all__ = ["command", "CommandHandler", "CommandRunner"]


class CommandHandler(object):
    """Descriptor, wrapper for command functions.

    Parameters
    ----------
    func : Callable
        The wrapped function.
    game : bool
        If True, allows use during the game. Default is True.
    lobby : bool
        If True, allows use in the lobby. Default is False.
    admin : bool
        If True, this is an admin-only command.
    name : None or str
        Command name. If None (default), uses function's name.
    """

    registered: Dict[str, CommandHandler] = {}
    score_cutoff: int = 80

    def __init__(
        self,
        func: Callable,
        *,
        game: bool = True,
        lobby: bool = False,
        admin: bool = False,
        name: str = None,
    ):
        if not callable(func):
            raise TypeError(f"`func` must be callable, got {func!r}")
        if name is None:
            name = func.__name__
        # TODO: Get documentation :)

        self.func = func
        self.name = name
        self.game = bool(game)
        self.lobby = bool(lobby)
        self.admin = bool(admin)

    def __set_name__(self, owner: Type[CommandRunner], name_: str):
        self.bound_name = name_
        _RC = "registered_commands"

        # self.registered[name] = self  # FIXME: change to the following?

        # Create a dict for `owner`
        if not hasattr(owner, _RC):
            v = dict(**getattr(super(owner), _RC, {}))
            setattr(owner, _RC, v)
        owner.registered_commands[self.name] = self

    def __get__(self, obj: CommandRunner, objtype=None):
        return partial(self.func, obj)


def command(
    name_or_func: Union[str, Callable],
    *,
    game: bool = None,
    lobby: bool = None,
    admin: bool = False,
) -> Union[Callable]:
    """Decorator to register methods as commands.

    By default, "game" is True, "lobby" is `not game`, and "admin" is False.
    """

    if game is None:
        if lobby is None:
            game = True
            lobby = False
        else:
            game = not lobby
    else:
        if lobby is None:
            lobby = not game
    game = bool(game)
    lobby = bool(lobby)
    admin = bool(admin)

    if isinstance(name_or_func, str):

        def inner(func: Callable) -> CommandHandler:
            return CommandHandler(
                func, name=name_or_func, game=game, lobby=lobby, admin=admin
            )

        return inner
    elif callable(name_or_func):
        func = name_or_func
        return CommandHandler(func, game=game, lobby=lobby, admin=admin)
    else:
        raise TypeError(f"Argument to `command` is neither str, nor callable.")


class CommandRunner(Generic[TUser]):
    """Interprets and runs commands on the Mafia engine.

    This handles both pre-game commands (such as joining or starting the game)
    and commands during the game.
    Basic Mafia commands are already added.

    To add or override a command handler, use the `command` decorator:

        class MyRunner(CommandRunner[MyUserType]):
            @command("foo", game=True)
            def my_foo(self, source: str, *args, **kwargs):
                return

    The command decorator defaults to non-admin, in-game actions.
    Specifying `lobby=True` will, by default, allow only lobby use.
    If you want it always on, use `@command("name", game=True, lobby=True)`

    Commands that don't match any given command will call `default_command()`.
    The default implementation raises a MafiaBadCommand exception, but you may
    override it (e.g. to ignore it).

    Attributes
    ----------
    parser : AbstractCommandParser
        Your own parser implementation, or ShellCommandParser() by default.
    lobby : AbstractLobby
        Your own lobby implementation, or SimpleDictLobby[TUser]() by default.
    game : None or Game
        The game state. Defaults to None.
    score_cutoff : int
        The score cutoff for matching command names, from 0 to 100.
        Default is 80 (relatively strict).
    """

    registered_commands: Dict[str, CommandHandler]

    def __init__(
        self,
        parser: AbstractCommandParser = ShellCommandParser(),
        lobby: AbstractLobby[TUser] = SimpleDictLobby[TUser](),
        game: Optional[Game] = None,
        *,
        score_cutoff: int = 80,
    ):
        self.parser = parser
        self.lobby = lobby
        self.score_cutoff = int(score_cutoff)
        # This will check :)
        self.game = game

    @classmethod
    def all_available_commands(cls) -> List[str]:
        """Returns all commands that are registered."""
        return list(cls.registered_commands.keys())

    def currently_available_commands(self, source: str = None) -> List[str]:
        """Returns all commands that are currently available."""
        all_cmds = self.all_available_commands()

        def chk(cmd: str) -> bool:
            # FIXME
            try:
                self.pre_dispatch_check(cmd, source=source)
            except Exception:
                return False
            return True

        return [cmd for cmd in all_cmds if chk(cmd)]

    @property
    def game(self) -> Optional[Game]:
        return self._game

    @game.setter
    def game(self, game: Optional[Game]):
        if game is not None and not isinstance(game, Game):
            raise TypeError(f"Expected None or Game, got {game!r}")
        self._game = game

    @property
    def lobby(self) -> AbstractLobby[TUser]:
        return self._lobby

    @lobby.setter
    def lobby(self, lobby: AbstractLobby[TUser]):
        if not isinstance(lobby, AbstractLobby):
            raise TypeError(f"Expected AbstractLobby, got {lobby!r}")
        self._lobby = lobby

    @property
    def parser(self) -> AbstractCommandParser:
        return self._parser

    @parser.setter
    def parser(self, parser: AbstractCommandParser):
        if not isinstance(parser, AbstractCommandParser):
            raise TypeError(f"Expected AbstractCommandParser, got {parser!r}")
        self._parser = parser

    @property
    def in_game(self) -> bool:
        """True if the game is active."""
        return self._game is not None

    @property
    def in_lobby(self) -> bool:
        """True if the game is not active."""
        return not self.in_game

    def pre_check_command(self, rc: RawCommand):
        """Override for additional command checking"""

    def parse_and_run(self, source: str, obj: str) -> List[Tuple[RawCommand, Any]]:
        """Parses commands and runs them."""
        rcs = self.parser.parse(source, obj)
        res = []
        for rc in rcs:
            self.pre_check_command(rc)
            out_i = self.dispatch(rc)
            res.append((rcs, out_i))
        return res

    def find_command(self, name: str) -> CommandHandler:
        """Finds the closes command handler."""
        matcher = FuzzyMatcher(
            choices=self.registered_commands,
            score_cutoff=self.score_cutoff,
        )
        return matcher[name]

    # TODO: Syntax for default command?
    def default_command(self, source: str, name: str, *args, **kwargs) -> NoReturn:
        """Default command definition - override."""
        rc = RawCommand(source, name, args, kwargs)
        raise MafiaBadCommand(rc)

    def pre_dispatch_check(self, cmd: str, source: str = None) -> CommandHandler:
        """Gets the command handler for a given command name, with checked access.

        Checks whether the command is available for a certain source.
        If not - raises an exception.
        """
        try:
            ch: CommandHandler = self.find_command(cmd)
        except KeyError:
            # TODO: Instead return a default command? ...
            raise KeyError(f"No such command: {cmd!r}.")

        if ch.admin:
            if source not in self.lobby.admin_names:
                raise RuntimeError(f"Command {ch.name!r} requires admin privileges.")
        if self.in_lobby and not ch.lobby:
            raise RuntimeError(f"Command {ch.name!r} not available in lobby.")
        if self.in_game and not ch.game:
            raise RuntimeError(f"Command {ch.name!r} not available during game.")
        return ch

    def dispatch(self, rc: RawCommand) -> Any:
        """Calls the relevant command given by `rc`."""
        try:
            ch: CommandHandler = self.pre_dispatch_check(rc.name, source=rc.source)
        except KeyError:
            # Default command
            return self.default_command(rc.source, rc.name, *rc.args, **rc.kwargs)
        except Exception:
            raise

        # TODO: Possibly add debug output here?
        return ch.func(self, rc.source, *rc.args, **rc.kwargs)

    def user_for(self, name: str) -> Optional[TUser]:
        """Gets the user by name from the lobby."""
        return self.lobby.get(name, None)

    @command("join", lobby=True)
    def join(self, source: str):
        """Joins the game as a player."""
        user = self.user_for(source)
        if user is None:
            raise ValueError(f"No user found for {source!r}. Possibly not implemented?")
        self.lobby.add_player(source, user)  # [source] = user

    @command("in", lobby=True)
    def _join2(self, source: str):
        """Alias for 'join'."""
        return self.join(source)

    @command("leave", lobby=True)
    def leave(self, source: str):
        """Leaves the lobby."""
        user = self.user_for(source)
        if user is None:
            raise ValueError(f"No user found for {source!r}. Possibly not implemented?")
        self.lobby.remove_player(source, user)  # [source] = user

    @command("out", lobby=True)
    def _leave2(self, source: str):
        """Alias for 'leave'."""
        return self.leave(source)

    @command("force-join", admin=True, lobby=True)
    def force_join(self, source: str, *targets: List[str]):
        """Force one or more users to join the lobby."""
        users: Dict[str, TUser] = {}
        errors: List[str] = []
        for t in targets:
            user = self.user_for(t)
            if user is None:
                errors.append(t)
            else:
                users[t] = user
        if len(errors) > 0:
            raise ValueError(f"No users found for these names: {errors!r}.")
        for n, u in users.items():
            self.lobby.add_player(n, u)

    @command("kick", admin=True, lobby=True, game=True)
    def kick(self, source: str, *args, **kwargs):
        """Kick a player from the lobby or game.

        TODO: Implement!
        Will probably need change in AbstractLobby.
        Will definitely need change in Game to handle kicking/modkilling...
        """
        # TODO: Implement.

    @command("create-game", admin=True, lobby=True)
    def create_game(self, source: str, builder_name: str, *args, **kwargs):
        """Creates the game.

        TODO: Need to standardize builder options.
        For example, 'game name' would be pretty important!
        """
        if self.in_game:
            raise ValueError("BUG. Currently in a game - can't create one.")
        builder = GameBuilder.load(builder_name)
        game = builder.build(self.lobby.player_names, *args, **kwargs)
        self.game = game

    @command("destroy-game", admin=True, game=True)
    def destroy_game(self, source: str):
        """Stops the game immediately.

        Do we even need this? I assume you'd just make a new runner... :)

        TODO: Maybe a bit more elegantly?...
        TODO: Auto-stop the game when EGameEnded occurs? Not sure how that would work.
        """
        self.game = None

    @command("phase", admin=True, game=True)
    def change_phase(self, source: str, new_phase: Optional[str] = None):
        """Changes the phase (admin action)."""
        if self.game is None:
            raise RuntimeError("Game not yet started.")
        self.game.change_phase(new_phase=new_phase)
        # Alternatively:
        # e = ETryPhaseChange(self.game, new_phase=new_phase)
        # self.game.process_event(e)

    @command("do", game=True)
    def do(self, source: str, abil_name: str, *args, **kwargs):
        """Activates an ability."""
        abil_path = get_path(source, ABILITY, abil_name)
        e = EActivate(self.game, abil_path, *args, **kwargs)
        self.game.process_event(e)

    @command("vote", game=True)
    def vote(self, source: str, *args, **kwargs):
        """Votes for the target(s)."""
        return self.do(source, "vote", *args, **kwargs)

    @command("unvote", game=True)
    def unvote(self, source: str, *args, **kwargs):
        """Unvotes from all previous votes."""
        # TODO: 'vote' for "unvote-all" or smth?
        # TODO: Maybe add this only in ForumCommandRunner?
        return self.do(source, "vote", *args, **kwargs)

    # TODO: Maybe allow backup command handlers for unknown commands? :)
