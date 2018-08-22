#!/usr/bin/env python

from __future__ import print_function
import sys
import argparse
import pandas as pd
from DAE import genomesDB


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Convert denovo data to DAE")

    parser.add_argument(
        'variantsFile', type=str,
        help='VCF format variant file. Available formats include '
             '.tsv, .csv, .xlsx'
    )
    parser.add_argument(
        'pedFile', type=str,
        help='pedgree file with certain established format'
    )
    parser.add_argument(
        '-f', '--file', type=str, default=None,
        dest='outputFile', metavar='outputFileName',
        help='output filepath'
    )
    parser.add_argument(
        '--skiprows', type=int, default=0,
        metavar='NumberOfRows',
        help='number of rows to be skipped from variants file. '
             'Applied only for xlsx files'
    )
    parser.add_argument(
        '-i', '--sampleIdColumn',
        type=str, default='sampleId',
        dest='sampleId', metavar='sampleIdColumn',
        help='column name for sampleId. Default is \'sampleId\''
    )
    parser.add_argument(
        '-c', '--chrColumn',
        type=str, default='chr',
        dest='chr', metavar='chrColumn',
        help='column name for chromosome. Default is \'chr\''
    )
    parser.add_argument(
        '-p', '--posColumn',
        type=str, default='pos',
        dest='pos', metavar='posColumn',
        help='column name for position. Default is \'pos\''
    )
    parser.add_argument(
        '-r', '--refColumn',
        type=str, default='ref',
        dest='ref', metavar='refColumn',
        help='column name for reference allele. Default is \'ref\''
    )
    parser.add_argument(
        '-a', '--altColumn',
        type=str, default='alt',
        dest='alt', metavar='altColumn',
        help='column name for alternative allele. Default is \'alt\''
    )
    parser.add_argument(
        '--zerobased',
        action='store_true',
        help='flag chromosome positions as zero based'
    )

    args = parser.parse_args(argv)
    return {a: getattr(args, a) for a in dir(args) if a[0] != '_'}


def import_file(filepath, skiprows=0):
    extension = filepath.split('.').pop()

    try:
        if extension == 'tsv' or extension == 'ped':
            return pd.read_table(filepath, sep='\t')
        elif extension == 'csv':
            return pd.read_csv(filepath)
        elif extension == 'xlsx':
            return pd.read_excel(filepath, skiprows=skiprows)
        else:
            raise IOError
    except IOError:
        print('ERROR:Incorrect filepath: {}'.format(filepath), file=sys.stderr)
        sys.exit(1)


def drop_dups(df, metadata=''):
    prev_len = len(df)
    df = df.drop_duplicates()
    print('Dropped {} duplicates from {} data'
          .format(prev_len - len(df), metadata), file=sys.stdout)
    return df


def form_variant(row):
    return (str(row.chr) + ':' + str(row.pos) + ', ' +
            str(row.ref) + '->' + str(row.alt))


def append_val(k, val, d):
    try:
        d[k].append(val)
    except KeyError:
        d[k] = [val]


def associate_person_variant(variants):
    for _, row in variants.iterrows():
        variant = form_variant(row)
        append_val(row.sampleId, variant, person_variant)


ROLES = ['mom', 'dad', 'prb', 'sib']
UNCOMMON_FAMILY_MEMBERS = []


def special_case(person):
    if person.role not in ROLES:
        if person.personId in person_variant:
            print('Uncommon family name with variant:', file=sys.stdout)
            print(person.personId + '-' + person.role + ': ' +
                  person_variant[person.personId], file=sys.stdout)
            print('No action taken...', file=sys.stdout)
        else:
            UNCOMMON_FAMILY_MEMBERS.append(person)  # export if necessary
            print('Removing ' + str(len(UNCOMMON_FAMILY_MEMBERS)) + ': '
                  + person.personId + ', role:' + person.role, file=sys.stdout)
        return True
    return False


def assign_family(grouped):
    for family_id, family_df in grouped:
        f = families_dict[family_id] = {}

        for _, person in family_df.iterrows():
            if special_case(person):
                continue

            pid, role = person.personId, person.role
            person_gender[pid] = person.gender
            person_family[pid] = family_id

            if role == 'mom':
                f['mom'] = [pid]
            elif role == 'dad':
                f['dad'] = [pid]
            elif role == 'prb':
                append_val('prb', pid, f)
            else:
                append_val('sib', pid, f)


def populate_global_data(variants, families):
    global person_variant, families_dict, person_gender, person_family

    families_dict = {}
    person_gender = {}
    person_family = {}
    person_variant = {}

    associate_person_variant(variants)
    assign_family(families.groupby(['familyId']))


def find_prob_family(probant_id):
    try:
        return person_family[probant_id]
    except KeyError:
        return None


def bs2str(state):
    return state + '/' + state.replace('2', '0')


