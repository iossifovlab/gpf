# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.testing import setup_pedigree, setup_vcf, setup_directories
from dae.testing.acgt_import import acgt_gpf
from dae.tools.vcf2parquet import main as vcf2parquet

@pytest.fixture(scope="module")
def import_vcf_data(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf2parquet_contigs_problem")
    gpf_instance = acgt_gpf(root_path)
    ped_path = setup_pedigree(
        root_path / "study_1" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "study_1" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        ##contig=<ID=chr3>
        ##contig=<ID=HLA-B*27:05:18>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        chr2   1   .  A   T    .    .      .    GT     0/1 0/0 0/1 0/0 0/0 0/1
        chr2   2   .  A   T    .    .      .    GT     0/0 0/0 0/0 0/0 0/0 0/1
        """)
    setup_directories(
        root_path / "study_1" / "partition_description.conf",
        textwrap.dedent("""
          [region_bin]
          chromosomes = chr1
          region_length = 10000000
        """)
    )
    return (
        gpf_instance, ped_path, vcf_path,
        root_path / "study_1" / "partition_description.conf")


def test_vcf2parquet_contigs_problem(import_vcf_data, tmp_path_factory):
    gpf_instance, ped_path, vcf_path, pd_path = import_vcf_data
    output = tmp_path_factory.mktemp("vcf2parquet_contigs_problem_output")

    import pdb; pdb.set_trace()

    argv = [
        str(ped_path),
        str(vcf_path),
        "-o", str(output),
        "--pd", str(pd_path),
        "--rb", "other_0",
    ]
    vcf2parquet(argv, gpf_instance=gpf_instance)
