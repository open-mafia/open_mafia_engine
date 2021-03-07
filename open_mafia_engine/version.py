try:
    import importlib.metadata as _im
except ImportError:
    import importlib_metadata as _im

from typing import Dict

import pkg_resources

__all__ = ["version", "get_versions"]
version = _im.version("open-mafia-engine")


def get_versions() -> Dict[str, str]:
    """Returns version info for all Open Mafia (sub-)packages."""

    prefix = "open-mafia"
    z = sorted(
        [
            (p.key, p.version)
            for p in pkg_resources.working_set
            if p.key.startswith(prefix)
        ]
    )
    res = {k: v for k, v in z}
    return res
