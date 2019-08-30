import pandas as pd

from box import Box

from .conftest import relative_to_this_test_folder
from dae.annotation.tools.frequency_annotator import FrequencyAnnotator
from dae.annotation.tools.annotator_config import AnnotationConfigParser


expected_warnings = \
    "WARNING test_freq.tsv.gz: " \
    "multiple variant occurrences of 1:20002 sub(C->A)\n"


expected_result_freq = \
    """RESULT_FREQ\tRESULT_FREQ_2
0.1\t0.8
0.5\t1.2
\t
0.7\t1.4
"""


def test_frequency_annotator(mocker, variants_io, expected_df, capsys):

    genome = mocker.Mock()
    genome.getSequence = lambda _, start, end: 'A' * (end - start + 1)

    with mocker.patch('dae.GenomeAccess.openRef') as genome_mock:
        genome_mock.return_value = genome

        options = Box({
            "vcf": True,
            "Graw": "fake_genome_ref_file",
            "direct": False,
            "mode": "overwrite",
            "scores_file": relative_to_this_test_folder(
                    "fixtures/TESTFreq/test_freq.tsv.gz")
        }, default_box=True, default_box_attr=None)

        columns = {
            'all_altFreq': 'RESULT_FREQ',
            'all_altFreq2': 'RESULT_FREQ_2'
        }

        config = AnnotationConfigParser.parse_section(
            Box({
                'options': options,
                'columns': columns,
                'annotator': 'frequency_annotator.FrequencyAnnotator'
            })
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
        expected_df(expected_result_freq),
        check_less_precise=3)

    assert captured.err == expected_warnings
