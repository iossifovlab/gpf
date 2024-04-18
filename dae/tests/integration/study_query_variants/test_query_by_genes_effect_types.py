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
        familyId  personId  dadId  momId  sex  status  role
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=foo>
##contig=<ID=bar>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1
foo    3   .  A   G     .    .      .    GT     0/0  0/1  0/0
foo    4   .  C   G     .    .      .    GT     0/0  0/1  0/0
foo    7   .  A   G     .    .      .    GT     1/1  1/1  0/0
foo    9   .  A   G     .    .      .    GT     1/1  1/1  0/0
foo    13  .  G   C     .    .      .    GT     1/1  1/1  0/0
foo    14  .  C   T     .    .      .    GT     1/1  1/1  0/0
foo    15  .  C   A     .    .      .    GT     1/1  1/1  0/0
foo    17  .  T   A     .    .      .    GT     1/1  1/1  0/0
foo    18  .  C   A     .    .      .    GT     1/1  1/1  0/0
bar    16  .  C   A     .    .      .    GT     1/1  1/1  0/0
        """)

    study = vcf_study(
        root_path,
        "effects_trio_vcf", pathlib.Path(ped_path),
        [pathlib.Path(vcf_path)],
        gpf_instance)
    return study


# (foo:3 A->G f1 000/010,
#     [intergenic!intergenic:intergenic]),
# (foo:4 C->G f1 000/010,
#     [noStart!g1:noStart!tx1:g1:noStart:2|tx2:g1:noStart:0]),
# (foo:7 A->G f1 110/110,
#     [splice-site!g1:splice-site!tx1:g1:splice-site:2/2]),
# (foo:9 A->G f1 110/110,
#     [intron!g1:intron!tx1:g1:intron:1/1[2]]),
# (foo:13 G->C f1 110/110,
#     [splice-site!g1:splice-site!tx1:g1:splice-site:2/2]),
# (foo:14 C->T f1 110/110,
#     [missense!g1:missense!tx1:g1:missense:2/2(Pro->Ser)]),
# (foo:15 C->A f1 110/110,
#     [noEnd!g1:noEnd!tx1:g1:noEnd:2]),
# (foo:17 T->A f1 110/110,
#     [noEnd!g1:noEnd!tx1:g1:noEnd:2]),
# (foo:18 C->A f1 110/110,
#     [intergenic!intergenic:intergenic]),
# (bar:16 C->A f1 110/110,
#     [5'UTR!g2:5'UTR!tx3:g2:5'UTR:1])]
@pytest.mark.parametrize(
    "effects,genes,count",
    [
        (None, None, 10),
        ([], None, 0),
        (None, [], 0),
        ([], [], 0),
        (None, ["g1"], 7),
        (None, ["g2"], 1),
        (None, ["g1", "g2"], 8),
        (None, ["G1"], 0),
        (["intergenic"], None, 2),
        (["noStart"], None, 1),
        (["noEnd"], None, 2),
        (["intron"], None, 1),
        (["splice-site"], None, 2),
        (["missense"], None, 1),
        (["5'UTR"], None, 1),
        (["5'UTR"], ["g1"], 0),
        (["5'UTR"], ["g2"], 1),
        (["5'UTR"], ["g1", "g2"], 1),
        (["missense", "5'UTR"], ["g1", "g2"], 2),
        (["noEnd", "splice-site", "5'UTR"], ["g1"], 4),
    ],
)
def test_single_alt_allele_effects(
    imported_study: GenotypeData,
    effects: Optional[list[str]], genes: Optional[list[str]], count: int,
) -> None:

    vs = list(imported_study.query_variants(genes=genes, effect_types=effects))
    gefs = [(v, v.effects) for v in vs]
    print(gefs)

    assert count == len(vs)
