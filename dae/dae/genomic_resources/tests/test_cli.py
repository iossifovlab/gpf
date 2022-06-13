# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository import GR_CONTENTS_FILE_NAME
from dae.genomic_resources.cli import cli_manage
from dae.genomic_resources.testing import build_testing_repository
# , cli_cache_repo


def test_cli_manifest(tmp_path):

    demo_gtf_content = "TP53\tchr3\t300\t200".encode("utf-8")
    build_testing_repository(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala"
            },
            "sub": {
                "two(1.0)": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "genes.txt": demo_gtf_content
                }
            }
        })

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).is_file()
    cli_manage(["manifest", str(tmp_path), "one"])
    assert (tmp_path / "one/.MANIFEST").is_file()
