# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from tests.foobar_import import foobar_gpf
from dae.tools.simple_study_import import main
from dae.gpf_instance import GPFInstance


@pytest.mark.skip(reason="wrong reference genome")
@pytest.mark.parametrize(
    "storage_id",
    [
        "genotype_impala",
        "genotype_impala_2",
        "genotype_filesystem",
    ]
)
def test_import_iossifov2014_filesystem(
        tmp_path_factory, storage_id, fixture_dirname):
    root_path = tmp_path_factory.mktemp(storage_id)
    foobar_gpf(root_path)
    gpf_instance = GPFInstance(work_dir=str(root_path / "gpf_instance"))

    pedigree_filename = \
        fixture_dirname("dae_iossifov2014/iossifov2014_families.ped")
    denovo_filename = \
        fixture_dirname("dae_iossifov2014/iossifov2014.txt")

    study_id = f"test_denovo_iossifov2014_{storage_id}"

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
        storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 16


@pytest.mark.parametrize(
    "storage_id",
    [
        "genotype_impala",
        "genotype_impala_2",
        "genotype_filesystem",
    ]
)
def test_flexible_denovo_default(
        tmp_path_factory, storage_id, local_fixture):
    root_path = tmp_path_factory.mktemp(storage_id)
    foobar_gpf(root_path)
    gpf_instance = GPFInstance(work_dir=str(root_path / "gpf_instance"))

    pedigree_filename = local_fixture(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = local_fixture("flexible_short/flexible_short.txt")

    study_id = f"test_flexible_denovo_default_{storage_id}"

    argv = [
        pedigree_filename,
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        denovo_filename,
        "--genotype-storage",
        storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


@pytest.mark.parametrize(
    "storage_id",
    [
        "genotype_impala",
        "genotype_impala_2",
        "genotype_filesystem",
    ]
)
def test_flexible_denovo_vcf(
        tmp_path_factory, storage_id, local_fixture):
    root_path = tmp_path_factory.mktemp(storage_id)
    foobar_gpf(root_path)
    gpf_instance = GPFInstance(work_dir=str(root_path / "gpf_instance"))

    pedigree_filename = local_fixture(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = local_fixture("flexible_short/flexible_short_vcf.txt")

    study_id = f"test_flexible_denovo_vcf{storage_id}"

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
        "--genotype-storage", storage_id,
        "-o", str(root_path / "output")
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


@pytest.mark.parametrize(
    "storage_id",
    [
        "genotype_impala",
        "genotype_impala_2",
        "genotype_filesystem",
    ]
)
def test_flexible_denovo_vcf_location(
        tmp_path_factory, storage_id, local_fixture):
    root_path = tmp_path_factory.mktemp(storage_id)
    foobar_gpf(root_path)
    gpf_instance = GPFInstance(work_dir=str(root_path / "gpf_instance"))

    pedigree_filename = local_fixture(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = local_fixture(
        "flexible_short/flexible_short_vcf_location.txt"
    )

    study_id = f"test_flexible_denovo_vcf_location_{storage_id}"

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
        storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


@pytest.mark.parametrize(
    "storage_id",
    [
        "genotype_impala",
        "genotype_impala_2",
        "genotype_filesystem",
    ]
)
def test_flexible_denovo_vcf_best_state(
        tmp_path_factory, storage_id, local_fixture):
    root_path = tmp_path_factory.mktemp(storage_id)
    foobar_gpf(root_path)
    gpf_instance = GPFInstance(work_dir=str(root_path / "gpf_instance"))

    pedigree_filename = local_fixture(
        "flexible_short/flexible_short_families.ped")
    denovo_filename = local_fixture(
        "flexible_short/flexible_short_vcf_best_state.txt")

    study_id = f"test_flexible_denovo_vcf_best_state_{storage_id}"

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
        storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


@pytest.mark.parametrize(
    "storage_id",
    [
        "genotype_impala",
        "genotype_impala_2",
        "genotype_filesystem",
    ]
)
def test_flexible_denovo_dae_chrom_pos(
        tmp_path_factory, storage_id, local_fixture):
    root_path = tmp_path_factory.mktemp(storage_id)
    foobar_gpf(root_path)
    gpf_instance = GPFInstance(work_dir=str(root_path / "gpf_instance"))

    pedigree_filename = local_fixture(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = local_fixture(
        "flexible_short/flexible_short_dae_chrom_pos.txt"
    )

    study_id = f"test_flexible_denovo_dae_chrom_pos_{storage_id}"

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
        storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


@pytest.mark.parametrize(
    "storage_id",
    [
        "genotype_impala",
        "genotype_impala_2",
        "genotype_filesystem",
    ]
)
def test_flexible_denovo_dae_person(
        tmp_path_factory, storage_id, local_fixture):
    root_path = tmp_path_factory.mktemp(storage_id)
    foobar_gpf(root_path)
    gpf_instance = GPFInstance(work_dir=str(root_path / "gpf_instance"))

    pedigree_filename = local_fixture(
        "flexible_short/flexible_short_families.ped"
    )
    denovo_filename = local_fixture(
        "flexible_short/flexible_short_dae_person.txt"
    )

    study_id = f"test_flexible_denovo_dae_person_{storage_id}"

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
        storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)
    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3
