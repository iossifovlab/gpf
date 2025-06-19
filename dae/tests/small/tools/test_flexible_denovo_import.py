# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
from collections.abc import Callable

import pytest
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.testing.foobar_import import foobar_gpf
from dae.tools.simple_study_import import main


@pytest.fixture(scope="module")
def resources_dir(request: pytest.FixtureRequest) -> pathlib.Path:
    resources_path = os.path.join(
        os.path.dirname(os.path.realpath(request.module.__file__)),
        "resources")
    return pathlib.Path(resources_path)


def test_flexible_denovo_default(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
    resources_dir: pathlib.Path,
) -> None:
    root_path = tmp_path_factory.mktemp("test_flexible_denovo_default")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    pedigree_filename = resources_dir / \
        "flexible_short/flexible_short_families.ped"
    denovo_filename = resources_dir / "flexible_short/flexible_short.txt"

    study_id = f"test_flexible_denovo_default_{genotype_storage.storage_id}"

    argv = [
        str(pedigree_filename),
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        str(denovo_filename),
        "--denovo-family-id", "familyId",
        "--denovo-location", "location",
        "--denovo-variant", "variant",
        "--denovo-best-state", "bestState",
        "--genotype-storage",
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


def test_flexible_denovo_vcf(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
    resources_dir: pathlib.Path,
) -> None:
    root_path = tmp_path_factory.mktemp("test_flexible_denovo_vcf")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    pedigree_filename = resources_dir / \
        "flexible_short/flexible_short_families.ped"
    denovo_filename = resources_dir / "flexible_short/flexible_short_vcf.txt"

    study_id = f"test_flexible_denovo_vcf{genotype_storage.storage_id}"

    argv = [
        str(pedigree_filename),
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        str(denovo_filename),
        "--genotype-storage", genotype_storage.storage_id,
        "-o", str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


def test_flexible_denovo_vcf_location(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
    resources_dir: pathlib.Path,
) -> None:
    root_path = tmp_path_factory.mktemp("test_flexible_denovo_vcf_location")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    pedigree_filename = resources_dir / \
        "flexible_short/flexible_short_families.ped"
    denovo_filename = resources_dir / \
        "flexible_short/flexible_short_vcf_location.txt"

    study_id = (
        f"test_flexible_denovo_vcf_location_"
        f"{genotype_storage.storage_id}")

    argv = [
        str(pedigree_filename),
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        str(denovo_filename),
        "--denovo-person-id",
        "person_id",
        "--denovo-location",
        "location",
        "--denovo-ref",
        "reference",
        "--denovo-alt",
        "alternative",
        "--genotype-storage",
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


def test_flexible_denovo_vcf_best_state(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
    resources_dir: pathlib.Path,
) -> None:
    root_path = tmp_path_factory.mktemp("test_flexible_denovo_vcf_best_state")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    pedigree_filename = resources_dir / \
        "flexible_short/flexible_short_families.ped"
    denovo_filename = resources_dir / \
        "flexible_short/flexible_short_vcf_best_state.txt"

    study_id = (
        f"test_flexible_denovo_vcf_best_state_"
        f"{genotype_storage.storage_id}"
    )

    argv = [
        str(pedigree_filename),
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        str(denovo_filename),
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
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


def test_flexible_denovo_dae_chrom_pos(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
    resources_dir: pathlib.Path,
) -> None:
    root_path = tmp_path_factory.mktemp("test_flexible_denovo_dae_chrom_pos")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    pedigree_filename = resources_dir / \
        "flexible_short/flexible_short_families.ped"
    denovo_filename = resources_dir / \
        "flexible_short/flexible_short_dae_chrom_pos.txt"

    study_id = (
        f"test_flexible_denovo_dae_chrom_pos_"
        f"{genotype_storage.storage_id}"
    )

    argv = [
        str(pedigree_filename),
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        str(denovo_filename),
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
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)

    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3


def test_flexible_denovo_dae_person(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
    resources_dir: pathlib.Path,
) -> None:
    root_path = tmp_path_factory.mktemp("test_flexible_denovo_dae_person")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)

    pedigree_filename = resources_dir / \
        "flexible_short/flexible_short_families.ped"
    denovo_filename = resources_dir / \
        "flexible_short/flexible_short_dae_person.txt"

    study_id = (
        f"test_flexible_denovo_dae_person_"
        f"{genotype_storage.storage_id}"
    )

    argv = [
        str(pedigree_filename),
        "--id",
        study_id,
        "--skip-reports",
        "--denovo-file",
        str(denovo_filename),
        "--denovo-variant",
        "variant",
        "--denovo-person-id",
        "person_id",
        "--denovo-location",
        "location",
        "--genotype-storage",
        genotype_storage.storage_id,
        "-o",
        str(root_path / "output"),
    ]

    main(argv, gpf_instance)
    gpf_instance.reload()
    study = gpf_instance.get_genotype_data(study_id)
    assert study is not None

    vs = list(study.query_variants())
    assert len(vs) == 3
