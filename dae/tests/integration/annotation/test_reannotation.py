# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

from dae.genomic_resources.genomic_context import GenomicContext
from dae.gpf_instance import GPFInstance
from dae.parquet.schema2.annotate_schema2_parquet import cli
from dae.parquet.schema2.loader import ParquetLoader

from tests.integration.annotation.conftest import t4c8_study


def test_sj_index_is_preserved(
    t4c8_instance: GPFInstance,
    tmp_path: pathlib.Path,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    new_annotation = root_path / "new_annotation.yaml"
    new_annotation.write_text("""
        - position_score:
            resource_id: two
    """)

    gpf_instance_genomic_context_fixture(t4c8_instance)

    study_path = t4c8_study(t4c8_instance)

    cli([
        study_path, str(new_annotation),
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ])

    result_loader = ParquetLoader.load_from_dir(output_dir)

    vs = list(result_loader.fetch_summary_variants())
    sj_indices = [
        allele.attributes["sj_index"]
        for v in vs
        for allele in v.alt_alleles
    ]
    assert sj_indices == [
        1000000000000000001,
        1000000000000000002,
        1000000000000010001,
        1000000000000020001,
        1000000000000020002,
        1000000000000030001,
        1000000000000030002,
        1000000000000040001,
        1000000000000040002,
        1000000000000050001,
        1000000000000050002,
    ]
