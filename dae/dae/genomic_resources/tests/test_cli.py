import os
from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository import GR_CONTENTS_FILE_NAME
from dae.genomic_resources.cli import cli_manage, cli_cache_repo


def test_cli_manage(tmp_path):

    demo_gtf_content = "TP53\tchr3\t300\t200".encode('utf-8')
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two[1.0]": {
                GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                "genes.txt": demo_gtf_content
            }
        }
    })
    dir_repo = GenomicResourceDirRepo('dir', directory=tmp_path)
    dir_repo.store_all_resources(src_repo)

    assert not (tmp_path / GR_CONTENTS_FILE_NAME).is_file()
    cli_manage(["index", str(tmp_path)])
    assert (tmp_path / GR_CONTENTS_FILE_NAME).is_file()


def test_cli_cache_instance(mocker, fixture_path, temp_cache_dir):
    definition = {
        "id": "local",
        "type": "directory",
        "directory": fixture_path("repo"),
        "cache_dir": temp_cache_dir
    }
    mocked = mocker.patch("dae.genomic_resources.cli.load_definition_file")
    mocked.return_value = definition

    cli_cache_repo([
        "--definition",
        "blank",
        "--instance",
        fixture_path("gpf_instance.yaml")
    ])

    paths = [
        ("genomes", "mock"),
        ("gene_models", "mock"),
        ("liftover", "mock"),
        ("scores", "mock1"),
        ("scores", "mock2"),
    ]
    for path in paths:
        full_path = os.path.join(
            temp_cache_dir,
            "local",
            *path,
            "genomic_resource.yaml"
        )
        assert os.path.exists(full_path)

    assert not os.path.exists(os.path.join(
        temp_cache_dir,
        "local",
        "scores",
        "mock_extra",
        "genomic_resource.yaml"
    ))


def test_cli_cache_annotation(mocker, fixture_path, temp_cache_dir):
    definition = {
        "id": "local",
        "type": "directory",
        "directory": fixture_path("repo"),
        "cache_dir": temp_cache_dir
    }
    mocked = mocker.patch("dae.genomic_resources.cli.load_definition_file")
    mocked.return_value = definition

    cli_cache_repo([
        "--definition",
        "blank",
        "--annotation",
        fixture_path("annotation.yaml")
    ])

    paths = [
        ("genomes", "mock"),
        ("liftover", "mock"),
        ("scores", "mock1"),
        ("scores", "mock2"),
    ]
    for path in paths:
        full_path = os.path.join(
            temp_cache_dir,
            "local",
            *path,
            "genomic_resource.yaml"
        )
        assert os.path.exists(full_path)

    assert not os.path.exists(os.path.join(
        temp_cache_dir,
        "local",
        "gene_models",
        "mock",
        "genomic_resource.yaml"
    ))
    assert not os.path.exists(os.path.join(
        temp_cache_dir,
        "local",
        "scores",
        "mock_extra",
        "genomic_resource.yaml"
    ))
