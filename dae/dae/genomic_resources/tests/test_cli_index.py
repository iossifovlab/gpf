"""Test grr_manage checkout command."""
# pylint: disable=protected-access,redefined-outer-name
import pytest

from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.cli import _run_index_command
from dae.genomic_resources.repository_helpers import RepositoryWorkflowHelper


@pytest.fixture
def repo_helper(tmp_path):
    """Fixture for directory repository."""

    demo_gtf_content = "TP53\tchr3\t300\t200"
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: ["", "2021-11-20T00:00:56+00:00"],
            "data.txt": ["alabala", "2021-11-20T00:00:56+00:00"],
        },
        "sub": {
            "two(1.0)": {
                GR_CONF_FILE_NAME: ["type: gene_models\nfile: genes.gtf",
                                    "2021-11-20T00:00:56+00:00"],
                "genes.txt": demo_gtf_content
            }
        }
    })
    repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    repo.store_all_resources(src_repo)

    helper = RepositoryWorkflowHelper(repo)
    return helper


def test_cli_index_simple(repo_helper):
    """Test grr_manage index simple invocation."""
    dir_repo = repo_helper.repo

    res = dir_repo.get_resource("sub/two")
    for fname, _, _ in dir_repo.collect_resource_files(res):
        filepath = dir_repo.get_filepath(res, fname)
        filepath.write_bytes(b"")

    assert not repo_helper.check_manifest_timestamps(res)

    _run_index_command(dir_repo)

    assert repo_helper.check_manifest_timestamps(res)


def test_cli_index_with_dry_run(repo_helper):
    """Test grr_manage index with dry_run invocation."""
    dir_repo = repo_helper.repo

    res = dir_repo.get_resource("sub/two")
    for fname, _, _ in dir_repo.collect_resource_files(res):
        filepath = dir_repo.get_filepath(res, fname)
        filepath.write_bytes(b"")
    assert not repo_helper.check_manifest_timestamps(res)

    _run_index_command(dir_repo, dry_run=True)
    assert not repo_helper.check_manifest_timestamps(res)

    _run_index_command(dir_repo, dry_run=False)
    assert repo_helper.check_manifest_timestamps(res)
