import pandas as pd

from .conftest import relative_to_this_test_folder
from dae.annotation.tools.frequency_annotator import FrequencyAnnotator
from dae.annotation.tools.annotator_config import AnnotationConfigParser


expected_warnings = (
    "WARNING test_freq.tsv.gz: "
    "multiple variant occurrences of 1:20002 sub(C->A)\n"
)


expected_result_freq = """RESULT_FREQ\tRESULT_FREQ_2
0.1\t0.8
0.5\t1.2
\t
0.7\t1.4
"""


def test_frequency_annotator(
        variants_io, expected_df, capsys, genomes_db_2013):

    options = {
        "vcf": True,
        "direct": False,
        "mode": "overwrite",
        "scores_file": relative_to_this_test_folder(
            "fixtures/TESTFreq/test_freq.tsv.gz"
        ),
    }

    columns = {"all_altFreq": "RESULT_FREQ", "all_altFreq2": "RESULT_FREQ_2"}

    config = AnnotationConfigParser.parse_section({
            "options": options,
            "columns": columns,
            "annotator": "frequency_annotator.FrequencyAnnotator",
            "virtual_columns": [],
        }
    )

    with variants_io("fixtures/freq_test_1.tsv") as io_manager:
        freq_annotator = FrequencyAnnotator(config, genomes_db_2013)
        assert freq_annotator is not None

        captured = capsys.readouterr()

        freq_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)

    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected_result_freq),
        rtol=10e-3)

    print(captured.err)

    # assert captured.err == expected_warnings
