# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.duckdb_storage.duckdb_genotype_storage import DuckDbGenotypeStorage
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage_registry import (
    get_genotype_storage_factory,
)
from dae.gpf_instance import GPFInstance
from dae.pedigrees.families_data import FamiliesData
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf


@pytest.fixture()
def duckdb_storage(
    tmp_path: pathlib.Path,
) -> DuckDbGenotypeStorage:
    storage_path = tmp_path / "duckdb_storage"
    storage_config = {
        "id": "duckdb_test",
        "storage_type": "duckdb2",
        "db": "duckdb_storage/test.duckdb",
        "base_dir": str(storage_path),
    }
    storage_factory = get_genotype_storage_factory("duckdb2")
    assert storage_factory is not None
    storage = storage_factory(storage_config)
    assert storage is not None
    assert isinstance(storage, DuckDbGenotypeStorage)
    return storage


@pytest.fixture()
def t4c8_instance(
    tmp_path: pathlib.Path,
    duckdb_storage: DuckDbGenotypeStorage,
) -> GPFInstance:
    root_path = tmp_path / "t4c8_instance"
    return t4c8_gpf(root_path, duckdb_storage)


@pytest.fixture()
def t4c8_genes(t4c8_instance: GPFInstance) -> GeneModels:
    return t4c8_instance.gene_models


@pytest.fixture()
def t4c8_genome(t4c8_instance: GPFInstance) -> ReferenceGenome:
    return t4c8_instance.reference_genome


@pytest.fixture()
def t4c8_study_1(
    t4c8_instance: GPFInstance,
) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir).parent
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
#CHROM POS  ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   54   .  T   C   .    .      .    GT     0/1  0/0  0/1 0/0  0/0  0/0
chr1   119  .  A   G,C .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
chr1   122  .  A   C   .    .      .    GT     0/0  1/0  0/0 0/0  0/0  0/0
        """)

    vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        t4c8_instance,
    )
    storage = t4c8_instance\
        .genotype_storages.get_genotype_storage("duckdb_test")
    assert storage is not None
    storage.shutdown()
    storage.start(read_only=True)
    t4c8_instance.reload()
    return t4c8_instance.get_genotype_data("study_1")


@pytest.fixture()
def t4c8_families_1(
    t4c8_study_1: GenotypeData,
) -> FamiliesData:
    return t4c8_study_1.families


@pytest.fixture()
def t4c8_study_2(
    t4c8_instance: GPFInstance,
) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_2" / "pedigree" / "in.ped",
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
        root_path / "study_2" / "vcf" / "in.vcf.gz",
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

    vcf_study(
        root_path,
        "study_2", ped_path, [vcf_path1],
        t4c8_instance,
        project_config_update=project_config_update,
    )
    storage = t4c8_instance\
        .genotype_storages.get_genotype_storage("duckdb_test")
    assert storage is not None
    storage.shutdown()
    storage.start(read_only=True)
    t4c8_instance.reload()
    return t4c8_instance.get_genotype_data("study_2")
