import os
import io

from contextlib import redirect_stdout

from box import Box

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader

from dae.annotation.tools.file_io_parquet import ParquetReader

from dae.backends.impala.loader import ParquetLoader

from dae.tools.vcf2parquet import main


def test_vcf2parquet_vcf(
        vcf_import_config, annotation_pipeline_config,
        annotation_scores_dirname, temp_dirname,
        gpf_instance_2013, default_dae_config, genomes_db_2013):

    argv = [
        'vcf',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        vcf_import_config.pedigree,
        vcf_import_config.vcf
    ]

    main(
        argv, gpf_instance=gpf_instance_2013,
        dae_config=default_dae_config,
        genomes_db=genomes_db_2013,
        annotation_defaults={'values': {
             "scores_dirname": annotation_scores_dirname,
        }}
    )

    summary = ParquetReader(Box({
        'infile': os.path.join(temp_dirname, 'variant', 'variants.parquet'),
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    # print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    assert schema['effect_gene'].type_name == 'str'
    assert schema['effect_type'].type_name == 'str'
    assert schema['effect_data'].type_name == 'str'
    # assert schema['worst_effect'].type_name == 'str'


def test_vcf2parquet_vcf_partition(
        vcf_import_config, annotation_pipeline_config,
        annotation_scores_dirname, temp_dirname,
        gpf_instance_2013, default_dae_config, genomes_db_2013,
        parquet_partition_configuration):

    argv = [
        'vcf',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        '--pd', parquet_partition_configuration,
        vcf_import_config.pedigree,
        vcf_import_config.vcf
    ]

    main(
        argv, gpf_instance=gpf_instance_2013,
        dae_config=default_dae_config,
        genomes_db=genomes_db_2013,
        annotation_defaults={'values': {
             "scores_dirname": annotation_scores_dirname,
        }}
    )

    generated_conf = os.path.join(temp_dirname, '_PARTITION_DESCRIPTION')
    assert os.path.exists(generated_conf)

    ped_df = FamiliesLoader.flexible_pedigree_read(vcf_import_config.pedigree)
    families = FamiliesData.from_pedigree_df(ped_df)

    pl = ParquetLoader(families, generated_conf)
    summary_genotypes = []
    for summary, gt in pl.summary_genotypes_iterator():
        summary_genotypes.append((summary, gt))

    assert len(summary_genotypes) == 110
    assert all(sgt[0].get_attribute('region_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('family_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('coding_bin')[0] is not None
               for sgt in summary_genotypes)
    assert all(sgt[0].get_attribute('frequency_bin')[0] is not None
               for sgt in summary_genotypes)
    assert any(sgt[0].reference == 'G' for sgt in summary_genotypes)
    assert any(sgt[0].reference == 'C' for sgt in summary_genotypes)
    assert any(sgt[0].alternative == 'T' for sgt in summary_genotypes)
    assert any(sgt[0].alternative == 'A' for sgt in summary_genotypes)
    assert any(sgt[0].reference == 'CGGCTCGGAAGG' for sgt in summary_genotypes)


def test_vcf2parquet_make(
        vcf_import_config, annotation_pipeline_default_config,
        annotation_scores_dirname, temp_dirname,
        gpf_instance_2013, default_dae_config, genome_2013):

    argv = [
        'make',
        '--annotation', annotation_pipeline_default_config,
        '-o', temp_dirname,
        vcf_import_config.pedigree,
        vcf_import_config.vcf
    ]

    f = io.StringIO()
    with redirect_stdout(f):
        main(argv)

    makefile = f.getvalue()
    assert 'all:' in makefile
    assert 'vcf2parquet.py vcf ' in makefile


def test_vcf2parquet_make_partition(
        vcf_import_config, annotation_pipeline_default_config,
        annotation_scores_dirname, temp_dirname,
        gpf_instance_2013, default_dae_config, genome_2013,
        parquet_partition_configuration):

    argv = [
        'make',
        '--annotation', annotation_pipeline_default_config,
        '-o', temp_dirname,
        '--pd', parquet_partition_configuration,
        vcf_import_config.pedigree,
        vcf_import_config.vcf
    ]

    f = io.StringIO()
    with redirect_stdout(f):
        main(argv)

    makefile = f.getvalue()
    print(makefile)
    assert 'all:' in makefile
    assert 'vcf2parquet.py vcf ' in makefile
    assert '1_8:' in makefile
    assert '--region 1:80000001-90000000' in makefile
    assert '1_9:' in makefile
    assert '--region 1:90000001-100000000' in makefile
    assert '1_12:' in makefile
    assert '--region 1:120000001-130000000' in makefile
