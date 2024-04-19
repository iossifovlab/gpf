# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import numpy as np
import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.acgt_import import acgt_gpf
from dae.variants.attributes import GeneticModel


@pytest.fixture(scope="module")
def quads_f1(
        tmp_path_factory: pytest.TempPathFactory,
        impala_genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"quads_f1_{impala_genotype_storage.storage_id}")
    gpf_instance = acgt_gpf(root_path, impala_genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId momId sex status role
        f1       mom      0     0     2   1      mom
        f1       dad      0     0     1   1      dad
        f1       ch1      dad   mom   2   2      prb
        f1       ch2      dad   mom   1   1      sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom dad ch1 ch2
chr1   1   .  A   C   .    .      .    GT     0/1 0/0 0/1 0/0
chr1   2   .  C   G   .    .      .    GT     0/0 0/1 0/1 0/0
        """)

    study = vcf_study(
        root_path,
        "effects_trio_vcf", pathlib.Path(ped_path),
        [pathlib.Path(vcf_path)],
        gpf_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "include_reference_genotypes": True,
                    "include_unknown_family_genotypes": True,
                    "include_unknown_person_genotypes": True,
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                },
            },
            "processing_config": {
                "include_reference": True,
            },
        })
    return study


def test_best_state_genetic_model(quads_f1: GenotypeData) -> None:

    best_state_expecteds = {
        1: np.array([[1, 2, 1, 2], [1, 0, 1, 0]], dtype=np.int8),
        2: np.array([[2, 1, 1, 2], [0, 1, 1, 0]], dtype=np.int8),
    }

    variants = list(quads_f1.query_variants())

    for variant in variants:
        assert np.all(
            variant.best_state == best_state_expecteds[variant.position])
    assert all(
        variant.genetic_model == GeneticModel.autosomal
        for variant in variants
    )
