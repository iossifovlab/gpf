# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
from dae.annotation.reannotate_instance import cli
from dae.gpf_instance import GPFInstance
from dae.testing import (
    setup_denovo,
    setup_directories,
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
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


@pytest.fixture(autouse=True)
def t4c8_study(t4c8_instance: GPFInstance):
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

    root_path = pathlib.Path(t4c8_instance.dae_dir)
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
        t4c8_instance,
        project_config_update=project_config,
    )
    t4c8_instance.reload()


def test_reannotate_instance_tool(
    t4c8_instance: GPFInstance,
) -> None:
    """
    Basic reannotate instance tool case.
    """
    # Expect default annotation in study variants
    study = t4c8_instance.get_genotype_data("study")
    vs = list(study.query_variants())
    assert all(v.has_attribute("score_one") for v in vs)
    assert not any(v.has_attribute("score_two") for v in vs)

    # Add default annotation config with different score resource
    pathlib.Path(t4c8_instance.dae_dir, "annotation.yaml").write_text(
        textwrap.dedent(
        """- position_score:
                resource_id: two
        """),
    )

    with open(f"{t4c8_instance.dae_dir}/gpf_instance.yaml", "a") as f:
        f.write(
            textwrap.dedent(
                """\
                annotation:
                    conf_file: annotation.yaml
                """,
            ),
        )

    new_instance = GPFInstance.build(
        f"{t4c8_instance.dae_dir}/gpf_instance.yaml",
        grr=t4c8_instance.grr,
    )

    # Run the reannotate instance tool
    cli(
        ["-j", "1",  # Single job to avoid using multiprocessing
        "--force"],
        new_instance,
    )
    new_instance.reload()

    # Annotations should be updated
    study = new_instance.get_genotype_data("study")
    vs = list(study.query_variants())

    assert all(v.has_attribute("score_two") for v in vs)
    assert not any(v.has_attribute("score_one") for v in vs)
