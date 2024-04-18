# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf


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
bar    7   .  A   C,G,T .    .      .    GT     0/1 0/2 1/3 1/2
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
# bar:10 C->A missense!g2:missense!tx3:g2:missense:2/3(Trp->Cys)
# bar:10 C->G missense!g2:missense!tx3:g2:missense:2/3(Trp->Cys)
# bar:10 C->T nonsense!g2:nonsense!tx3:g2:nonsense:2/3(Trp->End)
# --------------------------------------------------------------
# bar:11 G->A missense!g2:missense!tx3:g2:missense:2/3(Trp->Leu)
# bar:11 G->C synonymous!g2:synonymous!tx3:g2:synonymous:2/3
# bar:11 G->T nonsense!g2:nonsense!tx3:g2:nonsense:2/3(Trp->End)
# --------------------------------------------------------------
# bar:12 G->A synonymous!g2:synonymous!tx3:g2:synonymous:2/3
# bar:12 G->C missense!g2:missense!tx3:g2:missense:2/3(Trp->Gly)
# bar:12 G->T missense!g2:missense!tx3:g2:missense:2/3(Trp->Arg)
# --------------------------------------------------------------


@pytest.mark.parametrize(
    "effects,genes,count",
    [
        (None, None, 6),
        ([], None, 0),
        (None, [], 0),
        ([], [], 0),
        (None, ["g1"], 0),
        (None, ["g2"], 6),
        (["intergenic"], None, 0),
        (["synonymous"], None, 5),
        (["missense"], None, 6),
        (["nonsense"], None, 2),
    ],
)
def test_query_varaints_gene_effects(
    effects: Optional[list[str]],
    genes: Optional[list[str]],
    count: int,
    imported_study: GenotypeData,
) -> None:

    vs = list(imported_study.query_variants(
        effect_types=effects,
        genes=genes))
    for v in vs:
        print(100 * "-")
        for aa in v.alt_alleles:
            print(aa, aa.effects)
    assert len(vs) == count


@pytest.mark.parametrize(
    "effects,genes,count",
    [
        (None, None, 6),
        ([], None, 0),
        (None, [], 0),
        ([], [], 0),
        (None, ["g1"], 0),
        (None, ["g2"], 6),
        (["intergenic"], None, 0),
        (["synonymous"], None, 5),
        (["missense"], None, 6),
        (["nonsense"], None, 2),
    ],
)
def test_query_summary_varaints_gene_effects(
    effects: Optional[list[str]],
    genes: Optional[list[str]],
    count: int,
    imported_study: GenotypeData,
) -> None:

    vs = list(imported_study.query_summary_variants(
        effect_types=effects,
        genes=genes))
    for v in vs:
        print(100 * "-")
        for aa in v.alt_alleles:
            print(aa, aa.effects)
    assert len(vs) == count
