import pathlib  # noqa: INP001

from utils.testing import setup_t4c8_instance

ROOT_PATH = pathlib.Path("/wd/federation/tmp")

setup_t4c8_instance(ROOT_PATH)

GRR_PATH = ROOT_PATH / "grr_definition.yaml"
GRR_PATH.write_text(
"""id: "remote"
type: "directory"
directory: "/wd/federation/tmp/t4c8_grr"
""")
