from box import Box

from .conftest import relative_to_this_test_folder
from annotation.annotation_pipeline import PipelineAnnotator


def test_simple(capsys, variants_io):
    config_file = "fixtures/freq_test.conf"
    options = Box({
            "vcf": None,
            "direct": True,
            "mode": "replace",
        },
        default_box=True,
        default_box_attr=None)

    filename = relative_to_this_test_folder(config_file)

    captured = capsys.readouterr()
    with variants_io("fixtures/frequencies_test_small.tsv") as io_manager:
        pipeline = PipelineAnnotator.build(
            options, filename, io_manager.reader.schema,
            defaults={
                "fixtures_dir": relative_to_this_test_folder("fixtures/")
            })
        assert pipeline is not None
        pipeline.annotate_file(io_manager)
    captured = capsys.readouterr()

    print(captured.err)
    print(captured.out)
