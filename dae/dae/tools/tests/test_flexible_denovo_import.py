from box import Box

from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage
from dae.backends.storage.filesystem_genotype_storage import \
    FilesystemGenotypeStorage
from dae.tools.simple_study_import import main


def test_import_iossifov2014_filesystem(
        genomes_db, fixture_dirname, dae_iossifov2014_config,
        default_dae_config, default_gpf_instance, temp_dirname):

    pedigree_filename = dae_iossifov2014_config.family_filename
    denovo_filename = dae_iossifov2014_config.denovo_filename

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

    main(argv, default_gpf_instance)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'

    default_gpf_instance.reload()
    study = default_gpf_instance._variants_db.get_study(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 16

    vs = list(study.query_variants(effect_types=['splice-site']))
    assert len(vs) == 9

    vs = list(study.query_variants(effect_types=['no-frame-shift']))
    assert len(vs) == 2


def assert_proper_flexible_short_variants(vs):
    assert len(vs) == 3
    v = vs[0]
    for a in v.alt_alleles:
        print(a, a.effect)
        print("\t>", a.effect.transcripts)
        assert a.chrom == '15'
        assert a.position == 80137553
        assert a.reference == 'T'
        assert a.alternative == 'TA'
        assert a.family_id == '13590'
        assert len(a.effect.transcripts) == 4

    v = vs[1]
    for a in v.alt_alleles:
        print(a, a.effect)
        print("\t>", a.effect.transcripts)

        assert a.chrom == '3'
        assert a.position == 56627767
        assert a.reference == 'AAAGT'
        assert a.alternative == 'A'
        assert a.family_id == '13060'
        assert len(a.effect.transcripts) == 28

    v = vs[2]
    for a in v.alt_alleles:
        print(a, a.effect)
        print("\t>", a.effect.transcripts)
        assert a.chrom == '4'
        assert a.position == 83276456
        assert a.reference == 'C'
        assert a.alternative == 'T'
        assert a.family_id == '13590'
        assert len(a.effect.transcripts) == 4


def test_flexible_denovo_default(
        genomes_db, fixture_dirname, default_dae_config, default_gpf_instance,
        temp_dirname):


    pedigree_filename = fixture_dirname(
        'flexible_short/flexible_short_families.ped')
    denovo_filename = fixture_dirname('flexible_short/flexible_short.txt')

    genotype_storage_id = 'test_filesystem'
    study_id = 'test_flexible_denovo_default'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'
    genotype_storage = FilesystemGenotypeStorage(storage_config)
    assert genotype_storage

    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--denovo', denovo_filename,
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, default_gpf_instance)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'

    default_gpf_instance.reload()
    study = default_gpf_instance._variants_db.get_study(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)

def test_flexible_denovo_vcf(
        genomes_db, fixture_dirname, default_dae_config, default_gpf_instance,
        temp_dirname):


    pedigree_filename = fixture_dirname(
        'flexible_short/flexible_short_families.ped')
    denovo_filename = fixture_dirname('flexible_short/flexible_short_vcf.txt')

    genotype_storage_id = 'test_filesystem'
    study_id = 'test_flexible_denovo_vcf'

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'
    genotype_storage = FilesystemGenotypeStorage(storage_config)
    assert genotype_storage

    argv = [
        pedigree_filename,
        '--id', study_id,
        '--skip-reports',
        '--denovo', denovo_filename,
        '--denovo-person-id', 'person_id',
        '--denovo-chrom', 'chrom',
        '--denovo-pos', 'position',
        '--denovo-ref', 'reference',
        '--denovo-alt', 'alternative',
        '--genotype-storage', genotype_storage_id,
        '-o', temp_dirname,
    ]

    main(argv, default_gpf_instance)

    storage_config = default_dae_config.storage[genotype_storage_id]
    assert storage_config.type == 'filesystem'

    default_gpf_instance.reload()
    study = default_gpf_instance._variants_db.get_study(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)
