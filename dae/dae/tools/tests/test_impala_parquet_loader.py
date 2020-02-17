from dae.tools.impala_parquet_loader import main


def test_impala_parquet_loader_partitioned(fixture_dirname, gpf_instance_2013):

    pedigree_path = fixture_dirname('backends/test_partition/pedigree.parquet')
    variants_path = fixture_dirname('backends/test_partition/variants.parquet')

    argv = [
        'test_study_impala_01',
        pedigree_path,
        variants_path,
        '--gs', 'genotype_impala',
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()

    genotype_data = gpf_instance_2013.get_genotype_data('test_study_impala_01')
    assert genotype_data is not None


def test_imapala_parquet_loader_no_partition(
        fixture_dirname, gpf_instance_2013):

    pedigree_path = fixture_dirname('studies/quads_f1_impala/data/pedigree')
    variants_path = fixture_dirname('studies/quads_f1_impala/data/pedigree')

    argv = [
        'test_study_impala_02',
        pedigree_path,
        variants_path,
        '--gs', 'genotype_impala',
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()

    genotype_data = gpf_instance_2013.get_genotype_data('test_study_impala_02')
    assert genotype_data is not None
