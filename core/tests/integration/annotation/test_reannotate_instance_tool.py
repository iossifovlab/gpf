# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import tempfile
import textwrap

import pytest

from gpf.gpf_instance import GPFInstance
from gpf.tools.reannotate_instance import cli
from tests.integration.annotation.conftest import t4c8_study


def test_reannotate_instance_tool(
    t4c8_instance: GPFInstance,
    tmp_path: pathlib.Path,
) -> None:
    """
    Basic reannotate instance tool case.
    """
    # Setup study
    t4c8_study(t4c8_instance)

    # Expect default annotation in study variants
    study = t4c8_instance.get_genotype_data("study")
    vs = list(study.query_variants())
    assert all(v.has_attribute("score_one") for v in vs)
    assert not any(v.has_attribute("score_two") for v in vs)

    # Add default annotation config with different score resource
    instance_path = pathlib.Path(t4c8_instance.dae_dir)
    (instance_path / "annotation.yaml").write_text(
        textwrap.dedent(
            """- position_score:
                    resource_id: two
            """),
    )

    with open(instance_path / "gpf_instance.yaml", "a") as f:
        f.write(
            textwrap.dedent(
                """
                annotation:
                    conf_file: annotation.yaml
                """,
            ),
        )

    # Run the reannotate instance tool
    cli([
        "-j", "1",  # Single job to avoid using multiprocessing
        "--work-dir", str(tmp_path),
        "-i", str(instance_path / "gpf_instance.yaml"),
    ])
    t4c8_instance.reload()

    # Annotations should be updated
    study = t4c8_instance.get_genotype_data("study")
    vs = list(study.query_variants())

    assert all(v.has_attribute("score_two") for v in vs)
    assert not any(v.has_attribute("score_one") for v in vs)


def test_reannotate_instance_dry_run_gets_explicit_work_dir(
    t4c8_instance: GPFInstance,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # GPFInstance.get_annotation_pipeline makes its work directory with
    # tempfile.mkdtemp.
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    t4c8_study(t4c8_instance)
    instance_path = pathlib.Path(t4c8_instance.dae_dir)

    # --dry-run loads only the study pipeline, in
    # _is_study_annotation_up_to_date, and runs no reannotation task.
    cli([
        "--dry-run",
        "--work-dir", str(tmp_path / "work"),
        "-i", str(instance_path / "gpf_instance.yaml"),
    ])

    assert not [
        rec for rec in caplog.records
        if rec.name == "gain.annotation.annotation_factory"
        and "no `work_dir` passed" in rec.getMessage()
    ]
