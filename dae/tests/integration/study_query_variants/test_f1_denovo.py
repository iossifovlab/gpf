# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import cast

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyAllele


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
bar    7   .  A   C,G,T .    .      .    GT     1/0 0/0 0/. 0/2
bar    8   .  A   T,C,G .    .      .    GT     0/0 0/0 0/1 0/0
bar    9   .  A   T,C,G .    .      .    GT     0/1 0/1 0/1 0/2
        """)

    return vcf_study(
        root_path,
        f"effects_trio_vcf_{genotype_storage.storage_id}",
        pathlib.Path(ped_path),
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


# --------------------------------------------------------------
# bar:7 A->C synonymous!g2:synonymous!tx3:g2:synonymous:3/3
# bar:7 A->G missense!g2:missense!tx3:g2:missense:3/3(Lys->Asn)
# bar:7 A->T synonymous!g2:synonymous!tx3:g2:synonymous:3/3
# --------------------------------------------------------------
# bar:8 A->C missense!g2:missense!tx3:g2:missense:3/3(Lys->Arg)
# bar:8 A->G missense!g2:missense!tx3:g2:missense:3/3(Lys->Thr)
# bar:8 A->T synonymous!g2:synonymous!tx3:g2:synonymous:3/3
# --------------------------------------------------------------
# bar:9 A->C missense!g2:missense!tx3:g2:missense:3/3(Lys->Glu)
# bar:9 A->G missense!g2:missense!tx3:g2:missense:3/3(Lys->Gln)
# bar:9 A->T synonymous!g2:synonymous!tx3:g2:synonymous:3/3
# --------------------------------------------------------------


@pytest.mark.parametrize(
    "position, effects, inheritance, count",
    [
        (7, None, None, 1),
        (7, None, "denovo", 1),
        (7, ["synonymous"], "denovo", 0),
        (7, ["missense"], "denovo", 1),
        (7, None, "mendelian", 1),
    ],
)
def test_partially_known_denovo(
    imported_study: GenotypeData,
    position: int,
    effects: list[str] | None,
    inheritance: str,
    count: int,
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance,
        return_unknown=True,
        return_reference=True))
    gefs = [(v, v.effects) for v in vs]
    print(gefs)

    assert len(vs) == count


@pytest.mark.parametrize(
    "position, inheritance, effects, count",
    [
        # We check all ref and alt alleles since return_reference=True.
        # For the ref allele the inheritance is 'mendelian'.
        # For the alt allele the inheritance is 'denovo'.
        (8, None, None, 1),
        (8, "unknown", None, 1),
        (8, "mendelian", None, 1),
        (8, "mendelian", ["synonymous"], 0),
        (8, "mendelian", ["missense"], 0),
        (8, None, ["synonymous"], 1),
        (8, None, ["missense"], 0),
        (8, "denovo", ["synonymous"], 1),
        # The ref allele match the query so we return the variant.
        (8, "not denovo ", None, 1),
    ],
)
def test_f1_canonical_denovo(
    imported_study: GenotypeData,
    position: int,
    effects: list[str] | None,
    inheritance: str,
    count: int,
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance,
        return_unknown=True,
        return_reference=True))
    gefs = [(v, v.effects) for v in vs]
    print(gefs)

    assert len(vs) == count


@pytest.mark.parametrize(
    "position, inheritance, effects, count",
    [
        (9, None, None, 1),
        (9, "denovo", ["synonymous"], 0),
        (9, "denovo", ["missense"], 1),
        (9, "mendelian", ["synonymous"], 1),
        (9, "mendelian", ["missense"], 0),
    ],
)
def test_f1_simple(
    imported_study: GenotypeData,
    position: int,
    effects: list[str] | None,
    inheritance: str,
    count: int,
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        effect_types=effects,
        inheritance=inheritance,
        return_unknown=True,
        return_reference=True))
    gefs = [(v, v.effects) for v in vs]
    print(gefs)

    assert len(vs) == count


@pytest.mark.parametrize(
    "position,inheritance,return_reference,return_unknown,count",
    [
        (8, None, True, True, 1),
        (8, None, False, False, 1),  # find all
        (8, "denovo", False, False, 1),  # find denovo
        (8, "denovo", True, True, 1),  # find denovo
        (8, "omission", False, False, 0),  # find omission
        (8, "omission", True, True, 0),  # find omission
        (8, "mendelian", False, False, 0),
        (8, "mendelian", True, False, 1),
        (8, "mendelian", True, True, 1),
        (8, "not denovo and not omission and not unknown and not mendelian",
         False, False, 0),
        (8, "not denovo and not omission and not unknown and not mendelian",
         True, False, 0),
        (8, "not denovo and not omission",
         False, False, 0),
        (8, "not denovo and not omission",
         True, True, 1),
    ],
)
def test_f1_canonical_denovo_return_reference_or_unknown(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    return_reference: bool,  # noqa: FBT001
    return_unknown: bool,  # noqa: FBT001
    count: int,
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        inheritance=inheritance,
        return_unknown=return_unknown,
        return_reference=return_reference))
    for v in vs:
        print(100 * "-")
        for aa in v.alleles:
            print(aa, cast(FamilyAllele, aa).inheritance_in_members)

    assert len(vs) == count


@pytest.mark.parametrize(
    "position,inheritance,return_reference,return_unknown,count",
    [
        (7, None, True, True, 1),
        (7, None, False, False, 1),
        (7, "denovo", False, False, 1),
        (7, "omission", False, False, 0),
        (7, "mendelian", False, False, 0),
        (7, "mendelian", True, False, 1),
        (7, "mendelian", True, True, 1),
        (7, "not denovo or not omission", False, False, 1),
    ],
)
def test_f1_partially_unknown_denovo_return_reference_or_unknown(
    imported_study: GenotypeData,
    position: int,
    inheritance: str,
    return_reference: bool,  # noqa: FBT001
    return_unknown: bool,  # noqa: FBT001
    count: int,
) -> None:
    region = Region("bar", position, position)
    vs = list(imported_study.query_variants(
        regions=[region],
        inheritance=inheritance,
        return_unknown=return_unknown,
        return_reference=return_reference))
    for v in vs:
        print(100 * "-")
        for aa in v.alleles:
            print(aa, cast(FamilyAllele, aa).inheritance_in_members)

    assert len(vs) == count
