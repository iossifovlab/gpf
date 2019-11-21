from box import Box

from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage

from dae.tools.simple_study_import import main


def test_import_denovo_dae_style_into_impala(
        genomes_db, fixture_dirname,
        default_dae_config, default_gpf_instance):

    pedigree_filename = fixture_dirname('denovo_import/fake_pheno.ped')
    denovo_filename = fixture_dirname('denovo_import/variants_DAE_style.tsv')
    genotype_storage_id = 'test_impala'

    argv = [
        pedigree_filename,
        '--id', 'test_denovo_dae_style',
        # '--skip-reports',
        '--denovo', denovo_filename,
        '--denovo-location', 'location',
        '--denovo-variant', 'variant',
        '--denovo-family-id', 'familyId',
        '--denovo-best-state', 'bestState',
        '--genotype-storage', genotype_storage_id,
    ]

    main(argv, default_gpf_instance)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'impala'

    impala_storage = ImpalaGenotypeStorage(storage_config)
    fvars = impala_storage.build_backend(
        Box({'id': 'test_denovo_dae_style'}),
        genomes_db
    )

    vs = list(fvars.query_variants())
    assert len(vs) == 3


def test_import_vcf_into_impala(
        genomes_db, fixture_dirname, default_dae_config,
        default_gpf_instance):

    pedigree_filename = fixture_dirname('vcf_import/effects_trio.ped')
    vcf_filename = fixture_dirname('vcf_import/effects_trio.vcf.gz')
    study_id = 'test_vcf'
    genotype_storage_id = 'test_impala'

    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--vcf', vcf_filename,
        '--genotype-storage', genotype_storage_id,
    ]

    main(argv, default_gpf_instance)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'impala'

    impala_storage = ImpalaGenotypeStorage(storage_config)
    fvars = impala_storage.build_backend(
        Box({'id': study_id}),
        genomes_db
    )

    vs = list(fvars.query_variants())
    assert len(vs) == 10
