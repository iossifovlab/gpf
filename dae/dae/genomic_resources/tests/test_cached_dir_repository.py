import pathlib
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo

from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.cached_repository import CachingDirectoryRepo, GenomicResourceCachedRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources import GenomicResource


def test_cached_repository(tmp_path):

    demo_gtf_content = "TP53\tchr3\t300\t200"
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: ["type: gene_models\nfile: genes.gtf",
                                    '2021-11-20T00:00:56'],
                "genes.txt": demo_gtf_content
            }
        }
    })
    cache_repo = GenomicResourceCachedRepo(
        src_repo, tmp_path)

    def resource_set(repo):
        return {
            (gr.resource_id, gr.version)
            for gr in repo.get_all_resources()
        }

    assert resource_set(src_repo) == resource_set(cache_repo)

    cached_resource = cache_repo.get_resource("sub/two")
    assert isinstance(cached_resource, GenomicResource)
    assert cached_resource.get_file_content("genes.txt") == demo_gtf_content

    src_resource = src_repo.get_resource("sub/two")

    cache_manifest = cached_resource.get_manifest()
    src_manifest = src_resource.get_manifest()

    assert cache_manifest == src_manifest


def test_caching_dir_repository(tmp_path):

    demo_gtf_content = "TP53\tchr3\t300\t200"
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: ["type: gene_models\nfile: genes.gtf",
                                    '2021-11-20T00:00:56'],
                "genes.txt": demo_gtf_content
            }
        }
    })
    cache_repo = CachingDirectoryRepo(
        'dir', directory=tmp_path, remote_repo=src_repo)

    cache_resource = cache_repo.get_resource("sub/two")
    src_resource = src_repo.get_resource("sub/two")

    cache_manifest = cache_resource.get_manifest()
    src_manifest = src_resource.get_manifest()

    assert cache_manifest == src_manifest


def test_caching_dir_repository_resource_update(tmp_path):

    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: [
                    "",
                    "2021-11-19T23:22:51"
                ],
            }
        }
    })

    dir_repo = GenomicResourceDirRepo("dir", directory=tmp_path/"dir")
    dir_repo.store_all_resources(src_repo)

    cache_repo1 = CachingDirectoryRepo(
        'cache1', directory=tmp_path / "t1", remote_repo=dir_repo)

    cache_repo2 = CachingDirectoryRepo(
        'cache2', directory=tmp_path / "t2", remote_repo=dir_repo)

    gr1 = cache_repo1.get_resource("sub/two")
    gr2 = cache_repo2.get_resource("sub/two")

    assert gr1.get_manifest() == gr2.get_manifest()

    res = dir_repo.get_resource("sub/two")
    dirname = pathlib.Path(dir_repo.get_genomic_resource_dir(res))
    for filename, _size, _mod_time in res.get_files():
        path = dirname / filename
        path.touch()

    dir_repo.save_manifest(res, dir_repo.build_manifest(res))

    assert res.get_manifest() != gr1.get_manifest()
    assert res.get_manifest() != gr2.get_manifest()

    gr1 = cache_repo1.get_resource("sub/two")
    assert res.get_manifest() == gr1.get_manifest()

    gr2 = cache_repo2.get_resource("sub/two")
    assert res.get_manifest() == gr2.get_manifest()

# def test_dir_repository_resource_update_delete(tmp_path):

#     src_repo = GenomicResourceEmbededRepo("src", content={
#         "one": {
#             GR_CONF_FILE_NAME: "",
#             "data.txt": "alabala",
#             "alabala.txt": "alabala",
#         },
#     })

#     dir_repo1 = CachingDirectoryRepo(
#         'dir1', directory=tmp_path / "t1", remote_repo=src_repo)
#     dir_repo1.store_all_resources(src_repo)

#     dir_repo2 = CachingDirectoryRepo(
#         'dir2', directory=tmp_path / "t2", remote_repo=src_repo)
#     dir_repo2.store_all_resources(src_repo)

#     gr1 = dir_repo1.get_resource("one")
#     gr2 = dir_repo2.get_resource("one")

#     assert gr1.get_manifest() == gr2.get_manifest()
#     assert any([f.name == "alabala.txt" for f in gr1.get_manifest()])
#     assert any([f.name == "alabala.txt" for f in gr2.get_manifest()])

#     dirname = pathlib.Path(dir_repo1.get_genomic_resource_dir(gr1))
#     path = dirname / "alabala.txt"
#     path.unlink()

#     manifest = gr1.build_manifest()
#     print(manifest)
#     assert any([f.name != "alabala.txt" for f in manifest])

#     gr1.save_manifest(manifest)

#     assert gr1.get_manifest() != gr2.get_manifest()

#     dir_repo2.update_resource(gr1)
#     assert gr1.get_manifest() == gr2.get_manifest()


# def test_dir_repository_file_exists(tmp_path):
#     src_repo = GenomicResourceEmbededRepo("src", content={
#         "one": {
#             GR_CONF_FILE_NAME: "",
#             "data.txt": "alabala",
#             "alabala.txt": "alabala",
#         },
#     })

#     repo = CachingDirectoryRepo(
#         'dir', directory=tmp_path / "t1", remote_repo=src_repo)
#     repo.store_all_resources(src_repo)
#     res = repo.get_resource("one")

#     assert repo.file_exists(res, GR_CONF_FILE_NAME)
#     assert not repo.file_exists(res, "missing_file")
#     assert res.file_exists("data.txt")
