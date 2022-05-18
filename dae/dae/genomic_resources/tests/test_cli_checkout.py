"""Test grr_manage checkout command."""
# pylint: disable=protected-access,redefined-outer-name
import pytest

from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.cli import _run_checkout_command


@pytest.fixture
def dir_repo(tmp_path):
    """Fixture for directory repository."""

    demo_gtf_content = "TP53\tchr3\t300\t200"
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: ["", "2021-11-20T00:00:56+00:00"],  # NOSONAR
            "data.txt": ["alabala", "2021-11-20T00:00:56+00:00"],
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: ["type: gene_models\nfile: genes.gtf",
                                    "2021-11-20T00:00:56+00:00"],
                "genes.txt": demo_gtf_content
            }
        }
    })
    repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    repo.store_all_resources(src_repo)
    return repo


def test_cli_checkout_simple(dir_repo):
    """Test grr_manage checkout simple invocation."""

    res = dir_repo.get_resource("sub/two")  # NOSONAR
    for fname, _, _ in dir_repo.get_files(res):
        filepath = dir_repo._get_file_path(res, fname)
        filepath.touch()
    assert not dir_repo.check_manifest_timestamps(res)

    _run_checkout_command(dir_repo)
    assert dir_repo.check_manifest_timestamps(res)


def test_cli_checkout_dry_run(dir_repo):
    """Test grr_manage checkout simple invocation."""

    res = dir_repo.get_resource("sub/two")
    for fname, _, _ in dir_repo.get_files(res):
        filepath = dir_repo._get_file_path(res, fname)
        filepath.touch()
    assert not dir_repo.check_manifest_timestamps(res)

    _run_checkout_command(dir_repo, dry_run=True)
    assert not dir_repo.check_manifest_timestamps(res)

    _run_checkout_command(dir_repo, dry_run=False)
    assert dir_repo.check_manifest_timestamps(res)


def test_cli_checkout_with_same_resource(dir_repo):
    """Test grr_manage checkout simple invocation."""

    res = dir_repo.get_resource("sub/two")
    for fname, _, _ in dir_repo.get_files(res):
        filepath = dir_repo._get_file_path(res, fname)
        filepath.touch()
    assert not dir_repo.check_manifest_timestamps(res)

    _run_checkout_command(dir_repo, resource="sub/two")
    assert dir_repo.check_manifest_timestamps(res)


def test_cli_checkout_with_other_resource(dir_repo):
    """Test grr_manage checkout simple invocation."""

    res = dir_repo.get_resource("sub/two")
    for fname, _, _ in dir_repo.get_files(res):
        filepath = dir_repo._get_file_path(res, fname)
        filepath.touch()
    assert not dir_repo.check_manifest_timestamps(res)

    _run_checkout_command(dir_repo, resource="one")
    assert not dir_repo.check_manifest_timestamps(res)
