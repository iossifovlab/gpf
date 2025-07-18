# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import numpy as np
import pysam
import pytest
from dae.annotation.annotate_vcf import VCFWriter, process_vcf
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_pedigree,
    setup_vcf,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.loader import FamiliesLoader
from dae.testing.acgt_import import acgt_gpf
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariantFactory
from dae.variants_loaders.raw.loader import FullVariant
from dae.variants_loaders.vcf.serializer import VcfSerializer


@pytest.fixture
def test_gpf_instance(tmp_path: pathlib.Path) -> GPFInstance:
    score_dir = tmp_path / "acgt_gpf" / "sample_score"
    setup_denovo(
        score_dir / "data.txt",
        textwrap.dedent("""
            chrom  pos_begin  score
            chr1   10         0.1
            chr2   20         0.2
            chr3   30         0.3
        """))
    (score_dir / "genomic_resource.yaml").write_text(textwrap.dedent(
        """
        type: position_score
        table:
            filename: data.txt
        scores:
            - id: score
              type: float
              name: score
        """))
    return acgt_gpf(tmp_path)


@pytest.fixture
def sample_ped(tmp_path: pathlib.Path) -> pathlib.Path:
    filepath = tmp_path / "sample.ped"
    setup_pedigree(filepath, textwrap.dedent("""
        familyId personId dadId momId sex status role
        f1       mom      0     0     2   1      mom
        f1       dad      0     0     1   1      dad
        f1       prb      dad   mom   1   2      prb
    """))
    return filepath


@pytest.fixture
def sample_vcf(tmp_path: pathlib.Path) -> pathlib.Path:
    filepath = tmp_path / "sample.vcf"
    setup_vcf(filepath, textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        ##contig=<ID=chr3>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom dad prb
        chr1   10  .  C   T   .    .      .    GT     0/0 0/0 0/1
        chr2   20  .  C   T   .    .      .    GT     0/1 0/0 0/1
        chr3   30  .  C   T   .    .      .    GT     0/1 0/1 0/1
    """))
    return filepath


def test_vcf_writer(
    tmp_path: pathlib.Path,
    test_gpf_instance: GPFInstance,
    sample_ped: pathlib.Path,
):
    out_path = tmp_path / "out.vcf"

    families = FamiliesLoader(str(sample_ped)).load()
    summary_variant = SummaryVariantFactory.summary_variant_from_records(
        [{"chrom": "chr1",
          "position": 10,
          "reference": "C",
          "alternative": "T",
          "summary_index": -1,
          "allele_index": 1}],
    )
    family_variant = FamilyVariant(
        summary_variant, families["f1"],
        np.array([[0, 0, 0], [0, 0, 1]]),
        np.array([[2, 2, 1], [0, 0, 1]]),
    )

    serializer = VcfSerializer(
        families,
        test_gpf_instance.reference_genome,
        out_path,
    )
    with VCFWriter(serializer) as writer:
        writer.filter(FullVariant(summary_variant, [family_variant]))

    assert out_path.read_text() == (
       '##fileformat=VCFv4.2\n'
       '##FILTER=<ID=PASS,Description="All filters passed">\n'
       '##contig=<ID=chr1>\n'
       '##contig=<ID=chr2>\n'
       '##contig=<ID=chr3>\n'
       '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'
       '##INFO=<ID=END,Number=1,Type=Integer,Description="Stop position of the interval">\n'  # noqa: E501
       '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tmom\tdad\tprb\n'
       'chr1\t10\tchr1_10_C_T\tC\tT\t.\t.\t.\tGT\t0/0\t0/0\t0/1\n'
    )


def test_process_vcf_simple(
    tmp_path: pathlib.Path,
    test_gpf_instance: GPFInstance,
    sample_ped: pathlib.Path,
    sample_vcf: pathlib.Path,
):
    out_path = tmp_path / "out.vcf"
    work_dir = tmp_path / "work_dir"
    pipeline_config = [
        {"position_score": "sample_score"},
    ]

    process_vcf(
        sample_vcf,
        sample_ped,
        out_path,
        pipeline_config,
        None,
        test_gpf_instance.grr.definition,  # type: ignore
        test_gpf_instance.reference_genome.resource_id,
        work_dir,
        0,
        None,
        False,  # noqa: FBT003
        False,  # noqa: FBT003
    )

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_path)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2", "0.3"]


def test_process_vcf_simple_batch(
    tmp_path: pathlib.Path,
    test_gpf_instance: GPFInstance,
    sample_ped: pathlib.Path,
    sample_vcf: pathlib.Path,
):
    out_path = tmp_path / "out.vcf"
    work_dir = tmp_path / "work_dir"
    pipeline_config = [
        {"position_score": "sample_score"},
    ]

    process_vcf(
        sample_vcf,
        sample_ped,
        out_path,
        pipeline_config,
        None,
        test_gpf_instance.grr.definition,  # type: ignore
        test_gpf_instance.reference_genome.resource_id,
        work_dir,
        1,
        None,
        False,  # noqa: FBT003
        False,  # noqa: FBT003
    )

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_path)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2", "0.3"]
