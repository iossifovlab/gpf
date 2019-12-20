from box import Box

from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage
from dae.backends.storage.filesystem_genotype_storage import \
    FilesystemGenotypeStorage
from dae.tools.simple_study_import import main


def test_import_denovo_dae_style_into_impala(
        genomes_db_2013, fixture_dirname,
        default_dae_config, gpf_instance_2013, temp_dirname):

    pedigree_filename = fixture_dirname('denovo_import/fake_pheno.ped')
    denovo_filename = fixture_dirname('denovo_import/variants_DAE_style.tsv')
    genotype_storage_id = 'test_impala'
    study_id = 'test_denovo_dae_style'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'impala'
    impala_storage = ImpalaGenotypeStorage(storage_config)

    impala_storage.impala_drop_study_tables(
        Box({"id": study_id}, default_box=True)
    )

    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--denovo', denovo_filename,
        '--denovo-location', 'location',
        '--denovo-variant', 'variant',
        '--denovo-family-id', 'familyId',
        '--denovo-best-state', 'bestState',
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'impala'

    impala_storage = ImpalaGenotypeStorage(storage_config)
    fvars = impala_storage.build_backend(
        Box({'id': study_id}, default_box=True),
        genomes_db_2013
    )

    vs = list(fvars.query_variants())
    assert len(vs) == 3


def test_import_comp_vcf_into_impala(
        genomes_db_2013, fixture_dirname, default_dae_config,
        gpf_instance_2013, temp_dirname):

    pedigree_filename = fixture_dirname('study_import/comp.ped')
    vcf_filename = fixture_dirname('study_import/comp.vcf')
    study_id = 'test_comp_vcf'
    genotype_storage_id = 'test_impala'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'impala'
    impala_storage = ImpalaGenotypeStorage(storage_config)

    impala_storage.impala_drop_study_tables(
        Box({"id": study_id}, default_box=True)
    )
    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--vcf', vcf_filename,
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    fvars = impala_storage.build_backend(
        Box({'id': study_id}, default_box=True),
        genomes_db_2013
    )

    vs = list(fvars.query_variants())
    assert len(vs) == 30


def test_import_comp_denovo_into_impala(
        genomes_db_2013, fixture_dirname, default_dae_config,
        gpf_instance_2013, temp_dirname):

    pedigree_filename = fixture_dirname('study_import/comp.ped')
    denovo_filename = fixture_dirname('study_import/comp.tsv')

    study_id = 'test_comp_denovo'
    genotype_storage_id = 'test_impala'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'impala'
    impala_storage = ImpalaGenotypeStorage(storage_config)

    impala_storage.impala_drop_study_tables(
        Box({"id": study_id}, default_box=True)
    )

    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--denovo', denovo_filename,
        '--denovo-location', 'location',
        '--denovo-variant', 'variant',
        '--denovo-family-id', 'familyId',
        '--denovo-best-state', 'bestState',
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    fvars = impala_storage.build_backend(
        Box({'id': study_id}, default_box=True),
        genomes_db_2013
    )

    vs = list(fvars.query_variants())
    assert len(vs) == 5


def test_import_comp_all_into_impala(
        genomes_db_2013, fixture_dirname, default_dae_config,
        gpf_instance_2013, temp_dirname):

    pedigree_filename = fixture_dirname('study_import/comp.ped')
    vcf_filename = fixture_dirname('study_import/comp.vcf')
    denovo_filename = fixture_dirname('study_import/comp.tsv')

    study_id = 'test_comp_all'
    genotype_storage_id = 'test_impala'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'impala'
    impala_storage = ImpalaGenotypeStorage(storage_config)

    impala_storage.impala_drop_study_tables(
        Box({"id": study_id}, default_box=True)
    )

    argv = [
        pedigree_filename,
        '--id', study_id,
        # '--skip-reports',
        '--vcf', vcf_filename,
        '--denovo', denovo_filename,
        '--denovo-location', 'location',
        '--denovo-variant', 'variant',
        '--denovo-family-id', 'familyId',
        '--denovo-best-state', 'bestState',
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    fvars = impala_storage.build_backend(
        Box({'id': study_id}, default_box=True),
        genomes_db_2013
    )

    vs = list(fvars.query_variants())
    assert len(vs) == 35


def test_import_denovo_dae_style_into_filesystem(
        genomes_db_2013, fixture_dirname,
        default_dae_config, gpf_instance_2013, temp_dirname):

    pedigree_filename = fixture_dirname('denovo_import/fake_pheno.ped')
    denovo_filename = fixture_dirname('denovo_import/variants_DAE_style.tsv')

    # pedigree_filename = fixture_dirname(
    #     'dae_iossifov2014/iossifov2014_families.ped')
    # denovo_filename = fixture_dirname(
    #     'dae_iossifov2014/iossifov2014.txt')

    genotype_storage_id = 'test_filesystem'
    study_id = 'test_denovo_dae_style'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'
    genotype_storage = FilesystemGenotypeStorage(storage_config)
    assert genotype_storage

    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--denovo', denovo_filename,
        '--denovo-location', 'location',
        '--denovo-variant', 'variant',
        '--denovo-family-id', 'familyId',
        '--denovo-best-state', 'bestState',
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'

    gpf_instance_2013.reload()
    study = gpf_instance_2013._variants_db.get_study(study_id)
    vs = list(study.query_variants())
    assert len(vs) == 3


def test_import_iossifov2014_filesystem(
        genomes_db_2013, fixture_dirname, dae_iossifov2014_config,
        default_dae_config, gpf_instance_2013, temp_dirname):

    pedigree_filename = dae_iossifov2014_config.family_filename
    denovo_filename = dae_iossifov2014_config.denovo_filename

    # pedigree_filename = fixture_dirname(
    #     'dae_iossifov2014/iossifov2014_families.ped')
    # denovo_filename = fixture_dirname(
    #     'dae_iossifov2014/iossifov2014.txt')

    genotype_storage_id = 'test_filesystem'
    study_id = 'test_denovo_iossifov2014_fs'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'
    genotype_storage = FilesystemGenotypeStorage(storage_config)
    assert genotype_storage

    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--denovo', denovo_filename,
        '--denovo-location', 'location',
        '--denovo-variant', 'variant',
        '--denovo-family-id', 'familyId',
        '--denovo-best-state', 'bestState',
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'

    gpf_instance_2013.reload()
    study = gpf_instance_2013._variants_db.get_study(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 16

    vs = list(study.query_variants(effect_types=['splice-site']))
    assert len(vs) == 9

    vs = list(study.query_variants(effect_types=['no-frame-shift']))
    assert len(vs) == 2


def test_import_comp_all_into_filesystem(
        genomes_db_2013, fixture_dirname, default_dae_config,
        gpf_instance_2013, temp_dirname):

    pedigree_filename = fixture_dirname('study_import/comp.ped')
    vcf_filename = fixture_dirname('study_import/comp.vcf')
    denovo_filename = fixture_dirname('study_import/comp.tsv')

    study_id = 'test_comp_all_fs'
    genotype_storage_id = 'test_filesystem'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'

    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--vcf', vcf_filename,
        '--denovo', denovo_filename,
        '--denovo-location', 'location',
        '--denovo-variant', 'variant',
        '--denovo-family-id', 'familyId',
        '--denovo-best-state', 'bestState',
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, gpf_instance_2013)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'

    gpf_instance_2013.reload()
    study = gpf_instance_2013._variants_db.get_study(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 35
