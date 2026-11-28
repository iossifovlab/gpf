# pylint: disable=W0621,C0114,C0116
import argparse
import logging
import textwrap
from pathlib import Path
from typing import Any, cast

import duckdb
import pytest
import yaml
from gain.genomic_resources.histogram import CategoricalHistogramConfig
from gain.genomic_resources.testing import (
    setup_directories,
    setup_pedigree,
)

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.pheno import pheno_import
from gpf.pheno.common import (
    IMPORT_METADATA_TABLE,
    DestinationConfig,
    ImportManifest,
    InferenceConfig,
    InstrumentConfig,
    InstrumentDescriptionsConfig,
    MeasureDescriptionsConfig,
    MeasureHistogramConfigs,
    PhenoImportConfig,
    RegressionMeasure,
    StudyConfig,
)
from gpf.pheno.pheno_data import PhenotypeStudy
from gpf.pheno.pheno_import import (
    generate_phenotype_data_config,
    import_pheno_data,
)

ALL_MEASURES = {
    "instr1.m1",
    "instr1.m2",
    "instr1.m3",
    "pheno_common.test_col",
}


@pytest.fixture
def input_dir(tmp_path: Path) -> Path:
    root = tmp_path / "input"
    setup_pedigree(
        root / "pedigree.ped",
        """
        familyId	personId	dadId	momId	sex	status	role	test_col
        fam1	fam1.mom	0	0	2	1	mom	test1
        fam1	fam1.dad	0	0	1	1	dad	test2
        fam1	fam1.prb	fam1.dad	fam1.mom	2	2	prb	test3
        fam2	fam2.mom	0	0	2	1	mom	test4
        fam2	fam2.dad	0	0	1	1	dad	test5
        fam2	fam2.prb	fam2.dad	fam2.mom	2	2	prb	test6
        """)
    setup_directories(root, {
        "instruments": {
            "instr1.csv": textwrap.dedent("""
                person_id,m1,m2,m3
                fam1.mom,1,8,3
                fam1.dad,3,1,3
                fam1.prb,4,0,3
                fam2.mom,9,4,3
                fam2.dad,10,,3
                fam2.prb,23,asdf,3
            """),
        },
    })
    return root


def build_config(
    input_dir: Path, work_dir: Path, **kwargs: Any,
) -> PhenoImportConfig:
    return PhenoImportConfig(
        id="test",
        input_dir=str(input_dir),
        work_dir=str(work_dir),
        instrument_files=["instruments"],
        pedigree="pedigree.ped",
        person_column="person_id",
        **kwargs,
    )


def task_graph_args(*, force: bool) -> argparse.Namespace:
    return argparse.Namespace(
        jobs=1,
        force=force,
        task_status_dir=None,
        dask_cluster_name=None,
        dask_cluster_config_file=None,
    )


def read_study(db_path: Path) -> PhenotypeStudy:
    return PhenotypeStudy("test", str(db_path))


def count_rows(db_path: Path, table: str) -> int:
    with duckdb.connect(str(db_path), read_only=True) as connection:
        row = connection.execute(
            f"SELECT COUNT(*) FROM {table}",  # ruff: ignore[hardcoded-sql-expression]
        ).fetchone()
    assert row is not None
    return int(row[0])


