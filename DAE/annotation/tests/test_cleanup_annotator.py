from __future__ import print_function
import pytest

from box import Box

from annotation.tools.cleanup_annotator import CleanupAnnotator
from annotation.tools.annotator_config import AnnotatorConfig

expected_cleanup_output = """location
4:4372372973
10:4372372973
X:4372
Y:4372
"""


class SoftCleanupAnnotatorTester(CleanupAnnotator):

    def __init__(self, config):
        super(SoftCleanupAnnotatorTester, self).__init__(config)

    def line_annotation(self, annotation_line):
        super(SoftCleanupAnnotatorTester, self) \
                .line_annotation(annotation_line)
        if not self.config.options.hard:
            for column in self.cleanup_columns:
                assert column in annotation_line


@pytest.mark.parametrize('hard', [(True), (False)])
def test_cleanup_annotator(capsys, variants_io, hard):
    opts = Box({'hard': hard}, default_box=True, default_box_attr=None)

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
        annotator = SoftCleanupAnnotatorTester(section_config)
        assert annotator is not None
        capsys.readouterr()
        annotator.annotate_file(io_manager)

    captured = capsys.readouterr()

    print(captured.out)
    print(captured.err)
    assert captured.out == expected_cleanup_output
