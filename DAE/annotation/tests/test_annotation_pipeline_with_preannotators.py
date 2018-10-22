import pytest
from annotation.obsolete.annotation_pipeline import MultiAnnotator
from .test_annotation_pipeline import DummyIOAdapter, input_base, \
    options_preannotate


pytestmark = pytest.mark.skip


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch('os.path.exists',
                 return_value=True)


def test_annotators_tsv_with_preannotators():
    io = DummyIOAdapter(input_base())
    options = options_preannotate()
    annotator = MultiAnnotator(options, header=['id', 'location', 'variant'])
    annotator.annotate_file(io)
    assert io.output is not None
    print(io.output)
