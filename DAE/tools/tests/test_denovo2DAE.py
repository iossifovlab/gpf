import os
import pytest
from denovo2DAE import denovo2DAE, parse_cli_arguments


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


def test_incorrect_filepaths():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        denovo2DAE(parse_cli_arguments(['wrong_v', 'wrong_f']))
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


def test_file_output(dae_file, dae_with_columns):
    cmp_file_df(dae_file, dae_with_columns)
    os.remove(dae_file)


def test_xlsx_format_variants(dae_xlsx):
    assert all(dae_xlsx.columns.values == HEADER)
    assert len(dae_xlsx) == 14
    assert all(dae_xlsx.familyId.values == '1-0004-003')
    assert all(dae_xlsx.sampleIds.values == '1-0004-003')
    assert all(dae_xlsx.bestState.values == '2 2 1 2/0 0 1 0')
    assert all(dae_xlsx.inChild.values == 'prbF')


def test_zero_based_variants(dae_zero_based):
    wo, w = dae_zero_based
    assert all([x+1 == y for x, y in zip(wo.pos.values, w.pos.values)])


def test_different_column_names(dae_with_columns):
    assert all(dae_with_columns.columns.values == HEADER)


def test_wrong_columns(dae_without_columns_error):
    with pytest.raises(AssertionError):
        denovo2DAE(dae_without_columns_error)


def test_output(dae):
    cmp_file_df(path('dnv2dae/l-res.tsv'), dae)
