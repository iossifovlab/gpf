from __future__ import print_function

import pandas as pd
from box import Box

from .conftest import relative_to_this_test_folder
from annotation.tools.dbnsfp_annotator import dbNSFPAnnotator
from annotation.tools.annotator_config import VariantAnnotatorConfig

expected_result_dbNSFP = \
    """RESULT_dbNSFP
0.5
0.6
0.7
0.8
0.9
1.0
1.5
1.6
1.7
1.8
1.9
2.0
15.5
15.6
15.7
15.8
15.9
16.0
22.5
22.6
22.7
22.8
22.9
23.0
23.5
23.6
23.7
23.8
23.9
24.0
"""


def test_dbNSFP_annotator(mocker, variants_io, expected_df, capsys):

    genome = mocker.Mock()
    genome.getSequence = lambda _, start, end: 'A' * (end - start + 1)

    with mocker.patch('GenomeAccess.openRef') as genome_mock:
        genome_mock.return_value = genome

        options = Box({
            "vcf": False,
            "Graw": "fake_genome_ref_file",
            "direct": False,
            "mode": "overwrite",
            "dbNSFP_path": relative_to_this_test_folder(
                "fixtures/TESTdbNSFP/"),
            "dbNSFP_filename": "test_missense_chr{}.tsv.gz",
            "dbNSFP_config": "test_missense_config.conf"
        }, default_box=True, default_box_attr=None)

        columns_config = {
            'score': "RESULT_dbNSFP",
        }

        config = VariantAnnotatorConfig(
            name="test_annotator",
            annotator_name="dbNSFP_annotator.dbNSFPAnnotator",
            options=options,
            columns_config=columns_config,
            virtuals=[]
        )

        with variants_io("fixtures/multi_chrom_input.tsv") as io_manager:
            dbNSFP_annotator = dbNSFPAnnotator(config)
            assert dbNSFP_annotator is not None

            captured = capsys.readouterr()

            dbNSFP_annotator.annotate_file(io_manager)

    captured = capsys.readouterr()
    print(captured.err)
    print(captured.out)

    pd.testing.assert_frame_equal(
        expected_df(captured.out),
        expected_df(expected_result_dbNSFP),
        check_less_precise=3)
