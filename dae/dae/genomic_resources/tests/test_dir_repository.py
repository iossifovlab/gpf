import pathlib

from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources import GenomicResource


def test_dir_repository(tmp_path):

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
    dir_repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    dir_repo.store_all_resources(src_repo)

    def resource_set(repo):
        return {
            (gr.resource_id, gr.version)
            for gr in repo.get_all_resources()
        }

    assert resource_set(src_repo) == resource_set(dir_repo)
    assert isinstance(dir_repo.get_resource("sub/two"), GenomicResource)
    assert dir_repo.get_resource("sub/two").get_file_content("genes.txt") == \
        demo_gtf_content

    dir_resource = dir_repo.get_resource("sub/two")
    src_resource = src_repo.get_resource("sub/two")

    dir_manifest = dir_resource.get_manifest()
    src_manifest = src_resource.get_manifest()

    assert dir_manifest == src_manifest

    dirname = pathlib.Path(dir_repo.get_genomic_resource_dir(dir_resource))

    for filename, size, mod_time in dir_resource.get_files():
        path = dirname / filename
        path.touch()

    dir_manifest = dir_resource.build_manifest()

    assert dir_manifest != src_manifest


def test_dir_repository_resource_update(tmp_path):

    demo_gtf_content = "TP53\tchr3\t300\t200".encode('utf-8')
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: ["type: gene_models\nfile: genes.gtf",
                                    '2021-11-19T23:22:51'],
                "genes.gtf": demo_gtf_content
            }
        }
    })

    dir_repo1 = GenomicResourceDirRepo('dir', directory=tmp_path / "t1")
    dir_repo1.store_all_resources(src_repo)

    dir_repo2 = GenomicResourceDirRepo('dir', directory=tmp_path / "t2")
    dir_repo2.store_all_resources(src_repo)

    gr1 = dir_repo1.get_resource("sub/two")
    gr2 = dir_repo2.get_resource("sub/two")

    assert gr1.get_manifest() == gr2.get_manifest()

    dirname = pathlib.Path(dir_repo1.get_genomic_resource_dir(gr1))
    for filename, size, mod_time in gr1.get_files():
        path = dirname / filename
        path.touch()

    gr1.save_manifest(gr1.build_manifest())

    assert gr1.get_manifest() != gr2.get_manifest()


def test_dir_repository_file_exists(tmp_path):
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala",
            "alabala.txt": "alabala",
        },
    })

    repo = GenomicResourceDirRepo('dir', directory=tmp_path / "t1")
    repo.store_all_resources(src_repo)
    res = repo.get_resource("one")

    assert repo.file_exists(res, GR_CONF_FILE_NAME)
    assert not repo.file_exists(res, "missing_file")
    assert res.file_exists("data.txt")
