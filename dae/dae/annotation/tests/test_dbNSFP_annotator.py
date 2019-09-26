import pandas as pd
from box import Box

from .conftest import relative_to_this_test_folder
from dae.annotation.tools.dbnsfp_annotator import dbNSFPAnnotator
from dae.annotation.tools.annotator_config import AnnotationConfigParser

expected_result_dbNSFP = \
    '''RESULT_dbNSFP\tRESULT_dbNSFP_2
0.5\t1.5
0.65\t1.65
15.5\t16.5
15.75\t16.75
22.5\t23.5
22.65\t23.65
23.5\t24.5
23.8\t24.8
'''


def test_dbNSFP_annotator(variants_io, expected_df, capsys, mocked_genomes_db):
    options = Box({
        'vcf': True,
        'direct': False,
        'mode': 'overwrite',
        'dbNSFP_path': relative_to_this_test_folder(
            'fixtures/TESTdbNSFP/'),
        'dbNSFP_filename': 'test_missense_chr*.tsv.gz',
        'dbNSFP_config': 'test_missense_config.conf'
    }, default_box=True, default_box_attr=None)

    columns = {
        'score': 'RESULT_dbNSFP',
        'score2': 'RESULT_dbNSFP_2'
    }

    config = AnnotationConfigParser.parse_section(
        Box({
            'options': options,
            'columns': columns,
            'annotator': 'dbNSFP_annotator.dbNSFPAnnotator'
        }),
        mocked_genomes_db
    )

    with variants_io('fixtures/multi_chrom_input.tsv') as io_manager:
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
