import os

import dask
import yaml


def reconfigure() -> None:
    """Load default config into dask."""
    filename = os.path.join(os.path.dirname(__file__), "named_cluster.yaml")
    dask.config.ensure_file(source=filename)  # pyright: ignore

    with open(filename) as file:
        defaults = yaml.safe_load(file)

    dask.config.update_defaults(defaults)  # pyright: ignore


reconfigure()
