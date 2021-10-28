import pytest

import numpy as np

from dae.variants.core import Allele
from dae.backends.cnv.loader import CNVLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.configuration.gpf_config_parser import FrozenBox
from dae.utils.regions import Region


@pytest.fixture(scope="session")
def cnv_loader(
        fixture_dirname, genome_2013, annotation_pipeline_internal):

    families_filename = fixture_dirname("backends/cnv_ped.txt")
    variants_filename = fixture_dirname("backends/cnv_variants.txt")

    families_loader = FamiliesLoader(
        families_filename, **{"ped_file_format": "simple"})
    families = families_loader.load()

    variants_loader = CNVLoader(
        families, variants_filename, genome_2013.get_genomic_sequence())

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    return families_loader, variants_loader


@pytest.fixture(scope="session")
def cnv_raw(cnv_loader):
    _families_loader, variants_loader = cnv_loader
    fvars = RawMemoryVariants([variants_loader], variants_loader.families)
    return fvars


@pytest.fixture(scope="session")
def cnv_impala(
        request,
        cnv_loader,
        genomes_db_2013,
        hdfs_host,
        impala_host,
        impala_genotype_storage,
        reimport,
        cleanup,
        data_import):

    from dae.backends.impala.impala_helpers import ImpalaHelpers

    impala_helpers = ImpalaHelpers(
        impala_hosts=[impala_host], impala_port=21050)

    study_id = "cnv_test"

    (variant_table, pedigree_table) = \
        impala_genotype_storage.study_tables(
            FrozenBox({"id": study_id}))

    if reimport or \
            not impala_helpers.check_table(
                "impala_test_db", variant_table) or \
            not impala_helpers.check_table(
                "impala_test_db", pedigree_table):

        from dae.backends.impala.hdfs_helpers import HdfsHelpers

        hdfs = HdfsHelpers(hdfs_host, 8020)

        temp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
        hdfs.mkdir(temp_dirname)

        families_loader, variants_loader = cnv_loader
        impala_genotype_storage.simple_study_import(
            study_id,
            families_loader=families_loader,
            variant_loaders=[variants_loader],
            output=temp_dirname,
            include_reference=True)

    fvars = impala_genotype_storage.build_backend(
        FrozenBox({"id": study_id}), genomes_db_2013
    )

    return fvars


def test_cnv_impala(cnv_impala):
    vs = cnv_impala.query_variants(
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
        inheritance="denovo"
    )
    vs = list(vs)

    print(vs)

    for v in vs:
        assert v.alt_alleles
        for aa in v.alt_alleles:
            print(aa)
            assert Allele.Type.is_cnv(aa.allele_type)
    assert len(vs) == 12


def test_cnv_impala_region_query(cnv_impala):
    vs = cnv_impala.query_variants(
        regions=[
            Region("1", 1600000, 1620000)
        ],
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
        inheritance="denovo"
    )
    assert len(list(vs)) == 1
    vs = cnv_impala.query_variants(
        regions=[
            Region("1", 1600000, 1630000)
        ],
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
        inheritance="denovo"
    )
    assert len(list(vs)) == 2
    vs = cnv_impala.query_variants(
        regions=[
            Region("1", 1000000, 2000000)
        ],
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
        inheritance="denovo"
    )
    assert len(list(vs)) == 2


def test_cnv_best_state_X(cnv_raw):
    vs = cnv_raw.query_variants(
        effect_types=["CNV+", "CNV-"],
        variant_type="cnv+ or cnv-",
    )
    vs = [v for v in vs if v.chrom == "X"]

    assert len(vs) == 2
    for v in vs:
        assert v.alt_alleles
        for aa in v.alt_alleles:
            assert Allele.Type.is_cnv(aa.allele_type)

    assert np.array_equal(
        vs[0].best_state,
        np.asarray([
            [2, 1, 0, 2],
            [0, 0, 1, 0]
        ])
    )

    assert np.array_equal(
        vs[1].best_state,
        np.asarray([
            [2, 1, 0, 2],
            [0, 0, 1, 0]
        ])
    )
