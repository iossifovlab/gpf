import pytest

import os
import shutil
from box import Box

from dae.backends.impala.tests.conftest import relative_to_this_test_folder


def test_get_data_dir(parquet_manager):
    assert parquet_manager.get_data_dir('study_id') == \
        relative_to_this_test_folder('fixtures/studies/study_id/data')


@pytest.mark.parametrize(
    'prefix,study_id,bucket_index,suffix,pedigree,variant', [
        (
            '/tmp', None, 0, None, '/tmp/pedigree/tmp_pedigree.parquet',
            '/tmp/variant/tmp_variant.parquet'
        ),
        (
            '/tmp', 'study_id', 0, None,
            '/tmp/pedigree/study_id_pedigree.parquet',
            '/tmp/variant/study_id_variant.parquet'
        ),
        (
            '/tmp', 'study_id', 1, None,
            '/tmp/pedigree/study_id_pedigree_000001.parquet',
            '/tmp/variant/study_id_variant_000001.parquet'
        ),
        (
            '/tmp', 'study_id', 0, 'suffix',
            '/tmp/pedigree/study_id_pedigreesuffix.parquet',
            '/tmp/variant/study_id_variantsuffix.parquet'
        ),
        (
            '/tmp', 'study_id', 1111111, 'suffix',
            '/tmp/pedigree/study_id_pedigree_1111111suffix.parquet',
            '/tmp/variant/study_id_variant_1111111suffix.parquet'
        )
    ]
)
def test_parquet_file_config(
        parquet_manager, prefix, study_id, bucket_index, suffix, pedigree,
        variant):
    parquet_file_config = parquet_manager.build_parquet_filenames(
        prefix, study_id, bucket_index, suffix
    )

    assert parquet_file_config.pedigree == pedigree
    assert parquet_file_config.variant == variant


def test_generate_study_config_exist(capsys, parquet_manager):
    parquet_manager.generate_study_config(
        'quads_f1_vcf', 'genotype_impala'
    )
    config_path = relative_to_this_test_folder(
        'fixtures/studies/quads_f1_vcf/quads_f1_vcf.conf'
    )

    captured = capsys.readouterr()
    assert captured.out == \
        f'configuration file already exists: {config_path}\n' \
        'skipping generation of default config for: quads_f1_vcf\n'


def test_generate_study_config(parquet_manager):
    config_dir = relative_to_this_test_folder(
        'fixtures/studies/quads_f1_impala'
    )
    config_path = relative_to_this_test_folder(
        'fixtures/studies/quads_f1_impala/quads_f1_impala.conf'
    )
    shutil.rmtree(config_dir, ignore_errors=True)

    parquet_manager.generate_study_config(
        'quads_f1_impala', 'genotype_impala'
    )

    assert os.path.exists(config_path)

    with open(config_path, 'r') as config:
        assert config.read() == \
            '''
[study]

id = quads_f1_impala
genotype_storage = genotype_impala

'''


def test_pedigree_to_parquet(parquet_manager, variants_vcf, temp_dirname):
    fvars = variants_vcf('backends/effects_trio')

    data_dir = temp_dirname
    pedigree_path = os.path.join(
        data_dir,
        'quads_f1_impala_pedigree.parquet'
    )
    assert not os.path.exists(pedigree_path)

    parquet_manager.pedigree_to_parquet(fvars, pedigree_path)
    assert os.path.exists(pedigree_path)


def test_variant_to_parquet(parquet_manager, variants_vcf, temp_dirname):
    fvars = variants_vcf('backends/effects_trio')

    data_dir = temp_dirname
    variant_path = os.path.join(
        data_dir,
        'quads_f1_impala_variant.parquet'
    )

    assert not os.path.exists(variant_path)

    parquet_manager.variants_to_parquet(fvars, variant_path)

    assert os.path.exists(variant_path)
