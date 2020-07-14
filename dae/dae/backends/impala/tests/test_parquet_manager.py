import pytest
import os

from dae.backends.impala.parquet_io import ParquetManager


@pytest.mark.parametrize(
    "prefix,study_id,bucket_index,suffix,pedigree,variant",
    [
        (
            "/tmp",
            None,
            0,
            None,
            "/tmp/pedigree/tmp_pedigree.parquet",
            "/tmp/variants/tmp_variants.parquet",
        ),
        (
            "/tmp",
            "study_id",
            0,
            None,
            "/tmp/pedigree/study_id_pedigree.parquet",
            "/tmp/variants/study_id_variants.parquet",
        ),
        (
            "/tmp",
            "study_id",
            1,
            None,
            "/tmp/pedigree/study_id_000001_pedigree.parquet",
            "/tmp/variants/study_id_000001_variants.parquet",
        ),
        (
            "/tmp",
            "study_id",
            0,
            "suffix",
            "/tmp/pedigree/study_idsuffix_pedigree.parquet",
            "/tmp/variants/study_idsuffix_variants.parquet",
        ),
        (
            "/tmp",
            "study_id",
            1111111,
            "suffix",
            "/tmp/pedigree/study_id_1111111suffix_pedigree.parquet",
            "/tmp/variants/study_id_1111111suffix_variants.parquet",
        ),
    ],
)
def test_parquet_file_config(
    prefix, study_id, bucket_index, suffix, pedigree, variant
):
    parquet_file_config = ParquetManager.build_parquet_filenames(
        prefix, study_id, bucket_index, suffix
    )

    assert parquet_file_config.pedigree == pedigree
    assert parquet_file_config.variants == variant


def test_families_to_parquet(variants_vcf, temp_dirname):
    fvars = variants_vcf("backends/effects_trio")

    data_dir = temp_dirname
    pedigree_path = os.path.join(data_dir, "quads_f1_impala_pedigree.parquet")
    assert not os.path.exists(pedigree_path)

    ParquetManager.families_to_parquet(fvars.families, pedigree_path)
    assert os.path.exists(pedigree_path)


def test_variant_to_parquet(
    vcf_variants_loader, annotation_pipeline_default_decorator, temp_dirname
):

    fvars = annotation_pipeline_default_decorator(
        vcf_variants_loader("backends/effects_trio")
    )

    data_dir = temp_dirname
    variant_path = os.path.join(data_dir, "quads_f1_impala_variant.parquet")

    assert not os.path.exists(variant_path)

    ParquetManager.variants_to_parquet_filename(fvars, variant_path)

    assert os.path.exists(variant_path)
