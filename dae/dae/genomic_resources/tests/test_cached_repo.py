import pytest

from dae.genomic_resources.url_repository import GenomicResourceURLRepo
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_create_definition_with_cache(tmpdir):
    repo = build_genomic_resource_repository(
        {"cache_dir": tmpdir, "id": "bla", "type": "embeded",
         "content": {
             "one": {"genomic_resrouce.yaml"}
         }})
    assert isinstance(repo, GenomicResourceCachedRepo)


def test_get_cached_resource(tmpdir):
    child_repo = GenomicResourceEmbededRepo(
        "bla", {"one": {"genomic_resource.yaml": ""}})
    repo = GenomicResourceCachedRepo(child_repo, tmpdir)

    gr = repo.get_resource("one")
    assert gr


def test_cached_get_all_resources(tmpdir):

    demo_gtf_content = "TP53\tchr3\t300\t200".encode('utf-8')
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            '''
               The test is unstable with the resource below is unstable because
               the precision of the processor time is larger than the precisio
               of the file stamps. For example,

                ts = 1636242231.5675972 # this was returned by time.time()
                                        # in a failed run of the test.
                os.utime('a',(ts,ts))
                fs = pathlib.Path("a").stat().st_mtime
                print(f"{ts}\n{fs}")

                Results in:
                1636242231.5675972
                1636242231.567597
                '''
            "two-unstable[1.0]": {
                GR_CONF_FILE_NAME: "type: GeneModels\nfile: genes.gtf",
                "genes.txt": demo_gtf_content
            },
            "two[1.0]": {
                GR_CONF_FILE_NAME:
                    ["type: GeneModels\nfile: genes.gtf", 1636241590.2],
                "genes.txt": [demo_gtf_content, 1636241585.5]
            }
        }
    })

    cache_repo = GenomicResourceCachedRepo(src_repo, tmpdir)
    assert len(list(cache_repo.get_all_resources())) == 2

    src_gr = src_repo.get_resource("sub/two")
    cache_gr = cache_repo.get_resource("sub/two")

    assert src_gr.get_manifest() == cache_gr.get_manifest()
    assert src_gr.get_manifest() == cache_gr.build_manifest()

    assert len(list(cache_repo.get_all_resources())) == 3


def test_cache_all(tmpdir):

    demo_gtf_content = "TP53\tchr3\t300\t200".encode('utf-8')
    src_repo = GenomicResourceEmbededRepo("src", content={
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two-unstable[1.0]": {
                GR_CONF_FILE_NAME: "type: GeneModels\nfile: genes.gtf",
                "genes.txt": demo_gtf_content
            },
            "two[1.0]": {
                GR_CONF_FILE_NAME:
                    ["type: GeneModels\nfile: genes.gtf", 1636241590.2],
                "genes.txt": [demo_gtf_content, 1636241585.5]
            }
        }
    })

    cache_repo = GenomicResourceCachedRepo(src_repo, tmpdir)
    assert len(list(cache_repo.get_all_resources())) == 3
    cache_repo.cache_all_resources()

    assert len(list(cache_repo.get_all_resources())) == 6


@pytest.mark.parametrize("resource_id", [
    "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/"
    "gene_models/refGene_201309",

    "hg38/TESTCADD",
])
def test_cached_http_repo(
        resource_id, tmpdir, genomic_resource_fixture_http_repo):
    cached_repo = GenomicResourceCachedRepo(
        genomic_resource_fixture_http_repo, tmpdir)

    src_gr = genomic_resource_fixture_http_repo.get_resource(resource_id)
    assert src_gr is not None

    cached_gr = cached_repo.get_resource(resource_id)
    assert cached_gr is not None

    assert src_gr.get_manifest() == cached_gr.get_manifest()
    assert src_gr.get_manifest() == cached_gr.build_manifest()


@pytest.mark.parametrize("resource_id", [
    "hg19/GATK_ResourceBundle_5777_b37_phiX174/"
    "gene_models/refGene_v201309",
])
def test_cached_default_http_repo(
        resource_id, tmpdir):

    src_repo = GenomicResourceURLRepo(
        "default_http",
        "https://www.iossifovlab.com/distribution/public/"
        "genomic-resources-repository"
    )

    cached_repo = GenomicResourceCachedRepo(
        src_repo, tmpdir)

    src_gr = src_repo.get_resource(resource_id)
    assert src_gr is not None

    cached_gr = cached_repo.get_resource(resource_id)
    assert cached_gr is not None

    assert src_gr.get_manifest() == cached_gr.get_manifest()
    assert src_gr.get_manifest() == cached_gr.build_manifest()
