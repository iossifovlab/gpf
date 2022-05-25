import gzip

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.test_tools import build_test_repos
from dae.genomic_resources.test_tools import run_test_on_all_repos


def test_all_repo_types(tmp_path):

    brehGz = gzip.compress(b'breh')
    test_repos = build_test_repos(tmp_path, {
        "one": {
            GR_CONF_FILE_NAME: "opaa",
            "data.txt": "breh",
            "data.txt.gz": brehGz
        }
    })

    run_test_on_all_repos(
        test_repos, "is_file_list_ok",
        lambda repo: {GR_CONF_FILE_NAME, "data.txt", "data.txt.gz"} ==
        {entry.name for entry in repo.get_resource("one").get_manifest()}
    )

    run_test_on_all_repos(
        test_repos, "is_file_content_ok",
        lambda repo: repo.get_resource(
            "one").get_file_content("data.txt") == "breh"
    )

    run_test_on_all_repos(
        test_repos, "is_compressed_file_content_ok",
        lambda repo: repo.get_resource("one").get_file_content(
            "data.txt.gz", uncompress=False, mode="b") == brehGz
    )

    run_test_on_all_repos(
        test_repos, "is_uncompressed_file_content_ok",
        lambda repo: repo.get_resource("one").get_file_content(
            "data.txt.gz", uncompress=True, mode="t") == "breh"
    )

    def is_binary_ok(repo):
        with repo.get_resource("one").open_raw_file("data.txt", "rb") as F:
            return isinstance(F.read(10), bytes)
    run_test_on_all_repos(test_repos, "is_binary_ok", is_binary_ok)

    def is_text_ok(repo):
        with repo.get_resource("one").open_raw_file("data.txt", "rt") as F:
            return isinstance(F.read(10), str)
    run_test_on_all_repos(test_repos, "is_text_ok", is_text_ok)
