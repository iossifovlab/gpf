import pytest
import os

import numpy as np

from dae.variants.attributes import VariantType
from dae.backends.cnv.loader import CNVLoader
from dae.pedigrees.loader import FamiliesLoader
from dae.backends.raw.loader import AnnotationPipelineDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.impala.parquet_io import ParquetManager, \
    NoPartitionDescriptor
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
        families, variants_filename, genome_2013)

    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    return variants_loader


@pytest.fixture(scope="session")
def cnv_raw(cnv_loader):
    fvars = RawMemoryVariants([cnv_loader], cnv_loader.families)
    return fvars


@pytest.fixture(scope="session")
def cnv_impala(
        request,
        cnv_loader,
        genomes_db_2013,
        hdfs_host,
        impala_genotype_storage):

    from dae.backends.impala.hdfs_helpers import HdfsHelpers

    hdfs = HdfsHelpers(hdfs_host, 8020)

    temp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
    hdfs.mkdir(temp_dirname)

    study_id = "cnv_test"
    parquet_filenames = ParquetManager.build_parquet_filenames(
        temp_dirname, bucket_index=2, study_id=study_id
    )

    assert parquet_filenames is not None
    print(parquet_filenames)

    ParquetManager.families_to_parquet(
        cnv_loader.families, parquet_filenames.pedigree
    )

    variants_dir = os.path.join(temp_dirname, "variants")
    partition_description = NoPartitionDescriptor(variants_dir)

    ParquetManager.variants_to_parquet(
        cnv_loader, partition_description
    )

    impala_genotype_storage.impala_load_dataset(
        study_id,
        variants_dir=os.path.dirname(parquet_filenames.variants),
        pedigree_file=parquet_filenames.pedigree,
    )

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
            assert VariantType.is_cnv(aa.variant_type)
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
            assert VariantType.is_cnv(aa.variant_type)

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
