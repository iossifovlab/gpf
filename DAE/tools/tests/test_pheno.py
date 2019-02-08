import os
import itertools
import pytest

# from DAE import pheno
# from tools.get_pheno_property import parse_cli_arguments, query_data
# from fixtures.pheno_data import M, DB, DBS, DBS_HEADER, INSTRUMENTS_HEADER, \
#                                 MEASURES_HEADER, MEASURE_ROWS, \
#                                 get_people, get_people_filtered


# def assert_header(result, header):
#     assert result.pop(0) == header


# def assert_rows_ordered(result, expected):
#     assert all([result_row == expected_row for result_row, expected_row
#                 in zip(result, expected)])


# def assert_rows(result, expected):
#     assert len(result) == len(expected)
#     assert set([str(line) for line in expected]) == \
#         set([str(line) for line in result])


# def assert_phenodbs_required_arg(parser, mocker):
#     with pytest.raises(SystemExit) as wrapped_exception:
#         query_data(parse_cli_arguments([parser, 'Incorrect DB']))
#     assert wrapped_exception.type == SystemExit
#     assert wrapped_exception.value.code == 1


# def test_phenodbs_required_arg(mocker):
#     assert_phenodbs_required_arg('instruments', mocker)
#     assert_phenodbs_required_arg('measures', mocker)
#     assert_phenodbs_required_arg('people', mocker)


# def form_query(args):
#     args_dict = parse_cli_arguments(args)
#     return query_data(args_dict)


# # DBS PARSER
# # columns: Pheno DB names
# def test_dbs(mocker):
#     mocker.patch.object(pheno, 'get_pheno_db_names')
#     pheno.get_pheno_db_names.return_value = DBS

#     query = form_query(['dbs'])

#     pheno.get_pheno_db_names.assert_called_once()
#     assert_header(query, DBS_HEADER)
#     assert_rows_ordered(itertools.chain(*query), DBS)


# # INSTRUMENTS PARSER
# # columns: Db, Instrument
# # options: phenodbs
# def perform_asserts(query, expected, header):
#     pheno.get_pheno_db.assert_called_with(DB)
#     assert_header(query, header)
#     assert_rows(query, expected)


# def test_instruments(db):
#     query = form_query(['instruments', DB])
#     expected = [[DB, 'i1'], [DB, 'i2'], [DB, 'i3']]
#     perform_asserts(query, expected, INSTRUMENTS_HEADER)


# # MEASURES PARSER
# # columns: Db, MeasureId, Measure, Instrument, Type, Min, Max
# # options: phenodbs, measureIds, instrumentIds, measureTypes
# def test_measures(db):
#     query = form_query(['measures', DB])
#     perform_asserts(query, MEASURE_ROWS.values(), MEASURES_HEADER)


# def test_measures_ids(db, measure_ids_filter):
#     args = ['measures', DB, '--measureIds=' + measure_ids_filter]
#     expected = [MEASURE_ROWS[m_id] for m_id in measure_ids_filter.split(',')]
#     perform_asserts(form_query(args), expected, MEASURES_HEADER)


# def test_measures_types(db, measure_types_filter):
#     types, measure_ids = measure_types_filter
#     args = ['measures', DB, '--measureTypes=' + types]
#     expected = [MEASURE_ROWS[m_id] for m_id in measure_ids]
#     perform_asserts(form_query(args), expected, MEASURES_HEADER)


# def test_measures_intrument_ids(db, instrument_ids_filter):
#     instrument_ids, measure_ids = instrument_ids_filter
#     args = ['measures', DB, '--instrumentIds=' + instrument_ids]
#     expected = [MEASURE_ROWS[m_id] for m_id in measure_ids]
#     perform_asserts(form_query(args), expected, MEASURES_HEADER)


# def test_measures_complex_input(db, complex_measures_filter):
#     filters, measure_ids = complex_measures_filter
#     args = ['measures', DB] + filters
#     expected = [MEASURE_ROWS[m_id] for m_id in measure_ids]
#     perform_asserts(form_query(args), expected, MEASURES_HEADER)


