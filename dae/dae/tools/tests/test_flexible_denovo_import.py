from dae.backends.storage.filesystem_genotype_storage import (
    FilesystemGenotypeStorage,
)
from dae.tools.simple_study_import import main


def test_import_iossifov2014_filesystem(
    fixture_dirname,
    dae_iossifov2014_config,
    default_dae_config,
    gpf_instance_2019,
    temp_dirname,
):

    pedigree_filename = dae_iossifov2014_config.family_filename
    denovo_filename = dae_iossifov2014_config.denovo_filename

    genotype_storage_id = "test_filesystem"
    study_id = "test_denovo_iossifov2014_fs"

    storage_config = getattr(default_dae_config.storage, genotype_storage_id)
    assert storage_config.storage_type == "filesystem"
    genotype_storage = FilesystemGenotypeStorage(
        storage_config,
        genotype_storage_id
    )
    assert genotype_storage

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-location",
        "location",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2019)

    storage_config = getattr(default_dae_config.storage, genotype_storage_id)
    assert storage_config.storage_type == "filesystem"

    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 16

    vs = list(study.query_variants(effect_types=["splice-site"]))
    assert len(vs) == 9

    vs = list(study.query_variants(effect_types=["no-frame-shift"]))
    assert len(vs) == 2


def assert_proper_flexible_short_variants(vs):
    assert len(vs) == 3
    v = vs[0]
    for a in v.alt_alleles:
        print(a, a.effects)
        print("\t>", a.effects.transcripts)
        assert a.chrom == "15"
        assert a.position == 80137553
        assert a.reference == "T"
        assert a.alternative == "TA"
        assert a.family_id == "f1"
        assert len(a.effects.transcripts) == 4

    v = vs[1]
    for a in v.alt_alleles:
        print(a, a.effects)
        print("\t>", a.effects.transcripts)

        assert a.chrom == "3"
        assert a.position == 56627767
        assert a.reference == "AAAGT"
        assert a.alternative == "A"
        assert a.family_id == "f2"
        # assert len(a.effect.transcripts) == 28

    v = vs[2]
    for a in v.alt_alleles:
        print(a, a.effects)
        print("\t>", a.effects.transcripts)
        assert a.chrom == "4"
        assert a.position == 83276456
        assert a.reference == "C"
        assert a.alternative == "T"
        assert a.family_id == "f1"
        # assert len(a.effect.transcripts) == 4


def test_flexible_denovo_default(
    fixture_dirname, gpf_instance_2019, temp_dirname
):

    pedigree_filename = fixture_dirname(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = fixture_dirname("flexible_short/flexible_short.txt")

    genotype_storage_id = "test_filesystem"
    study_id = "test_flexible_denovo_default"

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"
    genotype_storage = FilesystemGenotypeStorage(
        storage_config,
        genotype_storage_id
    )
    assert genotype_storage

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2019)

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"

    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)


def test_flexible_denovo_vcf(
    fixture_dirname, gpf_instance_2019, temp_dirname
):

    pedigree_filename = fixture_dirname(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = fixture_dirname("flexible_short/flexible_short_vcf.txt")

    genotype_storage_id = "test_filesystem"
    study_id = "test_flexible_denovo_vcf"

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"
    genotype_storage = FilesystemGenotypeStorage(
        storage_config,
        genotype_storage_id
    )
    assert genotype_storage

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-person-id",
        "person_id",
        "--denovo-chrom",
        "chrom",
        "--denovo-pos",
        "position",
        "--denovo-ref",
        "reference",
        "--denovo-alt",
        "alternative",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2019)

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"

    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)


def test_flexible_denovo_vcf_location(
    fixture_dirname, gpf_instance_2019, temp_dirname
):

    pedigree_filename = fixture_dirname(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = fixture_dirname(
        "flexible_short/flexible_short_vcf_location.txt"
    )

    genotype_storage_id = "test_filesystem"
    study_id = "test_flexible_denovo_vcf_location"

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"
    genotype_storage = FilesystemGenotypeStorage(
        storage_config,
        genotype_storage_id
    )
    assert genotype_storage

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-person-id",
        "person_id",
        "--denovo-location",
        "location",
        "--denovo-ref",
        "reference",
        "--denovo-alt",
        "alternative",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2019)

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"

    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)


def test_flexible_denovo_vcf_best_state(
    fixture_dirname, gpf_instance_2019, temp_dirname
):

    pedigree_filename = fixture_dirname(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = fixture_dirname(
        "flexible_short/flexible_short_vcf_best_state.txt"
    )

    genotype_storage_id = "test_filesystem"
    study_id = "test_flexible_denovo_vcf_best_state"

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"
    genotype_storage = FilesystemGenotypeStorage(
        storage_config,
        genotype_storage_id
    )
    assert genotype_storage

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--denovo-location",
        "location",
        "--denovo-ref",
        "reference",
        "--denovo-alt",
        "alternative",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2019)

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"

    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)


def test_flexible_denovo_dae_chrom_pos(
    fixture_dirname, gpf_instance_2019, temp_dirname
):

    pedigree_filename = fixture_dirname(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = fixture_dirname(
        "flexible_short/flexible_short_dae_chrom_pos.txt"
    )

    genotype_storage_id = "test_filesystem"
    study_id = "test_flexible_denovo_dae_chrom_pos"

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"
    genotype_storage = FilesystemGenotypeStorage(
        storage_config,
        genotype_storage_id
    )
    assert genotype_storage

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-chrom",
        "chrom",
        "--denovo-pos",
        "position",
        "--denovo-variant",
        "variant",
        "--denovo-family-id",
        "familyId",
        "--denovo-best-state",
        "bestState",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2019)

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"

    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)


def test_flexible_denovo_dae_person(
    fixture_dirname, gpf_instance_2019, temp_dirname
):

    pedigree_filename = fixture_dirname(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = fixture_dirname(
        "flexible_short/flexible_short_dae_person.txt"
    )

    genotype_storage_id = "test_filesystem"
    study_id = "test_flexible_denovo_dae_person"

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"
    genotype_storage = FilesystemGenotypeStorage(
        storage_config,
        genotype_storage_id
    )
    assert genotype_storage

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--denovo-variant",
        "variant",
        "--denovo-person-id",
        "person_id",
        "--genotype-storage",
        genotype_storage_id,
        "-o",
        temp_dirname,
    ]

    main(argv, gpf_instance_2019)

    storage_config = getattr(
        gpf_instance_2019.dae_config.storage, genotype_storage_id
    )
    assert storage_config.storage_type == "filesystem"

    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)
