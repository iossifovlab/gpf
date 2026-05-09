# ruff: noqa: INP001
# Standalone helper script run as the entrypoint of the integration
# backend container — not a package member, so it has no neighbour
# __init__.py. Hence the file-level INP001 suppression.
"""Seed a t4c8 GPF instance for the federation integration test backend."""
import pathlib

from utils.testing import setup_t4c8_instance

ROOT_PATH = pathlib.Path("/workspace/federation/tmp")
ROOT_PATH.mkdir(parents=True, exist_ok=True)

setup_t4c8_instance(ROOT_PATH)

GRR_PATH = ROOT_PATH / "grr_definition.yaml"
GRR_PATH.write_text(
    'id: "remote"\n'
    'type: "directory"\n'
    f'directory: "{ROOT_PATH}/t4c8_grr"\n',
)
