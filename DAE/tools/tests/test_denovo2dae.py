import os
import pytest
import pandas as pd
from tools.denovo2dae import denovo2DAE, parse_cli_arguments

pytestmark = pytest.mark.skip


HEADER = ['familyId', 'chr', 'pos', 'ref', 'alt',
          'bestState', 'inChild', 'sampleIds']


def path(s):
    p = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(p, s)


def form_line(l):
    return '\t'.join(map(str, l)) + '\n'


def cmp_file_df(f_path, df):
    f = open(f_path, 'r')
    assert f.readline() == form_line(HEADER)
    for _, row in df.iterrows():
        assert f.readline() == form_line(row)
    f.close()


def assert_system_exit(args):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        denovo2DAE(parse_cli_arguments(args))
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


def test_exporting_dae(dae_file, dae):
    cmp_file_df(dae_file, dae)


def test_variants_formats(dae_tsv, dae_csv, dae_xlsx):
    pd.testing.assert_frame_equal(dae_csv, dae_xlsx)
    pd.testing.assert_frame_equal(dae_csv, dae_tsv)


def test_with_column_names(dae_with_columns):
    assert all(dae_with_columns.columns.values == HEADER)


def test_with_wrong_columns_names():
    args = [path('dnv2dae/vs.tsv'), path('dnv2dae/fs.ped'), '-si=Wrong']
    assert_system_exit(args)


def test_incorrect_filepaths():
    assert_system_exit(['wrong_v', 'wrong_f'])


def test_zero_based_variants(dae_zero_based):
    wo, w = dae_zero_based
    assert all([x+1 == y for x, y in zip(wo.pos.values, w.pos.values)])


def test_generate_family_ids(dae, dae_ids):
    pd.testing.assert_frame_equal(dae, dae_ids)


def test_with_missing_sample(dae):
    cmp_file_df(path('dnv2dae/res.tsv'), dae)


def test_force(dae, dae_force):
    missing_samples = {'alt': 'T',
                       'bestState': '1/1',
                       'chr': '6',
                       'familyId': '6',
                       'inChild': 'prbU',
                       'pos': 234735100,
                       'ref': 'C',
                       'sampleIds': '6'}
    dae_appended = dae.append(missing_samples, ignore_index=True)
    assert dae_appended.to_dict('records') == dae_force.to_dict('records')
