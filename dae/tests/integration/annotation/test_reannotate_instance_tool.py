# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

from dae.annotation.reannotate_instance import cli
from dae.gpf_instance import GPFInstance

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
    pathlib.Path(t4c8_instance.dae_dir, "annotation.yaml").write_text(
        textwrap.dedent(
            """- position_score:
                    resource_id: two
            """),
    )

    with open(f"{t4c8_instance.dae_dir}/gpf_instance.yaml", "a") as f:
        f.write(
            textwrap.dedent(
                """
                annotation:
                    conf_file: annotation.yaml
                """,
            ),
        )

    new_instance = GPFInstance.build(
        f"{t4c8_instance.dae_dir}/gpf_instance.yaml",
        grr=t4c8_instance.grr,
    )

    # Run the reannotate instance tool
    cli(
        ["-j", "1",  # Single job to avoid using multiprocessing
         "--work-dir", str(tmp_path)],
        new_instance,
    )
    new_instance.reload()

    # Annotations should be updated
    study = new_instance.get_genotype_data("study")
    vs = list(study.query_variants())

    assert all(v.has_attribute("score_two") for v in vs)
    assert not any(v.has_attribute("score_one") for v in vs)