# # PEOPLE PARSER
# # columns: Db, person_id, family_id, gender, status, m1, m2 ... mN
# # options: db, person_id/file, family_id/file, role,
# #          gender, status, measureIds, instrumentIds, measureTypes
# def df2list(df):
#     return map(lambda r: [DB, r[0], r[1], r[2].name, r[3].name, r[4].name]
#                + [str(x) for x in r[5:]], df.values)


# def perform_people_asserts(
#         measure_ids, args, roles=None, family_ids=None, person_ids=None):
#     people = get_people(measure_ids)
#     pheno.get_pheno_db(DB).get_persons_values_df.return_value = people
#     query = form_query(args)

#     assert_header(query, ['Db'] + list(people.columns))
#     assert_rows_ordered(query, df2list(people))

#     pheno.get_pheno_db(DB).get_persons_values_df.assert_called_once_with(
#         measure_ids.split(','),
#         family_ids=family_ids, person_ids=person_ids, roles=roles)


# def test_people_measure_ids(db, measure_ids_filter):
#     args = ['people', DB, '--measureIds=' + measure_ids_filter]
#     perform_people_asserts(measure_ids_filter, args)


# def test_people_role(db):
#     args = ['people', DB, '--measureIds=' + M, '--roles=prb']
#     perform_people_asserts(M, args, roles=['prb'])


# def test_people_person_ids(db):
#     args = ['people', DB, '--measureIds=' + M, '--personIds=SF0033601']
#     perform_people_asserts(M, args, person_ids=['SF0033601'])


# def test_people_family_ids(db):
#     args = ['people', DB, '--measureIds=' + M, '--familyIds=SF0033601']
#     perform_people_asserts(M, args, family_ids=['SF0033601'])


# def path(s):
#     p = os.path.dirname(os.path.abspath(__file__))
#     return os.path.join(p, s)


# def test_people_person_ids_file(db):
#     args = ['people', DB, '--measureIds=' + M, '--personIdsFile=' +
#             path('fixtures/person-ids.txt')]
#     perform_people_asserts(M, args, person_ids=['SF0033601'])


# def test_people_family_ids_file(db):
#     args = ['people', DB, '--measureIds=' + M, '--familyIdsFile=' +
#             path('fixtures/family-ids.txt')]
#     perform_people_asserts(M, args, family_ids=['SF0033601'])


# def test_people_gender(db):
#     people = get_people(M)
#     pheno.get_pheno_db(DB).get_persons_values_df.return_value = people
#     query = form_query(['people', DB, '--measureIds='+M, '--status=affected'])
#     assert_header(query, ['Db'] + list(people.columns))
#     assert_rows_ordered(query, df2list(get_people_filtered(M)))


# def test_people_status(db):
#     people = get_people(M)
#     pheno.get_pheno_db(DB).get_persons_values_df.return_value = people
#     query = form_query(['people', DB, '--measureIds=' + M, '--gender=F'])
#     assert_header(query, ['Db'] + list(people.columns))
#     assert_rows_ordered(query, df2list(get_people_filtered(M)))


# def test_people_instrument_ids(db):
#     args = ['people', DB, '--measureIds=' + M, '--instrumentIds=i1']
#     pheno.get_pheno_db(DB).get_measures.return_value = [M]
#     perform_people_asserts(M, args)
#     pheno.get_pheno_db(DB).get_measures.assert_called_once_with('i1', None)


# def test_people_measure_types(db):
#     args = ['people', DB, '--measureIds=' + M, '--measureTypes=ordinal']
#     pheno.get_pheno_db(DB).get_measures.return_value = [M]
#     perform_people_asserts(M, args)
#     pheno.get_pheno_db(DB).get_measures \
#          .assert_called_once_with(None, 'ordinal')


# def test_people_complex_input(db):
#     args = ['people', DB, '--measureIds=' + M, '--measureTypes=ordinal',
#             '--instrumentIds=i1']
#     pheno.get_pheno_db(DB).get_measures.return_value = [M]
#     perform_people_asserts(M, args)
#     pheno.get_pheno_db(DB).get_measures \
#          .assert_called_once_with('i1', 'ordinal')
