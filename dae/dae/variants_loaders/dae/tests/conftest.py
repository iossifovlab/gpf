# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pathlib
import textwrap

import pytest

from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.testing import setup_denovo, setup_pedigree


@pytest.fixture(scope="session")
def fake_families(fixture_dirname):
    ped_df = FamiliesLoader.flexible_pedigree_read(
        fixture_dirname("denovo_import/fake_pheno.ped"),
    )
    return FamiliesData.from_pedigree_df(ped_df)


@pytest.fixture(scope="session")
def denovo_families(tmp_path_factory: pytest.TempPathFactory) -> FamiliesData:
    root_path = tmp_path_factory.mktemp(
        "denovo_add_chrom_trio_families")
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


@pytest.fixture(scope="module")
def denovo_vcf_style(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("denovo_vcf_style")
    return setup_denovo(
        root_path / "in.tsv", textwrap.dedent("""
familyId chrom pos  ref alt bestState
f1       1     1    A   T   2||2||1||2/0||0||1||0
f1       2     1    A   T   2||2||1||2/0||0||1||0
f2       2     5    A   T   2||2||1/0||0||1
f3       3     1    A   T   1/1
"""))


@pytest.fixture(scope="module")
def denovo_vcf_style_chr(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("denovo_vcf_style_chr")
    return setup_denovo(
        root_path / "in.tsv", textwrap.dedent("""
familyId chrom pos  ref alt bestState
f1       chr1  1    A   T   2||2||1||2/0||0||1||0
f1       chr2  1    A   T   2||2||1||2/0||0||1||0
f2       chr2  5    A   T   2||2||1/0||0||1
f3       chr3  1    A   T   1/1
"""))


@pytest.fixture(scope="module")
def denovo_dae_style(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("denovo_vcf_style")
    return setup_denovo(
        root_path / "in.tsv", textwrap.dedent("""
familyId location variant     bestState
f1       1:1      sub(A->T)   2||2||1||2/0||0||1||0
f1       2:1      sub(A->T)   2||2||1||2/0||0||1||0
f2       2:5      sub(A->T)   2||2||1/0||0||1
f3       3:1      sub(A->T)   1/1
"""))


@pytest.fixture(scope="module")
def denovo_default_style(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("denovo_vcf_style")
    return setup_denovo(
        root_path / "in.tsv", textwrap.dedent("""
chrom  pos  ref  alt  person_id
1      1    A    T    p1
2      1    A    T    p1
2      5    A    T    p2
3      1    A    T    p3
"""))
