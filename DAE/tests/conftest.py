import os
import pytest
import shutil
import tempfile

from box import Box

from annotation.annotation_pipeline import PipelineAnnotator


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture
def temp_dirname(request):
    dirname = tempfile.mkdtemp(suffix='_data', prefix='variants_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname


@pytest.fixture(scope='session')
def annotation_pipeline():
    filename = relative_to_this_test_folder(
        "fixtures/annotation_pipeline/import_annotation.conf")

    options = Box({
            "default_arguments": None,
            "vcf": True,
            # "mode": "overwrite",
        },
        default_box=True,
        default_box_attr=None)

    pipeline = PipelineAnnotator.build(
        options, filename,
        defaults={
            "fixtures_dir": relative_to_this_test_folder(
                "fixtures/annotation_pipeline/")
        })
    return pipeline
