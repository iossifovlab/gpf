# pylint: disable=W0621,C0114,C0116,W0212,W0613

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

    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 16

    vs = list(study.query_variants(effect_types=["splice-site"]))
    assert len(vs) == 9

    vs = list(study.query_variants(effect_types=["no-frame-shift"]))
    assert len(vs) == 2


def assert_proper_flexible_short_variants(fvs):
    assert len(fvs) == 3
    v = fvs[0]
    for fa in v.alt_alleles:
        assert fa.chrom == "15"
        assert fa.position == 80137553
        assert fa.reference == "T"
        assert fa.alternative == "TA"
        assert fa.family_id == "f1"
        assert len(fa.effects.transcripts) == 4

    v = fvs[1]
    for fa in v.alt_alleles:
        assert fa.chrom == "3"
        assert fa.position == 56627767
        assert fa.reference == "AAAGT"
        assert fa.alternative == "A"
        assert fa.family_id == "f2"

    v = fvs[2]
    for fa in v.alt_alleles:
        assert fa.chrom == "4"
        assert fa.position == 83276456
        assert fa.reference == "C"
        assert fa.alternative == "T"
        assert fa.family_id == "f1"


def test_flexible_denovo_default(
    fixture_dirname, gpf_instance_2019, temp_dirname
):

    pedigree_filename = fixture_dirname(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = fixture_dirname("flexible_short/flexible_short.txt")

    genotype_storage_id = "test_filesystem"
    study_id = "test_flexible_denovo_default"

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
    gpf_instance_2019.reload()
    study = gpf_instance_2019.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert_proper_flexible_short_variants(vs)
