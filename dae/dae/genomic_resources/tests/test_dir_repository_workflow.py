"""Test directory repository workflow utils."""
# pylint: disable=protected-access,redefined-outer-name
import pytest

from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository_helpers import RepositoryWorkflowHelper


@pytest.fixture
def repo_helper(tmp_path):
    """Fixture for directory repository."""

    demo_gtf_content = "TP53\tchr3\t300\t200"
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: ["type: gene_models\nfile: genes.gtf",
                                    '2021-11-20T00:00:56+00:00'],
                "genes.txt": demo_gtf_content
            }
        }
    })
    repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    repo.store_all_resources(src_repo)
    helper = RepositoryWorkflowHelper(repo)
    return helper


def test_check_manifest_timestamps(repo_helper):
    """Test check for manifest timestamps."""

    res = repo_helper.repo.get_resource("sub/two")  # NOSONAR
    assert repo_helper.check_manifest_timestamps(res)

    for fname, _, _ in repo_helper.repo.collect_resource_files(res):
        filepath = repo_helper.repo.get_filepath(res, fname)
        filepath.touch()

    assert not repo_helper.check_manifest_timestamps(res)


def test_check_manifest_md5sums(repo_helper):
    """Test check for manifest md5sums."""

    res = repo_helper.repo.get_resource("sub/two")
    assert repo_helper.check_manifest_timestamps(res)

    assert repo_helper.check_manifest_md5sums(res)

    for fname, _, _ in repo_helper.repo.collect_resource_files(res):
        filepath = repo_helper.repo.get_filepath(res, fname)
        with open(filepath, "at", encoding="utf8") as outfile:
            outfile.write("\n")

    assert not repo_helper.check_manifest_md5sums(res)


def test_checkout_manifest_timestamps_simple(repo_helper):
    """Test that after timestamps checkout the manifest is ok."""
    res = repo_helper.repo.get_resource("sub/two")
    assert repo_helper.check_manifest_timestamps(res)

    for fname, _, _ in repo_helper.repo.collect_resource_files(res):
        filepath = repo_helper.repo.get_filepath(res, fname)
        filepath.touch()
    assert not repo_helper.check_manifest_timestamps(res)

    assert repo_helper.checkout_manifest_timestamps(res)
    assert repo_helper.check_manifest_timestamps(res)


def test_checkout_manifest_timestamps_fail_with_new_file(repo_helper):
    """Test that checkout fails when new file is found in the resource."""
    res = repo_helper.repo.get_resource("one")
    new_filepath = repo_helper.repo.get_filepath(res, "new_file.txt")
    with open(new_filepath, "wt", encoding="utf8") as outfile:
        outfile.write("new file\n")

    assert not repo_helper.checkout_manifest_timestamps(res)


def test_checkout_manifest_timestamps_fail_with_deleted_file(repo_helper):
    """Test that checkout fails when a file is deleted from the resource."""
    res = repo_helper.repo.get_resource("one")
    new_filepath = repo_helper.repo.get_filepath(res, "data.txt")
    new_filepath.unlink()

    assert not repo_helper.checkout_manifest_timestamps(res)
