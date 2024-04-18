# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.enrichment_tool.build_ur_synonymous_enrichment_background import cli
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.t4c8_import import t4c8_gpf


@pytest.fixture()
def t4c8_instance(
    tmp_path: pathlib.Path,
) -> GPFInstance:
    root_path = tmp_path
    gpf_instance = t4c8_gpf(root_path)
    return gpf_instance


@pytest.fixture()
def t4c8_study_1(t4c8_instance: GPFInstance) -> GenotypeData:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_1" / "pedigree" / "in.ped",
        """
familyId personId dadId momId sex status role
f1.1     mom1     0     0     2   1      mom
f1.1     dad1     0     0     1   1      dad
f1.1     ch1      dad1  mom1  2   2      prb
f1.3     mom3     0     0     2   1      mom
f1.3     dad3     0     0     1   1      dad
f1.3     ch3      dad3  mom3  2   2      prb
        """)
    vcf_path1 = setup_vcf(
        root_path / "study_1" / "vcf" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS  ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
chr1   54   .  T   C   .    .      .    GT     0/1  0/0  0/1 0/0  0/0  0/0
chr1   119  .  A   G   .    .      .    GT     0/0  0/0  0/0 0/1  0/0  0/1
chr1   122  .  A   C   .    .      .    GT     0/0  1/0  0/0 0/0  0/0  0/0
        """)

    study = vcf_study(
        root_path,
        "study_1", ped_path, [vcf_path1],
        t4c8_instance,
    )
    return study


def test_build_ur_synonymous_background(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    t4c8_study_1: GenotypeData,
) -> None:

    output = tmp_path / "ur_synonymous_background.tsv"

    cli(
        [
            "study_1",
            "-o", str(output),
            "--parents-called", "2",
        ],
        t4c8_instance,
    )

    assert output.exists()
    assert output.is_file()

    with open(output) as f:
        lines = f.readlines()
        assert len(lines) == 3
        assert lines[0].startswith("gene\tgene_weight")
        assert lines[1].startswith("T4\t1")
        assert lines[2].startswith("C8\t2")
