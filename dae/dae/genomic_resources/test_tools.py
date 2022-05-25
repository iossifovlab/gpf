from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.repository_helpers import RepositoryWorkflowHelper
from dae.genomic_resources.url_repository import GenomicResourceURLRepo


def build_a_test_resource(content: str):
    return GenomicResourceEmbededRepo("", content).get_resource("")


def convert_to_tab_separated(s: str):
    result = "\n".join(
        "\t".join(line.strip("\n\r").split())
        for line in s.split("\n")
        if line.strip("\r\n") != "")
    return result.replace("||", " ")


def build_test_repos(pth, content):
    dir_repo_path = pth / "dirRepo"
    emb_cache_path = pth / "embCache"
    url_cache_path = pth / "urlCache"
    url_repo_url = "file://" + str(dir_repo_path)

    emb_repo = GenomicResourceEmbededRepo("emb", content=content)

    dir_repo = GenomicResourceDirRepo("dir", directory=dir_repo_path)
    dir_repo.store_resource(emb_repo.get_resource("one"))

    repo_helper = RepositoryWorkflowHelper(dir_repo)
    repo_helper.update_repository_content_file()

    embeded_cached_repo = GenomicResourceCachedRepo(
        emb_repo, emb_cache_path)

    url_repo = GenomicResourceURLRepo("url", url=url_repo_url)
    url_cached_repo = GenomicResourceCachedRepo(
        url_repo, url_cache_path)

    return {"emb": emb_repo, "dir": dir_repo, "url_rep": url_repo,
            "emb_cached": embeded_cached_repo,
            "url_cached": url_cached_repo}


def run_test_on_all_repos(all_test_repos, test_name, test_function,
                          repo_names_that_should_fail=[]):
    for test_repo_name, test_repo in all_test_repos.items():
        print(100*"+")
        print(
            test_repo.repo_id, list(
                test_repo.get_resource("one").get_manifest()))
        print(100*"+")
        test_result = test_function(test_repo)
        if test_repo_name in repo_names_that_should_fail:
            assert not test_result, \
                f"{test_name} should fail with {test_repo_name}"
        else:
            assert test_result, \
                f"{test_name} should succeed with {test_repo_name}"
