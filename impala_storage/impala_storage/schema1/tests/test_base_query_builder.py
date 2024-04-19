# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
from box import Box

from dae.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData, GenotypeDataStudy
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf
from impala_storage.schema1.family_variants_query_builder import (
    FamilyVariantsQueryBuilder,
)
from impala_storage.schema1.impala_genotype_storage import ImpalaGenotypeStorage
from impala_storage.schema1.impala_variants import ImpalaVariants


@pytest.fixture(scope="module")
def impala_storage() -> ImpalaGenotypeStorage:
    storage_config = Box({
        "id": "genotype_impala",
        "storage_type": "impala",
        "hdfs": {
            "base_dir": "/tmp/test_data",
            "host": "localhost",
            "port": 8020,
            "replication": 1,
        },
        "impala": {
            "db": "impala_storage_test_db",
            "hosts": [
                "localhost",
            ],
            "pool_size": 3,
            "port": 21050,
        },
    })
    return ImpalaGenotypeStorage(storage_config)


@pytest.fixture(scope="module")
def t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
    impala_storage: ImpalaGenotypeStorage,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_instance")
    gpf_instance = t4c8_gpf(root_path, impala_storage)
    return gpf_instance


@pytest.fixture(scope="module")
def t4c8_study_1(
    t4c8_instance: GPFInstance,
) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT  QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   4    .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/1  0/2  0/2
chr1   54   .  T   C    .    .      .    GT     0/1  0/1  0/1 0/1  0/0  0/1
chr1   90   .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/1  0/2  0/1
chr1   100  .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/2  0/2  0/0
chr1   119  .  A   G,C  .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
chr1   122  .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/2  0/2  0/2
        """)

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "frequency_bin": {
                "rare_boundary": 25.0,
            },
            "coding_bin": {
                "coding_effect_types": [
                    "frame-shift",
                    "noStart",
                    "missense",
                    "synonymous",
                ],
            },
            "family_bin": {
                "family_bin_size": 2,
            },
        },
    }

    study = vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
    )
    return study


@pytest.fixture(scope="module")
def impala_variants(
    t4c8_study_1: GenotypeData,
) -> ImpalaVariants:
    assert isinstance(t4c8_study_1, GenotypeDataStudy)
    variants = t4c8_study_1._backend
    assert isinstance(variants, ImpalaVariants)
    return variants


@pytest.fixture(scope="module")
def impala_query_builder(
    impala_variants: ImpalaVariants,
) -> FamilyVariantsQueryBuilder:
    assert impala_variants.schema is not None
    query_builder = FamilyVariantsQueryBuilder(
        impala_variants.db,
        impala_variants.variants_table,
        impala_variants.pedigree_table,
        impala_variants.schema,
        impala_variants.table_properties,
        impala_variants.pedigree_schema,
        impala_variants.families,
        gene_models=impala_variants.gene_models,
        do_join=True,
    )
    return query_builder


def test_build_frequency_bin_heuristic(
    impala_query_builder: FamilyVariantsQueryBuilder,
) -> None:
    result = impala_query_builder._build_frequency_bin_heuristic(
        inheritance=[
            "not possible_denovo and not possible_omission",
            "any(missing,omission,mendelian,denovo)",
        ],
        ultra_rare=None,
        real_attr_filter=[
            ("genome_genomad_v3_af_percent", (None, 100.0)),
        ],
    )
    assert result == ""
