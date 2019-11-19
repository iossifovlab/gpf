from box import Box

from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage

from dae.tools.simple_study_import import main


def test_import_denovo_dae_style_into_impala(
        genomes_db, default_gene_models, fixture_dirname, default_dae_config):

    pedigree_filename = fixture_dirname('denovo_import/fake_pheno.ped')
    denovo_filename = fixture_dirname('denovo_import/variants_DAE_style.tsv')
    argv = [
        pedigree_filename,
        '--id', 'test_denovo_dae_style',
        '--skip-reports',
        '--denovo', denovo_filename,
        '--denovo-location', 'location',
        '--denovo-variant', 'variant',
        '--denovo-family-id', 'familyId',
        '--denovo-best-state', 'bestState',
    ]

    main(argv)

    default_storage_id = default_dae_config.genotype_storage.default
    default_storage_config = default_dae_config.storage[default_storage_id]
    assert default_storage_config.type == 'impala'

    impala_storage = ImpalaGenotypeStorage(default_storage_config)
    fvars = impala_storage.build_backend(
        Box({'id': 'test_denovo_dae_style'}),
        genomes_db
    )

    vs = list(fvars.query_variants())
    assert len(vs) == 3


def test_import_vcf_into_impala(
        genomes_db, default_gene_models, fixture_dirname, default_dae_config):

    pedigree_filename = fixture_dirname('vcf_import/effects_trio.ped')
    vcf_filename = fixture_dirname('vcf_import/effects_trio.vcf.gz')
    study_id = 'test_vcf'
    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--vcf', vcf_filename,
    ]

    main(argv)

    default_storage_id = default_dae_config.genotype_storage.default
    default_storage_config = default_dae_config.storage[default_storage_id]
    assert default_storage_config.type == 'impala'

    impala_storage = ImpalaGenotypeStorage(default_storage_config)
    fvars = impala_storage.build_backend(
        Box({'id': study_id}),
        genomes_db
    )

    vs = list(fvars.query_variants())
    assert len(vs) == 10
