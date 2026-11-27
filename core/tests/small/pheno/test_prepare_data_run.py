# pylint: disable=W0621,C0114,C0116,W0212,W0613
import logging
import shutil
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import duckdb
import pytest
import pytest_mock
from box import Box

from gpf.configuration.gpf_config_parser import GPFConfigParser
from gpf.configuration.schemas.phenotype_data import pheno_conf_schema
from gpf.pheno.common import (
    IMPORT_METADATA_TABLE,
    ImportManifest,
    MeasureType,
)
from gpf.pheno.pheno_data import (
    PhenotypeData,
    PhenotypeGroup,
    PhenotypeStudy,
)
from gpf.pheno.prepare_data import PreparePhenoBrowserBase
from gpf.pheno.registry import PhenoRegistry
from gpf.pheno.storage import PhenotypeStorage, PhenotypeStorageRegistry

PrepFactory = Callable[..., PreparePhenoBrowserBase]


@pytest.fixture
def run_kwargs(tmp_path: Path) -> dict[str, Any]:
    # ``jobs`` 1 makes ``TaskGraphCli.create_executor`` create a sequential
    # executor, so that no test starts a dask cluster. The task status
    # files go to ``tmp_path``, not to the current directory.
    return {"jobs": 1, "task_status_dir": str(tmp_path / "status")}


@pytest.fixture(autouse=True)
def no_figures(mocker: pytest_mock.MockerFixture) -> None:
    # The tests pin what ``run`` saves, not the figures. A draw function
    # that draws nothing keeps the tests fast and opens no figure.
    for draw in (
        "draw_measure_violinplot",
        "draw_ordinal_violin_distribution",
        "draw_categorical_violin_distribution",
    ):
        mocker.patch(f"gpf.pheno.prepare_data.{draw}", return_value=False)
    mocker.patch(
        "gpf.pheno.prepare_data.PreparePhenoBrowserBase.save_fig",
        return_value=("small.png", "large.png"),
    )


@pytest.fixture
def fake_regression(mocker: pytest_mock.MockerFixture) -> None:
    def build_regression(
        _phenotype_data: PhenotypeData, _images_dir: str,
        _dependent_measure: Any, _independent_measure: Any,
        _jitter: float,
    ) -> dict[str, Any]:
        return {
            "pvalue_regression_male": 0.25,
            "pvalue_regression_female": 0.5,
        }

    mocker.patch(
        "gpf.pheno.prepare_data.PreparePhenoBrowserBase.build_regression",
        side_effect=build_regression,
    )


@pytest.fixture
def pheno_registry(
    fake_pheno_db_dir: Path,
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
) -> Generator[PhenoRegistry, None, None]:
    # The session fixtures ``fake_phenotype_data`` and
    # ``fake_phenotype_group`` share their measure objects with other
    # tests, and some of those tests change a measure in place. A registry
    # for each test gives ``run`` measures that no other test has changed.
    registry = PhenoRegistry(
        fake_pheno_storage_registry,
        configurations_dir=str(fake_pheno_db_dir),
    )
    yield registry
    registry.shutdown()


@pytest.fixture
def study(pheno_registry: PhenoRegistry) -> PhenotypeStudy:
    data = pheno_registry.get_phenotype_data("fake")
    assert isinstance(data, PhenotypeStudy)
    return data


@pytest.fixture
def group(pheno_registry: PhenoRegistry) -> PhenotypeGroup:
    data = pheno_registry.get_phenotype_data("fake_group")
    assert isinstance(data, PhenotypeGroup)
    return data


