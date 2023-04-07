# pylint: disable=W0621,C0114,C0116,W0212,W0613


import pytest

from dae.testing import acgt_gpf, setup_pedigree, setup_vcf, setup_denovo
from dae.testing.import_helpers import StudyInputLayout, setup_import_project


@pytest.fixture
def project_fixture(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("import_project_tests")
    gpf_instance = acgt_gpf(root_path)

    ped_path = setup_pedigree(
        root_path / "input_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "input_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1
        chr1   7   .  A   C   .    .      .    GT     0/1 0/0 0/1
        """)
    denovo_path = setup_denovo(
        root_path / "trios2_data" / "in.tsv",
        """
          familyId  location  variant    bestState
          f1        chr2:11    sub(A->G)  2||2||1/0||0||1
        """
    )
    project = setup_import_project(
        root_path / "project",
        StudyInputLayout(
            "mixed", ped_path, [vcf_path], [denovo_path], [], []),
        gpf_instance)

    return project


def test_import_project_chromosomes_simple(project_fixture):
    assert project_fixture.get_variant_loader_chromosomes() == ["chr1", "chr2"]


def test_import_project_variant_loader_types(project_fixture):
    assert project_fixture.get_variant_loader_types() == {"vcf", "denovo"}
