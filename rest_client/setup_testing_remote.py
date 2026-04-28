import pathlib  # noqa: INP001

from utils.testing import setup_t4c8_instance

ROOT_PATH = pathlib.Path("/wd/rest_client/tmp")

GRR_PATH = ROOT_PATH / "grr_definition.yaml"
GRR_PATH.write_text(
"""id: "remote"
type: "directory"
directory: "/wd/rest_client/tmp/t4c8_grr"
""")

setup_t4c8_instance(ROOT_PATH)
