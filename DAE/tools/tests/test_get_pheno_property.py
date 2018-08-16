import pytest
import pandas as pd
from get_pheno_property import parse_cli_arguments
from query_pheno_data import query_data, get_phenodb_names, \
                             GENERIC_PHENO_DATA_COLUMNS

def list2df(l):
    return pd.DataFrame(l[1:], columns=l[0])

def is_sublist_in_list(sublist, full_list):
    return not [x for x in sublist if x not in full_list]

def case2query(d, parser):
    list_d = [['--'+column_name2property[k], ','.join(v)] for k,v in d.items()]
    return [parser] + [x for sublist in list_d for x in sublist]


def query_df(args):
    args_dict = parse_cli_arguments(args)
    generator = query_data(args_dict)
    return list2df([l for l in generator])

def assert_header(cols, header):
    assert list(cols) == header

def assert_query_not_empty(query):
    assert not query.empty

def assert_empty_result(query, header):
    assert_header(query.columns, header)
    assert query.empty

def assert_correct_column_values(query, expected):
    for col_name,values in expected.items():
        assert set(query[col_name].values) == set(values)

def assert_correct_non_column_atts(query, expected):
    result_measures = list(query.columns)[6:]
    if 'MeasureId' in expected:
        assert is_sublist_in_list(result_measures, expected['MeasureId'])
        del expected['MeasureId']

    if 'Instrument' in expected:
        result_instruments = [m.split('.')[0]
                            for m in result_measures] #theoretically true
        assert is_sublist_in_list(result_instruments, expected['Instrument'])
        del expected['Instrument']

    if 'Type' in expected:
        expected_measures = query_df(['measures', '--measureTypes',
                            ','.join(expected['Type'])]).MeasureId.values
        assert is_sublist_in_list(result_measures, expected_measures)
        del expected['Type']


'''
DBS PARSER
all
'''
def test_dbs_all():
    q = query_df(['dbs'])
    assert_header(q.columns, HEADER_D)
    assert all(q[HEADER_D[0]].values == get_phenodb_names())

'''
INSTRUMENTS PARSER
options: all, phenodbs
'''
def perform_instruments_asserts(q, expected_dbs):
    assert_header(q.columns, HEADER_I)
    assert_query_not_empty(q)
    assert_correct_column_values(q, {'Db':expected_dbs})


def test_instruments_all():
    q = query_df(['instruments'])
    perform_instruments_asserts(q, get_phenodb_names())

def test_instruments_filtered_by_dbs(instrument_dbs_cases):
    q = query_df(['instruments', '--phenodbs', instrument_dbs_cases])
    perform_instruments_asserts(q, instrument_dbs_cases.split(','))

def test_instruments_with_incorrect_dbs(instrument_incorrect_dbs_cases):
    q = query_df(['instruments', '--phenodbs', instrument_incorrect_dbs_cases])
    assert_empty_result(q, HEADER_I)

def test_instruments_with_partially_incorrect_dbs_input(
        instrument_partially_incorrect_input_dbs_cases):
    q = query_df(['instruments', '--phenodbs',
        instrument_partially_incorrect_input_dbs_cases['input']])
    perform_instruments_asserts(q,
        instrument_partially_incorrect_input_dbs_cases['expected'].split(','))

'''
MEASURES PARSER
options: all, phenodbs, measureIds, instrumentIds, measureTypes
columns: Db, Measure, Instrument, Type
'''
def perform_measures_asserts(q, expected, type=None):
    assert_header(q.columns, HEADER_M)
    assert_query_not_empty(q)
    assert_correct_column_values(q,expected)

def measure_query(param):
    return query_df(case2query(param, 'measures'))


def test_measures_all():
    q = query_df(['measures'])
    perform_measures_asserts(q, {'Db' : get_phenodb_names()})

def test_measures_simple_input(measures_simple_cases):
    query, expected = measures_simple_cases
    perform_measures_asserts(query, expected)

def test_measures_complex_input(measures_complex_cases):
    query, expected = measures_complex_cases
    perform_measures_asserts(query, expected)

def test_measures_filtered_until_empty_input(measures_filtered_until_empty_cases):
    assert_empty_result(measures_filtered_until_empty_cases, HEADER_M)

def test_measures_incorrect_input(measures_incorrect_input_cases):
    assert_empty_result(measures_incorrect_input_cases, HEADER_M)

def test_measures_partially_incorrect_input_cases(measures_partially_incorrect_input_cases):
    query, expected = measures_partially_incorrect_input_cases
    perform_measures_asserts(query, expected)

'''
PEOPLE PARSER
options: db, person_id/file, family_id/file,
            role, gender, status, measureIds, instrumentIds, measureTypes
columns: Db, person_id, family_id, gender, status, m1, m2 ... mN
'''
def perform_people_asserts(q, expected, type=None):
    assert_query_not_empty(q)
    assert_correct_non_column_atts(q, expected)
    assert_correct_column_values(q, expected)

def people_query(param):
    return query_df(case2query(param, 'people'))

def test_people_all():
    q = query_df(['people', '--measureIds',
        'individuals.age_at_registration_years,ADOS31.UEYE,bapq.status,med_child.inf_eryt_cu'])
    perform_people_asserts(q, {'Db' : get_phenodb_names()})

@pytest.mark.skip(reason="too heavy")
def test_people_simple_input(people_simple_cases):
    q, expected = people_simple_cases[0], people_simple_cases[1]
    perform_people_asserts(q, expected)

def test_people_complex_input(people_complex_cases):
    q, expected = people_complex_cases[0], people_complex_cases[1]
    perform_people_asserts(q, expected)

def test_people_partially_incorrect_input(people_partially_incorrect_input_cases):
    q, expected = people_partially_incorrect_input_cases[0], \
                 people_partially_incorrect_input_cases[1]
    perform_people_asserts(q, expected)

def test_people_incorrect_input(people_incorrect_input_cases):
    assert set(HEADER_P).issubset(people_incorrect_input_cases.columns)
    assert people_incorrect_input_cases.empty

def test_people_filter_until_empty(people_filter_until_empty_cases):
    assert set(HEADER_P).issubset(people_filter_until_empty_cases.columns)
    assert people_filter_until_empty_cases.empty

def test_people_file_input(people_file_input_cases):
    q, expected = people_file_input_cases[0], people_file_input_cases[1]
    perform_people_asserts(q, expected)


column_name2property = {#measures
                        'Db' : 'phenodbs',
                        'Instrument' : 'instrumentIds',
                        'Type' : 'measureTypes',
                        'MeasureId' : 'measureId',
                        #people
                        'role' : 'roles',
                        'gender' : 'gender',
                        'status' : 'status',
                        'person_id' : 'personIds',
                        'family_id' : 'familyIds',
                        #not present in column names
                        'personIdsFile' : 'personIdsFile',
                        'familyIdsFile' : 'familyIdsFile'}

HEADER_D = GENERIC_PHENO_DATA_COLUMNS['listDatabases']
HEADER_I = GENERIC_PHENO_DATA_COLUMNS['listInstruments']
HEADER_M = GENERIC_PHENO_DATA_COLUMNS['listMeasures']
HEADER_P = GENERIC_PHENO_DATA_COLUMNS['listPeople']
