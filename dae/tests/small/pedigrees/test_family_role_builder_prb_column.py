# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pandas as pd
import pytest
from dae.genomic_resources.testing import setup_pedigree
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import Role


@pytest.fixture
def pedigree_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return setup_pedigree(tmp_path / "pedigree.tsv", textwrap.dedent(
        """
        familyId personId dadId	 momId  sex    status prb
        f1       f1.dad   0      0      male   1      False
        f1       f1.mom   0      0      female 2      False
        f1       f1.sib   f1.dad f1.mom female 2      False
        f1       f1.prb   f1.dad f1.mom male   2      True
        """))


def test_load_pedigree_with_prb_column(pedigree_path: pathlib.Path) -> None:
    families = FamiliesLoader(
        str(pedigree_path),
        ped_proband="prb",
    ).load()
    assert families is not None
    assert len(families) == 1

    family = families["f1"]
    prb = family.get_member("f1.prb")
    assert prb is not None
    assert prb.role == Role.prb


def test_ped2ped_ped_proband(pedigree_path: pathlib.Path) -> None:
    # pylint: disable=import-outside-toplevel
    from dae.tools.ped2ped import main

    output_path = pedigree_path.parent / "output.tsv"
    main([
        str(pedigree_path),
        "--ped-proband", "prb",
        "--ped-layout-mode", "generate",
        "--output", str(output_path),
    ])
    assert output_path.exists()

    df = pd.read_csv(output_path, sep="\t")
    assert df["role"].tolist() == ["dad", "mom", "sib", "prb"]


@pytest.fixture
def pedigree_path2(tmp_path: pathlib.Path) -> pathlib.Path:
    return setup_pedigree(tmp_path / "pedigree2.tsv", textwrap.dedent(
        """
spid   sfid   father mother sex	age_m	asd	role    prb
P0001  F0002  0      0      1   528.0   1   father  False
P0002  F0002  P0001	 P0003  1   154.0   2   child   True
P0003  F0002  0      0      2   523.0   1   mother  False
        """))


def test_load_pedigree_with_prb_column_and_bad_role(
    pedigree_path2: pathlib.Path,
) -> None:
    families = FamiliesLoader(
        str(pedigree_path2),
        ped_person="spid",
        ped_family="sfid",
        ped_dad="father",
        ped_mom="mother",
        ped_status="asd",
        ped_no_role=True,
        ped_proband="prb",
    ).load()
    assert families is not None
    assert len(families) == 1

    family = families["F0002"]
    prb = family.get_member("P0002")
    assert prb is not None
    assert prb.role == Role.prb


def test_ped2ped_ped_proband_and_bad_role(
    pedigree_path2: pathlib.Path,
) -> None:
    # pylint: disable=import-outside-toplevel
    from dae.tools.ped2ped import main

    output_path = pedigree_path2.parent / "output.tsv"
    main([
        str(pedigree_path2),
        "--ped-person", "spid",
        "--ped-family", "sfid",
        "--ped-dad", "father",
        "--ped-mom", "mother",
        "--ped-status", "asd",
        "--ped-proband", "prb",
        "--ped-no-role",
        "--ped-layout-mode", "generate",
        "--output", str(output_path),
    ])
    assert output_path.exists()

    df = pd.read_csv(output_path, sep="\t")
    assert df["role"].tolist() == ["dad", "prb", "mom"]