def stats(variant, family):
    best_state, sample_id, in_child = [], [], ''

    for role in ROLES:
        if role in family:
            for member_id in family[role]:
                if member_id in person_variant and \
                   variant in person_variant[member_id]:
                    best_state.append('1')
                    sample_id.append(member_id)
                    in_child += role + person_gender[member_id]
                else:
                    best_state.append('2')

    return bs2str(' '.join(best_state)), in_child, ', '.join(sample_id)


def generate_dae(variants, families, zb):
    populate_global_data(variants, families)
    counter = 0
    for _, row in variants.iterrows():
        counter += 1
        if counter % 1000 == 0:
            print('{} lines processed'.format(counter), file=sys.stdout)

        family_id = find_prob_family(row.sampleId)
        if not family_id:
            continue

        bs, ch, chid = stats(form_variant(row), families_dict[family_id])
        pos = row.pos + 1 if zb else row.pos
        yield [family_id, row.chr, pos, row.ref, row.alt, bs, ch, chid]


def transform_files(args):
    variants = import_file(args['variantsFile'], args['skiprows'])
    families = import_file(args['pedFile']).astype(str)

    assert all([c in variants.columns for c in
                [args[k] for k in ['sampleId', 'chr', 'pos', 'ref', 'alt']]])

    families = families.astype({'status': int})
    variants = variants.rename(columns={
        args['sampleId']: 'sampleId',
        args['chr']: 'chr', args['pos']: 'pos',
        args['ref']: 'ref', args['alt']: 'alt'}) \
        .astype({'sampleId': str, 'pos': int, 'chr': str})

    variants = drop_dups(variants, 'variants')
    families = drop_dups(families, 'families')

    return variants, families


def consecutive_subs_correction(v):
    data_groupby_samples = v.groupby(['sampleId', 'chr'])
    to_delete = []

    for _, samples_df in data_groupby_samples:
        for index1, row1 in samples_df.iterrows():
            row1_end = row1.pos + len(row1.ref)
            for index2, row2 in samples_df.iterrows():
                row2_end = row2.pos + len(row2.ref)
                if row1_end == row2.pos:
                    start = row1.pos, row2_end
                    ref, alt = row1.ref + row2.ref, row1.alt + row2.alt

                    v.loc[index1, ['pos', 'ref', 'alt']] = [start, ref, alt]
                    to_delete.append(index2)

    return v.drop(to_delete)


def ref_alt_nan_correction(v):
    genome = genomesDB.get_genome()
    rows_to_change = {}

    for index, row in v.iterrows():
        # insertion ref:next alt:next+given
        if row.ref is pd.np.nan:
            new_ref = genome.getSequence(row.chr, row.pos,
                                         row.pos + len(row.alt) - 1)
            rows_to_change[index] = new_ref, new_ref+row.alt, row.pos
        # deletion ref:prev+given alt:prev
        if row.alt is pd.np.nan:
            new_alt = genome.getSequence(row.chr, row.pos-1, row.pos-1)
            rows_to_change[index] = new_alt+row.ref, new_alt, row.pos-1

    for index, values in rows_to_change.items():
        row = v.loc[index].copy()
        row.ref, row.alt, row.pos = values
        v = v.drop(index).append(row)
    return v


def perform_corrections(v):
    if v.ref.isnull().any() or v.alt.isnull().any():
        print('Correcting incomplete ref and alt allele data...',
              file=sys.stdout)
        count = v.ref.isnull().sum() + v.alt.isnull().sum()
        v = ref_alt_nan_correction(v)
        print('>>> {} variants changed.'.format(count), file=sys.stdout)

    print('Grouping consecutive substitutions...', file=sys.stdout)
    count, v = len(v), consecutive_subs_correction(v)
    print('>>> {} new complex variants formed.'.format(count-len(v)),
          file=sys.stdout)

    return v


def export(filename, prepared_data):
    prepared_data.to_csv(filename, sep='\t', index=False)
    print('Exported to filepath: {}'.format(filename), file=sys.stdout)


def denovo2DAE(args):
    v, f = transform_files(args)
    v = perform_corrections(v)

    prepared_data = pd.DataFrame(
        generate_dae(v, f, args['zerobased']),
        columns=['familyId', 'chr', 'pos', 'ref', 'alt',
                 'bestState', 'inChild', 'sampleIds'])
    prepared_data = prepared_data.sort_values(by=['chr', 'pos'])
    return prepared_data


def output_filename(args):
    if not args['outputFile']:
        args['outputFile'] = '.'.join(
            args['variantsFile'].split('.')[:-1]) + '_prepared.tsv'
    return args['outputFile']


if __name__ == '__main__':
    args_dict = parse_cli_arguments(sys.argv[1:])
    export(output_filename(args_dict), denovo2DAE(args_dict))
