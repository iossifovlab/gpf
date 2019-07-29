from box import Box

from annotation.tools.cleanup_annotator import CleanupAnnotator
from annotation.tools.annotator_config import AnnotatorConfig

expected_cleanup_output = """location
4:4372372973
10:4372372973
X:4372
Y:4372
"""


def test_cleanup_annotator(capsys, variants_io):
    opts = Box({}, default_box=True, default_box_attr=None)

    section_config = AnnotatorConfig(
        name="cleanup",
        annotator_name="cleanup_annotator.CleanupAnnotator",
        options=opts,
        columns_config={
            "cleanup": "id, variant",
        },
        virtuals=[]
    )

    with variants_io('fixtures/input.tsv') as io_manager:
        annotator = CleanupAnnotator(section_config)
        assert annotator is not None
        capsys.readouterr()
        annotator.annotate_file(io_manager)

    captured = capsys.readouterr()

    print(captured.out)
    print(captured.err)
    assert captured.out == expected_cleanup_output
