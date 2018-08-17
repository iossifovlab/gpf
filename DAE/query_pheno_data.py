from DAE import pheno
from itertools import combinations
import pandas as pd
import sys

def query_phenodbs(data):
    data.append(GENERIC_PHENO_DATA_COLUMNS['listDatabases'])
    for name in get_phenodb_names():
        data.append([name])

def query_instruments(data, dbs):
    data.append(GENERIC_PHENO_DATA_COLUMNS['listInstruments'])
    for db_name in dbs:
        db = pheno.get_pheno_db(db_name)
        data += map(lambda k: [db_name, k], db.instruments.keys())

def contained_in_options(value, container):
    if not container: return True
    else: return value in container

def query_measures(data, filters):
    data.append(GENERIC_PHENO_DATA_COLUMNS['listMeasures'])
    for db_name in filters['phenodbs']:
        db = pheno.get_pheno_db(db_name)
        data += [[db_name, m.measure_id, m.name,
                    m.instrument_name, m.measure_type.name,
                    str(m.min_value), str(m.max_value)]
                    for m in db.measures.values()
                    if contained_in_options(m.instrument_name, filters['instrumentIds'])
                    and contained_in_options(m.measure_type.name, filters['measureTypes'])
                    and contained_in_options(m.measure_id, filters['measureIds'])]

def measure_values(row, m_names):
    return [str(row[name]) for name in m_names]

def clean_list(arr, all_set):
    if not arr: return None
    return [x for x in list(set(arr)) if x in all_set]

def measureids_by_type_and_instrument(ins, types, db):
    if (ins is None and types is None): return None
    if ins == [] or types == []: return []

    if not ins: ins = [None]
    if not types: types = [None]
    it_measure_ids = []

    filters = [f for f in combinations(ins+types,2)
                if f[0] in ins and f[1] in types]
    for i,t in filters: it_measure_ids += db.get_measures(i,t)
    return it_measure_ids

def query_people(data, options):
    data.append(list(GENERIC_PHENO_DATA_COLUMNS['listPeople']))
    for db_name in options['phenodbs']:
        db = pheno.get_pheno_db(db_name)

        measure_ids = clean_list(options['measureIds'], db.measures)
        instrument_ids = clean_list(options['instrumentIds'], db.instruments)
        measure_types = clean_list(options['measureTypes'],
                        ['continuous', 'ordinal', 'categorical', 'unknown'])

        it_measure_ids = measureids_by_type_and_instrument(
            instrument_ids, measure_types, db)
        if it_measure_ids is not None and measure_ids is not None:
            measure_ids = list(set(measure_ids) & set(it_measure_ids))
        if not measure_ids:
            continue

        df = db.get_persons_values_df(measure_ids, roles=options['roles'],
            person_ids=options['personIds'], family_ids=options['familyIds'])
        measure_columns = list(df.columns)[5:]

        data += [[db_name, row.person_id, row.family_id,
                    row.role.name, row.gender.name, row.status.name]
                    + ['' for m in data[0][6:]]
                    + measure_values(row, measure_columns)
                    for _,row in df.iterrows()
                    if contained_in_options(row.gender.name, options['gender'])
                    and contained_in_options(row.status.name, options['status'])]
        data[0] += measure_columns


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
        if not options[arg]: options[arg] = []
        options[arg] += options[file_arg]

def include_file_arguments(options):
    add_file_arg('familyIds', options)
    add_file_arg('personIds', options)

def get_phenodb_names():
    return pheno.get_pheno_db_names()

def get_measures(dbs):
    ms = []
    for db_name in dbs:
        db = pheno.get_pheno_db(db_name)
        ms += db.measures.keys()
    return ms


def parse_filter(options, filter_name, all_set):
    if filter_name not in options: return

    if not options[filter_name]:
        options[filter_name] = all_set
    else:
        options[filter_name] = clean_list(options[filter_name], all_set)

def prepare_filter(options, arg):
    if arg not in options or options[arg] is None: return None
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
    else:
        return 'people'


def prepare_options(options):
    prepared_options = {
        'parser': get_parser_name(options)
    }
    prepared_options.update({k:prepare_filter(options, k)
                            for (k,v) in options.items()})

    parse_filter(prepared_options, 'phenodbs', get_phenodb_names())
    if 'phenodbs' in prepared_options:
        dbs = prepared_options['phenodbs']
        if dbs and prepared_options['parser'] == 'people':
            parse_filter(prepared_options, 'measureIds', get_measures(dbs))

    include_file_arguments(prepared_options)

    return prepared_options

def generate_response(data):
    for row in data: yield row

def sjoin(x):
    return (' '.join(x[x.notnull()].astype(str))).strip()

def add_missing_measures(data):
    for row in data:
        while len(row) < len(data[0]):
            row.append('')

def rearange_columns(header, etc):
    return header + [x for x in etc if x not in header]

def remove_dups(data):
    if len(set(data[0])) == len(data[0]): return data

    df = pd.DataFrame(data[1:], columns=data[0])
    df = df.groupby(level=0, axis=1).apply(lambda x: x.apply(sjoin, axis=1))
    df = df[rearange_columns(
        GENERIC_PHENO_DATA_COLUMNS['listPeople'], list(df.columns))]

    return [list(df.columns)] + [list(row) for _,row in df.iterrows()]

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
        add_missing_measures(data)
        data = remove_dups(data)

    return generate_response(data)


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
