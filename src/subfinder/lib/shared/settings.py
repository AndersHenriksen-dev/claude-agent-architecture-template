"""Reading config files, and the settings the whole package shares.

Each config file belongs to one Python file and mirrors its path: `lib/api/clean_merchants.py` reads
`config/api/clean_merchants.yaml`. Pydantic checks every file as it is read, so a typo fails when the package loads.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, TypeAdapter

REPO_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
_LIB_PREFIX = "subfinder.lib."


class Strict(BaseModel):
    """A model that refuses unknown fields, so a misspelled key fails instead of being ignored."""

    model_config = ConfigDict(extra="forbid")


def config_path(module: str) -> Path:
    """Where a module's config file is: `subfinder.lib.api.clean_merchants` reads `config/api/clean_merchants.yaml`."""
    return CONFIG_DIR.joinpath(*module.removeprefix(_LIB_PREFIX).split(".")).with_suffix(".yaml")


def read_config[T](path: Path, shape: type[T]) -> T:
    """Read one YAML file and check it against a shape, so the rest of the code works with typed objects."""
    with path.open(encoding="utf-8") as file:
        return TypeAdapter(shape).validate_python(yaml.safe_load(file))


def config_for[T](module: str, shape: type[T]) -> T:
    """Read a module's own config file. Pass `__name__`, which keeps the two paths matched."""
    return read_config(config_path(module), shape)


class Price(Strict):
    """USD per million tokens."""

    input: float
    output: float


class Settings(Strict):
    """The settings every part of the package shares."""

    model: str
    prices: dict[str, Price]
    workspace_dir: str
    workbook_file: str
    audit_file: str


SETTINGS = config_for(__name__, Settings)


def model_from_env() -> str:
    """The model for paid calls: SUBFINDER_MODEL, or the default."""
    return os.environ.get("SUBFINDER_MODEL", SETTINGS.model)


def workspace_dir() -> Path:
    """The folder a run writes to: SUBFINDER_WORKSPACE, or the git-ignored folder in the repo."""
    return Path(os.environ.get("SUBFINDER_WORKSPACE", REPO_ROOT / SETTINGS.workspace_dir))


def workbook_path() -> Path:
    """The file that holds a run's tags and summary."""
    return workspace_dir() / SETTINGS.workbook_file


def audit_log_path() -> Path:
    """The file the hooks append every tool call to."""
    return workspace_dir() / SETTINGS.audit_file
