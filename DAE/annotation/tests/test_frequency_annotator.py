from __future__ import print_function

import pandas as pd

from box import Box

from .conftest import relative_to_this_test_folder
# from annotation.annotation_pipeline import PipelineAnnotator
from annotation.tools.frequency_annotator import FrequencyAnnotator
from annotation.tools.annotator_config import VariantAnnotatorConfig


# def test_simple(capsys, variants_io):
#     config_file = "fixtures/freq_test.conf"
#     options = Box({
#             "vcf": None,
#             "direct": True,
#             "mode": "replace",
#         },
#         default_box=True,
#         default_box_attr=None)

#     filename = relative_to_this_test_folder(config_file)

#     captured = capsys.readouterr()
#     with variants_io("fixtures/frequencies_test_small.tsv") as io_manager:
#         pipeline = PipelineAnnotator.build(
#             options, filename, io_manager.reader.schema,
#             defaults={
#                 "fixtures_dir": relative_to_this_test_folder("fixtures/")
#             })
#         assert pipeline is not None
#         pipeline.annotate_file(io_manager)
#     captured = capsys.readouterr()

#     print(captured.err)
#     print(captured.out)


exptected_result_freq = \
    """RESULT_FREQ
0.1
0.5
0.7
"""


def test_frequency_annotator(mocker, variants_io, expected_df, capsys):

    genome = mocker.Mock()
    genome.getSequence = lambda _, start, end: 'A' * (end - start + 1)

    with mocker.patch('GenomeAccess.openRef') as genome_mock:
        genome_mock.return_value = genome

        options = Box({
            "vcf": True,
            "Graw": "fake_genome_ref_file",
            "direct": False,
            "freq_file": relative_to_this_test_folder(
                "fixtures/TESTFreq/test_freq.tsv.gz"),
            "freq": "all.altFreq",
            # "c": "CSHL:chr",
            # "p": "CSHL:position",
            # "v": "CSHL:variant",
        }, default_box=True, default_box_attr=None)

        columns_config = {
            'freq': "RESULT_FREQ",
        }

        config = VariantAnnotatorConfig(
            name="test_annotator",
            annotator_name="frequency_annotator.FrequencyAnnotator",
            options=options,
            columns_config=columns_config,
            virtuals=[]
        )

        with variants_io("fixtures/freq_test_1.tsv") as io_manager:
            freq_annotator = FrequencyAnnotator(config)
            assert freq_annotator is not None

            captured = capsys.readouterr()

            freq_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)

    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(exptected_result_freq),
        check_less_precise=3)
