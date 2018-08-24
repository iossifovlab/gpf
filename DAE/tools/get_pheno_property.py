#!/usr/bin/env python
from __future__ import print_function
from itertools import combinations
import argparse
import sys
from DAE import pheno
from query_variants import join_line


def query_phenodbs(data):
    data.append(GENERIC_PHENO_DATA_COLUMNS['listDatabases'])
    for name in get_phenodb_names():
        data.append([name])


def query_instruments(data, db_name):
    data.append(GENERIC_PHENO_DATA_COLUMNS['listInstruments'])
    db = pheno.get_pheno_db(db_name)
    data += [[db_name, k] for k in db.instruments]


def in_options(value, container):
    if not container:
        return True
    else:
        return value in container


def query_measures(data, filters):
    data.append(GENERIC_PHENO_DATA_COLUMNS['listMeasures'])
    db_name = filters['phenodbs']
    db = pheno.get_pheno_db(db_name)
    data += [[db_name, m.measure_id, m.name,
              m.instrument_name, m.measure_type.name,
              str(m.min_value), str(m.max_value)]
             for m in db.measures.values()
             if in_options(m.instrument_name, filters['instrumentIds'])
             and in_options(m.measure_type.name, filters['measureTypes'])
             and in_options(m.measure_id, filters['measureIds'])]


def measure_values(row, m_names):
    return [str(row[name]) for name in m_names]


def clean_list(arr, all_set):
    if not arr:
        return None
    return [x for x in list(set(arr)) if x in all_set]


def filter_measure_ids(ins, types, db):
    if ins is None and types is None:
        return None
    if ins == [] or types == []:
        return []

    if not ins:
        ins = [None]
    if not types:
        types = [None]
    it_measure_ids = []

    filters = [f for f in combinations(ins + types, 2)
               if f[0] in ins and f[1] in types]
    for i, t in filters:
        it_measure_ids += db.get_measures(i, t)
    return it_measure_ids


def query_people(data, options):
    data.append(list(GENERIC_PHENO_DATA_COLUMNS['listPeople']))
    db_name = options['phenodbs']
    db = pheno.get_pheno_db(db_name)

    measure_ids = clean_list(options['measureIds'], db.measures)
    instrument_ids = clean_list(options['instrumentIds'], db.instruments)
    measure_types = clean_list(options['measureTypes'], MEASURE_TYPES)

    it_measure_ids = filter_measure_ids(instrument_ids, measure_types, db)
    if it_measure_ids is not None and measure_ids is not None:
        measure_ids = list(set(measure_ids) & set(it_measure_ids))
    if not measure_ids:
        return

    df = db.get_persons_values_df(
        measure_ids, roles=options['roles'],
        person_ids=options['personIds'], family_ids=options['familyIds'])
    measure_columns = list(df.columns)[5:]
    data[0] += measure_columns
    data += [[db_name, row.person_id, row.family_id,
              row.role.name, row.gender.name, row.status.name]
             + measure_values(row, measure_columns)
             for _, row in df.iterrows()
             if in_options(row.gender.name, options['gender'])
             and in_options(row.status.name, options['status'])]


def __load_text_column(files, sep=','):
    res = []
    for f_name in files.split(','):
        f = open(f_name)
        for l in f:
            cs = l.split()
            if sep in cs:
                cs = [x.split() for x in cs]
                cs = [x in l in cs for x in l]
            res += cs
        f.close()
    return ','.join(res)


def add_file_arg(arg, options):
    file_arg = arg + 'File'
    if file_arg in options and options[file_arg]:
        if not options[arg]:
            options[arg] = []
        options[arg] += options[file_arg]


def include_file_arguments(options):
    add_file_arg('familyIds', options)
    add_file_arg('personIds', options)


def get_phenodb_names():
    return pheno.get_pheno_db_names()


def prepare_filter(options, arg):
    if arg not in options or options[arg] is None:
        return None
    if 'File' in arg:
        return __load_text_column(options[arg]).split(',')
    return options[arg].split(',')


def get_parser_name(options):
    if len(options) == 0:
        return 'dbs'
    elif len(options) == 1:
        return 'instruments'
    elif len(options) == 4:
        return 'measures'
    return 'people'


def prepare_dbs(options):
    if 'phenodbs' not in options:
        return
    dbs = options['phenodbs']

    if len(dbs) != 1:
        print('ERROR: Only one phenodb argument is supported', file=sys.stderr)
        sys.exit(1)
    if dbs[0] not in get_phenodb_names():
        print('ERROR: Incorrect pheno db name: ' + dbs[0], file=sys.stderr)
        sys.exit(1)

    options['phenodbs'] = dbs[0]