def test_import_creates_nested_work_dir(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "a" / "b" / "work"
    config = build_config(input_dir, work_dir)

    import_pheno_data(config)

    assert (work_dir / "test.db").exists()


def test_import_without_task_graph_args_replaces_existing_db(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    (work_dir / "test.db").write_text("stale")
    config = build_config(input_dir, work_dir)

    import_pheno_data(config)

    assert set(read_study(work_dir / "test.db").measures) == ALL_MEASURES


def test_import_with_force_replaces_existing_db(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    (work_dir / "test.db").write_text("stale")
    config = build_config(input_dir, work_dir)

    import_pheno_data(config, task_graph_args=task_graph_args(force=True))

    assert set(read_study(work_dir / "test.db").measures) == ALL_MEASURES


def test_import_without_force_exits_on_existing_db(
    input_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    db_path = work_dir / "test.db"
    db_path.write_text("stale")
    config = build_config(input_dir, work_dir)

    with pytest.raises(SystemExit) as exc_info:
        import_pheno_data(
            config, task_graph_args=task_graph_args(force=False))

    assert exc_info.value.code == 1
    assert capsys.readouterr().out == (
        f"Pheno DB already exists at {db_path}!\n"
        "Use --force or specify another directory.\n"
    )
    assert db_path.read_text() == "stale"
    assert not (work_dir / "test.yaml").exists()


def test_import_destination_error_raises_before_writing_db(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(
        input_dir, work_dir, destination=DestinationConfig())
    gpf_instance = cast(GPFInstance, object())

    with pytest.raises(ValueError, match="without a storage id"):
        import_pheno_data(config, gpf_instance=gpf_instance)

    assert work_dir.is_dir()
    assert not list(work_dir.iterdir())


def test_import_without_inference_config_skips_pedigree_columns(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir)

    import_pheno_data(config)

    assert set(read_study(work_dir / "test.db").measures) == ALL_MEASURES


def test_import_loads_inference_config_from_file(
    input_dir: Path, tmp_path: Path,
) -> None:
    (input_dir / "inference.yaml").write_text(
        yaml.dump({"instr1.m2": {"skip": True}}))
    work_dir = tmp_path / "work"
    config = build_config(
        input_dir, work_dir, inference_config="inference.yaml")

    import_pheno_data(config)

    assert set(read_study(work_dir / "test.db").measures) == \
        ALL_MEASURES - {"instr1.m2"}


def test_import_empty_inference_config_path_skips_nothing(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir, inference_config="")

    import_pheno_data(config)

    assert set(read_study(work_dir / "test.db").measures) == ALL_MEASURES


def test_import_uses_inference_config_dict(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(
        input_dir, work_dir,
        inference_config={"instr1.m3": InferenceConfig(skip=True)},
    )

    import_pheno_data(config)

    assert set(read_study(work_dir / "test.db").measures) == \
        ALL_MEASURES - {"instr1.m3"}


def test_import_adds_pheno_common_entries_to_inference_config_dict(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(
        input_dir, work_dir,
        inference_config={"instr1.m3": InferenceConfig(skip=True)},
    )

    import_pheno_data(config)

    entries = dict(cast(dict[str, Any], config.inference_config))
    assert entries["pheno_common.familyId"] == {"skip": True}
    assert entries["pheno_common.personId"] == {"skip": True}


def test_import_without_histogram_configs_stores_no_histogram_config(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir)

    import_pheno_data(config)

    measure = read_study(work_dir / "test.db").measures["instr1.m1"]
    assert measure.histogram_config is None


def test_import_uses_histogram_configs_object(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(
        input_dir, work_dir,
        histogram_configs=MeasureHistogramConfigs(
            categorical_config={"instr1.m1": {"label_rotation": 45}},
        ),
    )

    import_pheno_data(config)

    measure = read_study(work_dir / "test.db").measures["instr1.m1"]
    assert isinstance(measure.histogram_config, CategoricalHistogramConfig)
    assert measure.histogram_config.label_rotation == 45


def test_import_loads_histogram_configs_assigned_as_path(
    input_dir: Path, tmp_path: Path,
) -> None:
    (input_dir / "histograms.yaml").write_text(yaml.dump({
        "categorical_config": {"instr1.m1": {"label_rotation": 30}},
    }))
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir)
    config.histogram_configs = cast(
        MeasureHistogramConfigs, "histograms.yaml")

    import_pheno_data(config)

    measure = read_study(work_dir / "test.db").measures["instr1.m1"]
    assert isinstance(measure.histogram_config, CategoricalHistogramConfig)
    assert measure.histogram_config.label_rotation == 30


def test_import_rejects_histogram_configs_path_at_validation(
    input_dir: Path, tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="histogram_configs"):
        build_config(
            input_dir, tmp_path / "work",
            histogram_configs="histograms.yaml",
        )


def test_import_skip_pedigree_measures_drops_pheno_common(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(
        input_dir, work_dir, skip_pedigree_measures=True)

    import_pheno_data(config)

    assert set(read_study(work_dir / "test.db").measures) == \
        ALL_MEASURES - {"pheno_common.test_col"}


def test_import_reads_pheno_common_with_tab_delimiter(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir, delimiter=";")
    config.instrument_files = [
        InstrumentConfig(path="instruments/instr1.csv", delimiter=","),
    ]

    import_pheno_data(config)

    assert set(read_study(work_dir / "test.db").measures) == ALL_MEASURES


def test_import_reads_pheno_common_from_relative_input_dir(
    input_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(input_dir.parent)
    work_dir = tmp_path / "work"
    config = build_config(Path(input_dir.name), work_dir)
    seen: list[Any] = []
    original = pheno_import.create_import_tasks

    def spy(task_graph: Any, instruments: Any, *args: Any) -> None:
        seen.extend(instruments)
        original(task_graph, instruments, *args)

    monkeypatch.setattr(pheno_import, "create_import_tasks", spy)

    import_pheno_data(config)

    pheno_common = [i for i in seen if i.name == "pheno_common"]
    assert pheno_common[0].files == [input_dir / "pedigree.ped"]
    assert pheno_common[0].files[0].is_absolute()
    assert set(read_study(work_dir / "test.db").measures) == ALL_MEASURES


def test_import_writes_measure_and_instrument_descriptions(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(
        input_dir, work_dir,
        data_dictionary=MeasureDescriptionsConfig(
            dictionary={"instr1": {"m1": "measure one"}},
        ),
        instrument_dictionary=InstrumentDescriptionsConfig(
            dictionary={"instr1": "instrument one"},
        ),
    )

    import_pheno_data(config)

    measure = read_study(work_dir / "test.db").measures["instr1.m1"]
    assert measure.description == "measure one"
    assert measure.instrument_description == "instrument one"
    assert count_rows(work_dir / "test.db", "measure_descriptions") == 1
    assert count_rows(work_dir / "test.db", "instrument_descriptions") == 1


def test_import_empty_descriptions_write_no_rows(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(
        input_dir, work_dir,
        data_dictionary=MeasureDescriptionsConfig(dictionary={}),
        instrument_dictionary=InstrumentDescriptionsConfig(dictionary={}),
    )

    import_pheno_data(config)

    measure = read_study(work_dir / "test.db").measures["instr1.m1"]
    assert measure.description is None
    assert count_rows(work_dir / "test.db", "measure_descriptions") == 0
    assert count_rows(work_dir / "test.db", "instrument_descriptions") == 0


def test_import_writes_import_manifest(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir)

    import_pheno_data(config)

    with duckdb.connect(str(work_dir / "test.db"), read_only=True) as conn:
        manifests = ImportManifest.from_table(conn, IMPORT_METADATA_TABLE)
    assert [m.import_config for m in manifests] == [config]


def test_import_writes_default_study_config(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir)

    import_pheno_data(config)

    assert (work_dir / "test.yaml").read_text() == \
        generate_phenotype_data_config("test", None, None)


def test_import_loads_regressions_into_caller_study_config(
    input_dir: Path, tmp_path: Path,
) -> None:
    regression = {
        "instrument_name": "instr1",
        "measure_names": ["m1"],
        "jitter": 0.1,
        "display_name": "M1",
    }
    (input_dir / "regressions.yaml").write_text(
        yaml.dump({"regression": {"reg1": regression}}))
    work_dir = tmp_path / "work"
    study_config = StudyConfig(regressions="regressions.yaml")
    config = build_config(input_dir, work_dir, study_config=study_config)

    import_pheno_data(config)

    assert config.study_config is study_config
    assert study_config.regressions == {
        "reg1": RegressionMeasure.model_validate(regression),
    }
    written = yaml.safe_load((work_dir / "test.yaml").read_text())
    assert written["regressions"] == {"reg1": regression}


def test_import_without_destination_copies_nothing(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir)

    import_pheno_data(config)

    assert {p.name for p in tmp_path.iterdir()} == {"input", "work"}


def test_import_copies_to_missing_storage_dir(
    input_dir: Path, tmp_path: Path,
) -> None:
    work_dir = tmp_path / "work"
    storage_dir = tmp_path / "x" / "storage"
    config = build_config(
        input_dir, work_dir,
        destination=DestinationConfig(storage_dir=str(storage_dir)),
    )

    import_pheno_data(config)

    assert (storage_dir / "test" / "test.yaml").read_text() == \
        (work_dir / "test.yaml").read_text()
    assert set(read_study(storage_dir / "test" / "test.db").measures) == \
        ALL_MEASURES


def test_import_into_storage_dir_warns_on_same_file_copies(
    input_dir: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    storage_dir = tmp_path / "storage"
    work_dir = storage_dir / "test"
    config = build_config(
        input_dir, work_dir,
        destination=DestinationConfig(storage_dir=str(storage_dir)),
    )

    with caplog.at_level(logging.WARNING, logger="gpf.pheno.pheno_import"):
        import_pheno_data(config)

    messages = [r.getMessage() for r in caplog.records]
    assert (
        "Tried to copy pheno config to where it already is "
        f"{work_dir / 'test.yaml'}"
    ) in messages
    assert (
        "Tried to copy pheno data to where it already is "
        f"{work_dir / 'test.db'}"
    ) in messages
    assert set(read_study(work_dir / "test.db").measures) == ALL_MEASURES


def test_import_finishes_when_measure_classification_fails(
    input_dir: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    (input_dir / "broken.csv").write_text("pid,m4\nfam1.mom,1\n")
    work_dir = tmp_path / "work"
    config = build_config(input_dir, work_dir, skip_pedigree_measures=True)
    config.instrument_files = ["broken.csv"]

    with caplog.at_level(logging.ERROR, logger="gpf.pheno.pheno_import"):
        import_pheno_data(config)

    assert "Failed to classify measure" in [
        r.getMessage() for r in caplog.records]
    assert (work_dir / "test.yaml").exists()
    assert not read_study(work_dir / "test.db").measures
