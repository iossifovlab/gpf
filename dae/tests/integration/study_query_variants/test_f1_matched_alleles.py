# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.effect_annotation.effect import EffectGene
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
        tmp_path_factory: pytest.TempPathFactory,
        genotype_storage: GenotypeStorage) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        f"query_by_genes_effects_{genotype_storage.storage_id}")
    gpf_instance = foobar_gpf(root_path, genotype_storage)
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
##contig=<ID=bar>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom dad ch1 ch2
bar    7   .  A   C,G,T .    .      .    GT     0/0 0/1 0/1 0/2
bar    8   .  A   C,G,T .    .      .    GT     0/1 0/2 1/3 1/2
bar    9   .  A   C,G,T .    .      .    GT     0/1 0/2 1/3 1/2
bar    10  .  C   A,G,T .    .      .    GT     0/1 0/2 1/3 1/2
bar    11  .  G   A,C,T .    .      .    GT     0/1 0/2 1/3 1/2
bar    12  .  G   A,C,T .    .      .    GT     0/1 0/2 1/3 1/2
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


@pytest.mark.parametrize(
    "position,inheritance,effects,return_reference,matched_alleles",
    [
        (7, None, None, True, [0, 1, 2]),
        (7, None, None, False, [1, 2]),
        (7, "denovo", None, True, [2]),
        (7, "denovo", ["missense"], True, [2]),
        (7, None, ["missense"], True, [2]),
        (7, "denovo", None, False, [2]),
        (7, "denovo", ["missense"], False, [2]),
        (7, None, ["missense"], False, [2]),
        (7, "mendelian", ["synonymous"], True, [1]),
        (7, "mendelian", None, True, [0, 1]),
        (7, "mendelian", None, False, [1]),
    ],
)
def test_f1_matched_allele_indexes(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    effects: list[str] | None,
    return_reference: bool,
    matched_alleles: list[int],
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance,
        return_reference=return_reference))
    assert len(vs) == 1
    assert vs[0].matched_alleles_indexes == matched_alleles


@pytest.mark.parametrize(
    "position,inheritance,effects,matched_effects",
    [
        (7, None, None, set()),
        (7, "denovo", ["missense"], {EffectGene("g2", "missense")}),
        (7, "denovo", None, set()),
        (7, "mendelian", ["synonymous"], {EffectGene("g2", "synonymous")}),
        (7, "mendelian", None, set()),
        (7, None, ["missense", "synonymous"],
         {EffectGene("g2", "synonymous"), EffectGene("g2", "missense")}),
    ],
)
def test_f1_matched_gene_effects(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    effects: list[str] | None,
    matched_effects: set[EffectGene],
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance))
    assert len(vs) == 1

    assert vs[0].matched_gene_effects == matched_effects
