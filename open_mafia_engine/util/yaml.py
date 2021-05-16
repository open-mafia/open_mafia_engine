from pathlib import Path
from typing import Union

try:
    import yaml

    def load_yaml(p: Path) -> Union[dict, list, None]:
        """Loads a YAML file safely."""

        p = Path(p).resolve()
        with p.open() as f:
            return yaml.safe_load(f)


except ImportError:
    from ruamel.yaml import YAML

    def load_yaml(p: Path) -> Union[dict, list, None]:
        p = Path(p).resolve()
        with p.open() as f:
            return YAML(typ="safe").load(f)
