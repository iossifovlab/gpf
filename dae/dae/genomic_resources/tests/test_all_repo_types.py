from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.url_repository import GenomicResourceURLRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
import gzip


def test_all_repo_types(tmp_path):

    dir_repo_path = tmp_path / "dirRepo"
    emb_cache_path = tmp_path / "embCache"
    url_cache_path = tmp_path / "urlCache"
    url_repo_url = "file://" + str(dir_repo_path)

    brehGz = gzip.compress(b'breh')
    embeded_repo = GenomicResourceEmbededRepo("emb", content={
        "one": {
            GR_CONF_FILE_NAME: "opaa",
            "data.txt": "breh",
            "data.txt.gz": brehGz}})

    dir_repo = GenomicResourceDirRepo("dir", directory=dir_repo_path)
    dir_repo.store_resource(embeded_repo.get_resource("one"))
    dir_repo.save_content_file()

    embeded_cached_repo = GenomicResourceCachedRepo(
        embeded_repo, emb_cache_path)

    url_repo = GenomicResourceURLRepo("url", url=url_repo_url)
    url_cached_repo = GenomicResourceCachedRepo(
        url_repo, url_cache_path)

    def is_file_list_ok(repo):
        return {GR_CONF_FILE_NAME, "data.txt", "data.txt.gz"} == \
            {fn for fn, _, _ in repo.get_resource("one").get_files()}

    assert is_file_list_ok(embeded_repo)
    assert is_file_list_ok(dir_repo)
    assert is_file_list_ok(embeded_cached_repo)
    assert is_file_list_ok(url_repo)
    assert is_file_list_ok(url_cached_repo)

    def is_file_content_ok(repo):
        return repo.get_resource("one").get_file_content("data.txt") == b"breh"

    assert is_file_content_ok(embeded_repo)
    assert is_file_content_ok(dir_repo)
    assert is_file_content_ok(embeded_cached_repo)
    assert is_file_content_ok(url_repo)
    assert is_file_content_ok(url_cached_repo)

    def is_compressed_file_content_ok(repo):
        gr = repo.get_resource("one")
        return gr.get_file_content("data.txt.gz", False) == brehGz

    assert is_compressed_file_content_ok(embeded_repo)
    assert is_compressed_file_content_ok(dir_repo)
    assert is_compressed_file_content_ok(embeded_cached_repo)
    assert is_compressed_file_content_ok(url_repo)
    assert is_compressed_file_content_ok(url_cached_repo)

    def is_uncompressed_file_content_ok(repo):
        gr = repo.get_resource("one")
        return gr.get_file_content("data.txt.gz") == b"breh"

    assert is_uncompressed_file_content_ok(embeded_repo)
    assert is_uncompressed_file_content_ok(dir_repo)
    assert is_uncompressed_file_content_ok(embeded_cached_repo)
    assert is_uncompressed_file_content_ok(url_repo)
    assert is_uncompressed_file_content_ok(url_cached_repo)

    def is_binary_ok(repo):
        with repo.get_resource("one").open_raw_file("data.txt", "rb") as F:
            return isinstance(F.read(10), bytes)

    assert is_binary_ok(embeded_repo)
    assert is_binary_ok(dir_repo)
    assert is_binary_ok(embeded_cached_repo)
    assert is_binary_ok(url_repo)
    assert is_binary_ok(url_cached_repo)

    def is_text_ok(repo):
        with repo.get_resource("one").open_raw_file("data.txt", "rt") as F:
            return isinstance(F.read(10), str)

    assert is_text_ok(embeded_repo)
    assert is_text_ok(dir_repo)
    assert is_text_ok(embeded_cached_repo)
    assert is_text_ok(url_repo)
    assert is_text_ok(url_cached_repo)
