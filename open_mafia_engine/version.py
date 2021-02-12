try:
    import importlib.metadata as _im
except ImportError:
    import importlib_metadata as _im

__all__ = ["version"]
version = _im.version("open_mafia_engine")
