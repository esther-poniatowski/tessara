"""
tessara.handling.param_interface
================================

Re-export module for backward compatibility.

The implementations have been split into focused modules:

- ``assigner`` -- ParamAssigner, Config
- ``binder`` -- ParamBinder
- ``composer`` -- ParamComposer
- ``sweeper`` -- ParamSweeper

All public names are re-exported here so that existing imports continue to work.
"""
from tessara.handling.assigner import Config, ParamAssigner  # noqa: F401
from tessara.handling.binder import ParamBinder  # noqa: F401
from tessara.handling.composer import ParamComposer  # noqa: F401
from tessara.handling.sweeper import ParamSweeper  # noqa: F401

__all__ = [
    "Config",
    "ParamAssigner",
    "ParamBinder",
    "ParamComposer",
    "ParamSweeper",
]
