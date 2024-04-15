"""Configuration access and handling module.

- stores all config-values imported from Env-Variables or specifically specified
- offers class Config, that sets and stores config-values in class-variables

  Typical usage example:

  dev_mode = Config.conf["development_mode"]
"""

import os
from collections import ChainMap

from agatha import __version__
from agatha.util import singleton


@singleton
class Config:
    """Store config-values in class-variables."""

    # Empty ChainMap before initialization
    defaults = {"development_mode": False}
    conf: ChainMap = ChainMap(defaults)

    def __init__(self, **cli_args):
        """Init config from cli, environment and default values.

        Chains cli-arguments with environment arguments and default values, uses

        Args:
            cli_args: cli-config as keyword arguments

        """
        env_vars = {}

        # Add other config variables here with default values

        if tmp := os.environ.get("AGATHA_DEVELOPMENT_MODE"):
            # with ensured types
            env_vars["development_mode"]: bool = tmp == "True"

        Config.conf = ChainMap(cli_args, env_vars, Config.defaults)


def print_config():
    """Print startup info message displaying version and environment status."""
    print("\n" + "=" * 20 + f" Agatha v. {__version__} " + "=" * 20)
    for key, value in Config.conf.items():
        name = key.replace("_", " ")
        name = name.capitalize()
        if "mode" in name:
            state = "active" if value else "inactive"
        else:
            state = str(state)
        print(f"{name}: {state}")
    print()
