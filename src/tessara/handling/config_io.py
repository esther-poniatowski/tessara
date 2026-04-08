"""
tessara.handling.config_io
==========================

Configuration loading utilities.
"""

from pathlib import Path
from typing import Any


def load_yaml(path: str | Path, prefer_omegaconf: bool = True) -> dict:
    """
    Load configuration from YAML with optional OmegaConf resolution.

    Parameters
    ----------
    path : str | Path
        Path to the YAML file.
    prefer_omegaconf : bool, default True
        If True, try OmegaConf before PyYAML. If False, try PyYAML first.

    Returns
    -------
    dict
        Loaded configuration.

    Raises
    ------
    FileNotFoundError
        If the YAML file does not exist at *path*.
    ImportError
        If neither ``omegaconf`` nor ``pyyaml`` is installed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    loaders = ["omegaconf", "pyyaml"] if prefer_omegaconf else ["pyyaml", "omegaconf"]

    last_error: Exception | None = None
    for loader in loaders:
        try:
            if loader == "omegaconf":
                from omegaconf import OmegaConf

                config = OmegaConf.load(path)
                config = OmegaConf.to_container(config, resolve=True)
            else:
                import yaml

                with open(path) as f:
                    config = yaml.safe_load(f)
            return config or {}
        except ImportError as exc:
            last_error = exc
            continue

    raise ImportError(
        "Either 'omegaconf' or 'pyyaml' is required for YAML loading."
    ) from last_error