def prepare_people_measure_ids(options):
    if options['parser'] != 'people':
        return
    measures = pheno.get_pheno_db(options['phenodbs']).measures.keys()
    if not options['measureIds']:
        options['measureIds'] = measures
    else:
        options['measureIds'] = clean_list(options['measureIds'], measures)


def prepare_options(options):
    prepared_options = {'parser': get_parser_name(options)}
    prepared_options.update({k: prepare_filter(options, k)
                             for k, v in options.items()})
    prepare_dbs(prepared_options)
    prepare_people_measure_ids(prepared_options)
    include_file_arguments(prepared_options)

    return prepared_options


def query_data(options):
    filters = prepare_options(options)
    data = []

    if filters['parser'] == 'dbs':
        query_phenodbs(data)
    if filters['parser'] == 'instruments':
        query_instruments(data, filters['phenodbs'])
    if filters['parser'] == 'measures':
        query_measures(data, filters)
    if filters['parser'] == 'people':
        query_people(data, filters)

    return data


GENERIC_PHENO_DATA_COLUMNS = {
    'listDatabases': ['Pheno DB names'],
    'listInstruments': ['Db', 'Instrument'],
    'listMeasures': ['Db',
                     'MeasureId',
                     'Measure',
                     'Instrument',
                     'Type',
                     'Min',
                     'Max'],
    'listPeople': ['Db', 'person_id', 'family_id', 'role', 'gender', 'status']
}
MEASURE_TYPES = ['continuous', 'ordinal', 'categorical', 'unknown']


def create_dbs_parser(subparsers):
    subparsers.add_parser(
        'dbs',
        help='executes commands in relation to pheno databases.')


def create_instruments_parser(subparsers):
    instruments_parser = subparsers.add_parser(
        'instruments',
        help='queries instruments  according to the given filters')

    instruments_parser.add_argument(
        'phenodbs', type=str,
        default=None,
        help='pheno dbs (i.e. spark, agre, vip)'
    )


def create_measures_parser(subparsers):
    measures_parser = subparsers.add_parser(
        'measures',
        help='queries measures according to the given filters')

    measures_parser.add_argument(
        'phenodbs', type=str,
        default=None,
        help='pheno dbs (i.e. spark, agre, vip)'
    )
    measures_parser.add_argument(
        '--instrumentIds', type=str,
        default=None,
        help='instrument IDs'
    )
    measures_parser.add_argument(
        '--measureIds', type=str,
        default=None,
        help='measure IDs'
    )
    measures_parser.add_argument(
        '--measureTypes', type=str,
        default=None,
        help='measure types. One of the following: ' + ', '.join(MEASURE_TYPES)
    )


def create_people_parser(subparsers):
    people_parser = subparsers.add_parser(
        'people',
        help='queries people according to the given filters')

    people_parser.add_argument(
        'phenodbs', type=str,
        default=None,
        help='pheno dbs (i.e. spark, agre, vip)'
    )
    people_parser.add_argument(
        '--measureIds', type=str,
        default=None,
        help='measure IDs'
    )
    people_parser.add_argument(
        '--instrumentIds', type=str,
        default=None,
        help='instrument IDs'
    )
    people_parser.add_argument(
        '--familyIds', type=str,
        default=None,
        help='family IDs'
    )
    people_parser.add_argument(
        '--familyIdsFile', type=str,
        default=None,
        help='file containing family IDs'
    )
    people_parser.add_argument(
        '--personIds', type=str,
        default=None,
        help='person IDs'
    )
    people_parser.add_argument(
        '--personIdsFile', type=str,
        default=None,
        help='file containing person IDs'
    )
    people_parser.add_argument(
        '--roles', type=str,
        default=None,
        help='roles in family (i.e. prb, sib, mom, dad)'
    )
    people_parser.add_argument(
        '--gender', type=str,
        default=None,
        help='person\'s gender. Can be M or F'
    )
    people_parser.add_argument(
        '--status', type=str,
        default=None,
        help='preson\'s status. Can be affected or unaffected'
    )
    people_parser.add_argument(
        '--measureTypes', type=str,
        default=None,
        help='measure types. One of the following: ' + ', '.join(MEASURE_TYPES)
    )


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Query pheno properties")

    subparsers = parser.add_subparsers(
        title='subcommands',
        help='When no arguments given, subparsers list all respective queries')

    create_dbs_parser(subparsers)
    create_instruments_parser(subparsers)
    create_measures_parser(subparsers)
    create_people_parser(subparsers)

    args = parser.parse_args(argv)
    return {a: getattr(args, a) for a in dir(args) if a[0] != '_'}


if __name__ == "__main__":
    args_dict = parse_cli_arguments(sys.argv[1:])
    result = query_data(args_dict)

    for line in result:
        sys.stdout.write(join_line(line, '\t'))
