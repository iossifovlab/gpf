# pylint: disable=W0621,C0114,C0116,W0212,W0613,R0917
import pathlib

import pytest
import pytest_mock
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.parquet_io import VariantsParquetWriter
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture
def vcf_variants(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[str, str]:
    root_path = tmp_path_factory.mktemp("test_vcf_loader")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1		    mom1		0	    0	    2	1	    mom
    f1		    dad1		0	    0	    1	1	    dad
    f1		    ch1		    dad1	mom1	1	2	    prb
    f1		    ch2		    dad1	mom1	2	1	    sib
    """)

    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=chr1>
    #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 ch2
    chr1   1   .  A   T   .    .      .    GT     1/1  1/1  1/0 1/1
    """)

    return (str(ped_path), str(vcf_path))


def test_vcf_denovo_reference(
    vcf_variants: tuple[str, str],
    acgt_genome_38: ReferenceGenome,
    tmp_path: pathlib.Path,
    t4c8_grr: GenomicResourceRepo,
) -> None:
    ped_path, vcf_path = vcf_variants
    families = FamiliesLoader(ped_path).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_denovo_mode": "denovo",
    }
    vcf_loader = VcfLoader(
        families,
        [vcf_path],
        acgt_genome_38,
        params=params,
    )

    assert vcf_loader is not None
    variants = list(vcf_loader.full_variants_iterator())
    assert len(variants) == 1
    annotation_pipeline = AnnotationPipeline(t4c8_grr)
    partition_descriptor = PartitionDescriptor(
        rare_boundary=5.0,
    )
    parquet_writer = VariantsParquetWriter(
        str(tmp_path / "out"),
        annotation_pipeline,
        partition_descriptor,
    )

    parquet_writer.write_dataset(variants)

    assert (tmp_path / "out").exists()
    assert (tmp_path / "out" / "family" / "frequency_bin=0").exists()


@pytest.mark.parametrize("batch_size", [0, 500])
def test_batch_annotation(
    batch_size: int,
    mocker: pytest_mock.MockerFixture,
    vcf_variants: tuple[str, str],
    acgt_genome_38: ReferenceGenome,
    tmp_path: pathlib.Path,
    t4c8_grr: GenomicResourceRepo,
) -> None:
    ped_path, vcf_path = vcf_variants
    families = FamiliesLoader(ped_path).load()
    vcf_loader = VcfLoader(families, [vcf_path], acgt_genome_38)
    annotation_pipeline = AnnotationPipeline(t4c8_grr)
    partition_descriptor = PartitionDescriptor()
    parquet_writer = VariantsParquetWriter(
        str(tmp_path / "out"),
        annotation_pipeline,
        partition_descriptor,
    )

    mocker.spy(AnnotationPipeline, "annotate")
    mocker.spy(AnnotationPipeline, "batch_annotate")

    parquet_writer.write_dataset(
        vcf_loader.full_variants_iterator(),
        annotation_batch_size=batch_size,
    )

    assert AnnotationPipeline.annotate.call_count == (  # type: ignore
        0 if batch_size else 1
    )
    assert AnnotationPipeline.batch_annotate.call_count == (  # type: ignore
        1 if batch_size else 0
    )