@pytest.fixture
def make_prep(
    fake_pheno_db_dir: Path,
    fake_pheno_storage_registry: PhenotypeStorageRegistry,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[PrepFactory, None, None]:
    preps: list[PreparePhenoBrowserBase] = []

    def factory(
        phenotype_data: PhenotypeData, *,
        pheno_db_dir: Path = fake_pheno_db_dir,
        storage_registry: PhenotypeStorageRegistry = (
            fake_pheno_storage_registry),
        pheno_regressions: Box | None = None,
    ) -> PreparePhenoBrowserBase:
        monkeypatch.setattr(phenotype_data, "cache_path", tmp_path)
        browser = PhenotypeData.create_browser(
            phenotype_data, read_only=False,
        )
        prep = PreparePhenoBrowserBase(
            pheno_db_dir, storage_registry, phenotype_data, browser,
            cache_dir=tmp_path / "cache",
            images_dir=tmp_path / "images",
            pheno_regressions=pheno_regressions,
        )
        preps.append(prep)
        return prep

    yield factory
    for prep in preps:
        prep.close()


CopiedPheno = tuple[Path, PhenotypeStorageRegistry, PhenotypeData]


@pytest.fixture
def copy_without_manifest(
    fake_pheno_db_dir: Path,
    tmp_path: Path,
) -> Generator[Callable[[str, str], CopiedPheno], None, None]:
    # Copies the fake phenotype databases, empties the import manifests of
    # the study ``emptied`` in the copy and loads ``pheno_id`` from it.
    registries: list[PhenoRegistry] = []

    def factory(emptied: str, pheno_id: str) -> CopiedPheno:
        pheno_dir = tmp_path / "pheno"
        shutil.copytree(fake_pheno_db_dir, pheno_dir)
        with duckdb.connect(pheno_dir / emptied / f"{emptied}.db") as conn:
            conn.execute("DELETE FROM import_metadata")
        storage_registry = PhenotypeStorageRegistry()
        storage_registry.register_default_storage(
            PhenotypeStorage.from_config(
                {"id": "copy_storage", "base_dir": pheno_dir},
            ),
        )
        registry = PhenoRegistry(
            storage_registry, configurations_dir=str(pheno_dir),
        )
        registries.append(registry)
        return (
            pheno_dir, storage_registry,
            registry.get_phenotype_data(pheno_id),
        )

    yield factory
    for registry in registries:
        registry.shutdown()


@pytest.fixture
def fake_regressions(fake_phenotype_data_config: str) -> Box:
    regressions: Box = GPFConfigParser.load_config(
        fake_phenotype_data_config, pheno_conf_schema,
    )["regressions"]
    return regressions


def _query(prep: PreparePhenoBrowserBase, sql: str) -> list[tuple]:
    with prep.browser.connection.cursor() as cursor:
        return cursor.execute(sql).fetchall()


def _browser_measure_ids(prep: PreparePhenoBrowserBase) -> list[str]:
    rows = _query(
        prep, "SELECT measure_id FROM variable_browser ORDER BY measure_id",
    )
    return [row[0] for row in rows]


def _regression_value_keys(
    prep: PreparePhenoBrowserBase,
) -> list[tuple[str, str]]:
    return _query(
        prep,
        "SELECT measure_id, regression_id FROM regression_values "
        "ORDER BY measure_id, regression_id",
    )


def _browser_manifests(prep: PreparePhenoBrowserBase) -> list[ImportManifest]:
    return ImportManifest.from_table(
        prep.browser.connection, IMPORT_METADATA_TABLE,
    )


def _all_measures(phenotype_data: PhenotypeData) -> list[Any]:
    return sorted(
        (
            measure
            for instrument in phenotype_data.instruments.values()
            for measure in instrument.measures.values()
        ),
        key=lambda measure: measure.measure_id,
    )


def _leaf_import_configs(leaves: list[PhenotypeStudy]) -> list[Any]:
    return [
        ImportManifest.from_table(
            leaf.db.connection, IMPORT_METADATA_TABLE,
        )[0].import_config
        for leaf in leaves
    ]


def test_run_saves_every_measure_of_a_study(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    study: PhenotypeStudy,
) -> None:
    prep = make_prep(study)

    prep.run(**run_kwargs)

    assert _browser_measure_ids(prep) == [
        m.measure_id for m in _all_measures(study)]


def test_run_without_regressions_saves_no_regression(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    study: PhenotypeStudy,
) -> None:
    prep = make_prep(study)

    prep.run(**run_kwargs)

    assert _query(prep, "SELECT * FROM regression") == []
    assert _regression_value_keys(prep) == []


@pytest.mark.usefixtures("fake_regression")
def test_run_with_regressions_saves_the_regressions(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    study: PhenotypeStudy,
    fake_regressions: Box,
) -> None:
    prep = make_prep(
        study, pheno_regressions=fake_regressions,
    )

    prep.run(**run_kwargs)

    assert sorted(_query(
        prep,
        "SELECT regression_id, instrument_name, measure_name, display_name "
        "FROM regression",
    )) == [
        ("age", "i1", "age", "age"),
        ("nviq", "i1", "iq", "nonverbal iq"),
    ]


@pytest.mark.usefixtures("fake_regression")
def test_run_with_regressions_saves_the_regression_values(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    study: PhenotypeStudy,
    fake_regressions: Box,
) -> None:
    prep = make_prep(
        study, pheno_regressions=fake_regressions,
    )
    regressands = [
        measure for measure in _all_measures(study)
        if measure.measure_type in {
            MeasureType.continuous, MeasureType.ordinal}
        and measure.measure_name not in {"age", "iq"}
    ]

    prep.run(**run_kwargs)

    assert regressands
    assert _regression_value_keys(prep) == [
        (measure.measure_id, reg_id)
        for measure in regressands
        for reg_id in ("age", "nviq")
    ]


@pytest.mark.usefixtures("fake_regression")
def test_run_saves_a_measure_that_has_no_regression_values(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    study: PhenotypeStudy,
    fake_regressions: Box,
) -> None:
    prep = make_prep(
        study, pheno_regressions=fake_regressions,
    )
    categorical = [
        measure.measure_id
        for measure in _all_measures(study)
        if measure.measure_type == MeasureType.categorical
    ]

    prep.run(**run_kwargs)

    assert categorical
    assert set(categorical) <= set(_browser_measure_ids(prep))
    assert not {
        measure_id for measure_id, _ in _regression_value_keys(prep)
    } & set(categorical)


def test_run_raises_runtime_error_when_a_task_fails(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    study: PhenotypeStudy,
    tmp_path: Path,
) -> None:
    # No phenotype data configuration lives in this directory, so the
    # task of each measure fails to find its phenotype data.
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    prep = make_prep(study, pheno_db_dir=empty_dir)

    with pytest.raises(RuntimeError, match=r"^Failed to create images$") as e:
        prep.run(**run_kwargs)

    assert e.value.__cause__ is not None
    assert _browser_manifests(prep) == []


def test_run_of_a_study_writes_the_manifest_of_the_study(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    study: PhenotypeStudy,
) -> None:
    prep = make_prep(study)

    prep.run(**run_kwargs)

    assert [
        manifest.import_config for manifest in _browser_manifests(prep)
    ] == _leaf_import_configs([study])


def test_run_of_a_group_writes_the_manifest_of_each_leaf(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    group: PhenotypeGroup,
) -> None:
    leaves = group.get_leaves()
    assert len(leaves) == 2
    prep = make_prep(group)

    prep.run(**run_kwargs)

    assert [
        manifest.import_config for manifest in _browser_manifests(prep)
    ] == _leaf_import_configs(leaves)


def test_run_skips_a_leaf_with_no_manifest(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    copy_without_manifest: Callable[[str, str], CopiedPheno],
    caplog: pytest.LogCaptureFixture,
) -> None:
    pheno_dir, storage_registry, study = copy_without_manifest(
        "fake_i1", "fake_i1",
    )
    prep = make_prep(
        study, pheno_db_dir=pheno_dir, storage_registry=storage_registry,
    )

    with caplog.at_level(logging.WARNING, logger="gpf.pheno.prepare_data"):
        prep.run(**run_kwargs)

    assert _query(prep, "SELECT COUNT(*) FROM import_metadata") == [(0,)]
    assert "fake_i1 has no import manifests" in caplog.text


def test_run_of_a_group_keeps_the_leaves_after_a_leaf_with_no_manifest(
    make_prep: PrepFactory,
    run_kwargs: dict[str, Any],
    copy_without_manifest: Callable[[str, str], CopiedPheno],
) -> None:
    # The first leaf of ``fake_group`` has no manifest. The manifest of the
    # second leaf must still be written: the empty leaf is skipped, and the
    # loop goes on.
    pheno_dir, storage_registry, group = copy_without_manifest(
        "fake", "fake_group",
    )
    assert isinstance(group, PhenotypeGroup)
    leaves = group.get_leaves()
    assert [leaf.pheno_id for leaf in leaves] == ["fake", "fake2"]
    prep = make_prep(
        group, pheno_db_dir=pheno_dir, storage_registry=storage_registry,
    )

    prep.run(**run_kwargs)

    assert [
        manifest.import_config for manifest in _browser_manifests(prep)
    ] == _leaf_import_configs(leaves[1:])
