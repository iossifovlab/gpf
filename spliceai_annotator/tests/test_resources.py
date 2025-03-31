# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.genomic_resources.repository import GenomicResourceRepo


def test_genomic_resources_repo(
        spliceai_grr: GenomicResourceRepo,
) -> None:
    grr = spliceai_grr
    assert grr is not None
    assert grr.get_resource("hg19/genome_10") is not None
    assert grr.get_resource("hg19/gene_models_small") is not None
