from open_mafia_engine.util.repr import ReprMixin


class MafiaError(Exception, ReprMixin):
    """Base class for Mafia exceptions."""
