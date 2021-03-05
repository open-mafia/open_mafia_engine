from pathlib import Path
from typing import Union

import yaml

# TODO: Support ruamel.yaml as well


def load_yaml(p: Path) -> Union[dict, list, None]:
    """Loads a YAML file safely."""

    p = Path(p).resolve()
    with p.open() as f:
        return yaml.safe_load(f)
