# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_directories,
    setup_pedigree,
    setup_vcf,
)
from dae.gpf_instance import GPFInstance
from dae.testing.import_helpers import vcf_study
from dae.testing.t4c8_import import t4c8_gpf


@pytest.fixture
def t4c8_instance(tmp_path: pathlib.Path) -> GPFInstance:
    root_path = tmp_path
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: t4c8_local
                type: directory
                directory: {root_path!s}
            """),
            "one": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_one
                          type: float
                          name: score
                """),
            },
            "two": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_two
                          type: float
                          name: score
                """),
            },
        },
    )
    one_content = textwrap.dedent("""
        chrom  pos_begin  score
        chr1   4          0.01
        chr1   54         0.02
        chr1   90         0.03
        chr1   100        0.04
        chr1   119        0.05
        chr1   122        0.06
    """)
    two_content = textwrap.dedent("""
        chrom  pos_begin  score
        chr1   4          0.11
        chr1   54         0.12
        chr1   90         0.13
        chr1   100        0.14
        chr1   119        0.15
        chr1   122        0.16
    """)
    setup_denovo(root_path / "one" / "data.txt", one_content)
    setup_denovo(root_path / "two" / "data.txt", two_content)
    return t4c8_gpf(root_path)


def t4c8_study(instance: GPFInstance) -> str:
    pedigree = textwrap.dedent("""
        familyId personId dadId momId sex status role
        f1.1     mom1     0     0     2   1      mom
        f1.1     dad1     0     0     1   1      dad
        f1.1     ch1      dad1  mom1  2   2      prb
        f1.3     mom3     0     0     2   1      mom
        f1.3     dad3     0     0     1   1      dad
        f1.3     ch3      dad3  mom3  2   2      prb
    """)
    variants = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        ##contig=<ID=chr3>
        #CHROM POS  ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
        chr1   4    .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/1  0/2  0/2
        chr1   54   .  T   C    .    .      .    GT     0/1  0/0  0/1 0/0  0/0  0/0
        chr1   90   .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/1  0/2  0/1
        chr1   100  .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/2  0/2  0/0
        chr1   119  .  A   G,C  .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
        chr1   122  .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/2  0/2  0/2
    """)  # noqa: E501

    project_config = {
        "destination": {"storage_type": "schema2"},
        "annotation": [
            {"position_score": {"resource_id": "one"}},
        ],
    }

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "frequency_bin": {
                "rare_boundary": 25.0,
            },
            "coding_bin": {
                "coding_effect_types": [
                    "frame-shift",
                    "noStart",
                    "missense",
                    "synonymous",
                ],
            },
            "family_bin": {
                "family_bin_size": 2,
            },
        },
    }

    root_path = pathlib.Path(instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study" / "pedigree" / "in.ped",
        pedigree,
    )
    vcf_path = setup_vcf(
        root_path / "study" / "vcf" / "in.vcf.gz",
        variants,
    )
    vcf_study(
        root_path, "study",
        ped_path, [vcf_path],
        gpf_instance=instance,
        project_config_overwrite=project_config_update,
        project_config_update=project_config,
    )
    instance.reload()
    return f"{root_path}/work_dir/study"
