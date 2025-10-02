# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.testing import setup_denovo, setup_pedigree
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.dae.loader import DenovoLoader


@pytest.fixture(scope="module")
def edge_case_study(
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    root_path = tmp_path_factory.mktemp("edge_case")
    setup_pedigree(
        root_path / "study" / "in.ped",
        """
familyId personId       momId          dadId          sex status      role         sample_id      generated not_sequenced
fam1     fam1.p1        0              0              F   unaffected  mom          fam1.p1        False     False
fam1     fam1.p12       fam1.p2.mother fam1.p2        M   unaffected  half_sibling fam1.p12       False     False
fam1     fam1.p13       fam1.p1        fam1.p1.father M   unaffected  half_sibling fam1.p13       False     False
fam1     fam1.p14       fam1.p1        fam1.p1.father F   unaffected  half_sibling fam1.p14       False     False
fam1     fam1.p15       fam1.p1        fam1.p2        F   unaffected  sib          fam1.p15       False     False
fam1     fam1.p2        0              0              M   unaffected  dad          fam1.p2        False     False
fam1     fam1.p3        fam1.p1        fam1.p2        F   affected    prb          fam1.p3        False     False
fam1     fam1.p2.mother 0              0              F   unspecified unknown      fam1.p2.mother True      True
fam1     fam1.p1.father 0              0              M   unspecified unknown      fam1.p1.father True      True
        """)  # noqa: E501
    setup_denovo(
        root_path / "study" / "variants.tsv",
        """
personId        familyId        chrom   position        ref     alt
fam1.p3         fam1            chr1    54              T       C
        """)
    return f"{root_path}/study"


def test_edge_case(
    acgt_genome_38: ReferenceGenome,
    edge_case_study: str,
) -> None:
    families_loader = FamiliesLoader(f"{edge_case_study}/in.ped")
    families = families_loader.load()
    variants_loader = DenovoLoader(
        families,
        f"{edge_case_study}/variants.tsv",
        genome=acgt_genome_38,
        params={
            "denovo_chrom": "chrom",
            "denovo_pos": "position",
            "denovo_ref": "ref",
            "denovo_alt": "alt",
            "denovo_person_id": "personId",
        },
    )
    _, fvs = next(variants_loader.full_variants_iterator())
    assert fvs[0].genotype == [[0, 0], [0, 0],
                               [0, 0], [0, 0],
                               [0, 0], [0, 0],
                               [0, 1]]
