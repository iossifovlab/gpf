# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib
import textwrap

import pytest
from dae.genomic_resources.testing import setup_denovo, setup_pedigree
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing.alla_import import alla_gpf
from dae.variants_loaders.dae.loader import DenovoLoader


@pytest.fixture
def denovo_families(
    tmp_path: pathlib.Path,
) -> FamiliesData:
    root_path = tmp_path
    ped_path = setup_pedigree(
        root_path / "trio_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     1   1      sib
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        f3       p3       0      0      1   2      prb
        """)
    loader = FamiliesLoader(ped_path)
    return loader.load()


@pytest.fixture
def denovo_dae_style(
    tmp_path: pathlib.Path,
) -> pathlib.Path:
    root_path = tmp_path
    return setup_denovo(
        root_path / "in.tsv", textwrap.dedent("""
familyId location variant     bestState
f1       chr1:1      sub(A->T)   2||2||1||2/0||0||1||0
f1       chr2:1      sub(A->T)   2||2||1||2/0||0||1||0
f1       chrY:1      sub(A->T)   2||2||1||2/0||0||1||0
f2       chr2:5      sub(A->T)   2||2||1/0||0||1
f3       chr3:1      sub(A->T)   1/1
"""))


def test_read_variants_dae_style(
    denovo_dae_style: pathlib.Path,
    denovo_families: FamiliesData,
    tmp_path: pathlib.Path,
) -> None:

    gpf = alla_gpf(tmp_path)

    loader = DenovoLoader(
        denovo_families, str(denovo_dae_style),
        genome=gpf.reference_genome,
        params={
            "denovo_location": "location",
            "denovo_variant": "variant",
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
        })
    res_df = loader.flexible_denovo_load(
        str(denovo_dae_style),
        gpf.reference_genome,
        families=denovo_families,
        denovo_location="location",
        denovo_variant="variant",
        denovo_family_id="familyId",
        denovo_best_state="bestState",
    )

    assert len(res_df) == 4
