"""YAML loader for seed-data defaults under configs/defaults/."""

from typing import Any

import yaml

from backend.app.utils.path import CONFIG_PATH

DEFAULTS_DIR = CONFIG_PATH / "defaults"


class DefaultsNotFoundError(Exception):
    """Raised when a defaults YAML file does not exist."""


def load_defaults(name: str) -> list[dict[str, Any]]:
    """Load a defaults YAML file and return its ``items`` list.

    Parameters
    ----------
    name:
        Stem name of the YAML file (e.g. ``"scoring_criteria"``).

    Returns
    -------
    list[dict[str, Any]]
        The list of default item dicts.

    Raises
    ------
    DefaultsNotFoundError
        If the file does not exist.
    """
    path = DEFAULTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise DefaultsNotFoundError(f"Defaults file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    return data["items"]
