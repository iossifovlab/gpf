#!/usr/bin/env python

from __future__ import print_function
import sys
import argparse
from collections import defaultdict
import pandas as pd


ROLES = ['mom', 'dad', 'prb', 'sib']


def create_families_arguments(parser):
    parser.add_argument(
        '-pi', '--personId',
        type=str, default='personId',
        dest='personId', metavar='families personIdColumn',
        help='personId column name in families file. Default is \'personId\''
    )
    parser.add_argument(
        '-s', '--status',
        type=str, default='status',
        dest='status', metavar='statusColumn',
        help='status column name in families file. Default is \'status\''
    )
    parser.add_argument(
        '--sex',
        type=str, default=None,
        dest='sex', metavar='sexColumn',
        help='column name for sex in families file. Optional argument. '
             'When ommited default for everybody is Unspecified'
    )
    parser.add_argument(
        '--familyId',
        type=str, default=None,
        metavar='familyIdColumn',
        help='column name for familyId in families file. Optional argument. '
             'When ommited default for everybody is same as sample\'s Id'
    )
    parser.add_argument(
        '--momId',
        type=str, default=None,
        metavar='momIdColumn',
        help='column name for momId in families file. Optional argument. '
             'When ommited default for everybody is 0'
    )
    parser.add_argument(
        '--dadId',
        type=str, default=None,
        metavar='dadIdColumn',
        help='column name for dadId in families file. Optional argument. '
             'When ommited default for everybody is 0'
    )


def create_variants_arguments(parser):
    parser.add_argument(
        '-si', '--sampleIdColumn',
        type=str, default='sampleId',
        dest='sampleId', metavar='variants sampleIdColumn',
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


def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Convert denovo data to DAE')

    parser.add_argument(
        'variantsFile', type=str,
        help='VCF format variant file. Available formats include '
             '.tsv, .csv, .xlsx'
    )
    parser.add_argument(
        'familiesFile', type=str,
        help='pedigree file with certain established format'
    )
    parser.add_argument(
        '-o', '--out', type=str, default=None,
        dest='outputFile', metavar='outputFilePath',
        help='output filepath'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='resolve conflicts concerning missing samples'
    )

    create_variants_arguments(parser)
    create_families_arguments(parser)

    args = parser.parse_args(argv)
    return {a: getattr(args, a) for a in dir(args) if a[0] != '_'}


def group_consecutive_sub_variants(v):
    data_groupby_samples = v.groupby(['sampleId', 'chr'])
    to_delete = []

    for _, samples_df in data_groupby_samples:
        for index1, row1 in samples_df.iterrows():
            row1_end = row1.pos + len(row1.ref)
            for index2, row2 in samples_df.iterrows():
                if row1_end == row2.pos:
                    start = row1.pos
                    ref, alt = row1.ref + row2.ref, row1.alt + row2.alt

                    v.loc[index1, ['pos', 'ref', 'alt']] = [start, ref, alt]
                    to_delete.append(index2)

    return v.drop(to_delete)


def load_file(filepath):
    extension = filepath.split('.').pop()
    try:
        if extension == 'tsv' or extension == 'ped':
            return pd.read_table(filepath, sep='\t')
        elif extension == 'csv':
            return pd.read_csv(filepath)
        elif extension == 'xlsx':
            return pd.read_excel(filepath)
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


class SharedData(object):
    def __init__(self, variants, families, force):
        self.initiate_values()
        self.force = force
        self.associate_person_variant(variants)
        self.assign_family(families.groupby(['familyId']))
        self.force_missing_samples(variants, families)

    def initiate_values(self):
        self.families_dict = defaultdict(lambda: defaultdict(list))
        self.person_sex = {}
        self.person_family = {}
        self.person_variant = defaultdict(list)
        self.counter = 0

    def associate_person_variant(self, variants):
        for _, row in variants.iterrows():
            variant = form_variant(row)
            self.person_variant[row.sampleId].append(variant)

    def assign_family(self, grouped):
        for fid, family_df in grouped:
            for _, person in family_df.iterrows():
                self.person_sex[person.personId] = person.sex
                self.person_family[person.personId] = fid
                self.families_dict[fid][person.role].append(person.personId)

    def increment_counter(self):
        self.counter += 1
        if self.counter % 1000 == 0:
            print('{} lines processed'.format(self.counter), file=sys.stdout)

    def force_missing_samples(self, variants, families):
        if not self.force:
            return

        missing_ids = set(variants.sampleId) - set(families.personId)
        for mid in missing_ids:
            self.person_family[mid] = mid
            self.families_dict[mid]['prb'].append(mid)
            self.person_sex[mid] = 'U'
            print('Including sample {}\'s variants...'
                  .format(mid), file=sys.stderr)


def bs2str(state):
    return state + '/' + state.replace('2', '0')


def sex_leter(sex):
    if sex in ["M", "F", "U"]:
        return sex
    else:
        return {1: "M", 2: "F", 0: "U"}[int(sex)]


def calculate_additional_columns(sd, variant, family):
    best_state, sample_id, in_child = [], [], ''

    for role in ROLES:
        if role in family:
            for member_id in family[role]:
                if member_id in sd.person_variant and \
                   variant in sd.person_variant[member_id]:
                    best_state.append('1')
                    sample_id.append(member_id)
                    in_child += role + sex_leter(sd.person_sex[member_id])
                else:
                    best_state.append('2')

    return bs2str(' '.join(best_state)), in_child, ', '.join(sample_id)


def generate_dae(variants, families, zero_based, force):
    sd = SharedData(variants, families, force)

    for _, row in variants.iterrows():
        sd.increment_counter()

        if row.sampleId not in sd.person_family:
            assert force is False
            print('Omitting variant. Sample {}\'s variant({}) not found in '
                  'pedigree file. Use --force if you wish to include it.'
                  .format(row.sampleId, form_variant(row)), file=sys.stderr)
            continue
        family_id = sd.person_family[row.sampleId]

        bs, ch, chid = calculate_additional_columns(
            sd, form_variant(row), sd.families_dict[family_id])
        pos = row.pos + 1 if zero_based else row.pos
        yield [family_id, row.chr, pos, row.ref, row.alt, bs, ch, chid]


def assert_required_columns(column_names, df, args):
    def error_msg(c, df):
        if c is not None and c not in df.columns:
            print('Column {} is missing from file'.format(c), file=sys.stderr)
            return True

    errors = [error_msg(c, df) for c in [args[k] for k in column_names]]
    if any(errors):
        sys.exit(1)


def prepare_families_df(args):
    families = load_file(args['familiesFile'])

    assert_required_columns(['personId', 'status'], families, args)

    families = families.rename(columns={
        args['personId']: 'personId',
        args['status']: 'status',
        args['familyId']: 'familyId',
        args['sex']: 'sex',
        args['momId']: 'momId',
        args['dadId']: 'dadId'})

    if args['sex'] is None:
        print('Sex column unspecified. Assigning U...', file=sys.stderr)
        families['sex'] = 'U'
    if args['familyId'] is None:
        print('FamilyId column unspecified. Generating them automatically...',
              file=sys.stderr)
        families['familyId'] = families.personId
    if args['momId'] is None:
        print('MomId column unspecified. Assigning 0''s...', file=sys.stderr)
        families['momId'] = 0
    if args['dadId'] is None:
        print('DadId column unspecified. Assigning 0''s...', file=sys.stderr)
        families['dadId'] = 0

    families = families.astype(str).astype({'status': int})
    families = drop_dups(families, 'families')

    families['role'] = families['status'].map({1: 'sib', 2: 'prb'})
    return families


def prepare_variants_df(args):
    variants = load_file(args['variantsFile'])

    assert_required_columns(['sampleId', 'chr', 'pos', 'ref', 'alt'],
                            variants, args)
    variants = variants.rename(columns={
        args['sampleId']: 'sampleId',
        args['chr']: 'chr', args['pos']: 'pos',
        args['ref']: 'ref', args['alt']: 'alt'}) \
        .astype({'sampleId': str, 'pos': int, 'chr': str})
    variants = drop_dups(variants, 'variants')
    return variants


def get_parent(families, parent_id, role):
    parent = families.loc[families.personId == parent_id].iloc[0]
    assert parent.sex == ('F' if role == 'mom' else 'M')
    return [parent.personId, 0, 0, role, parent.sex]


def get_family_id(children, existing_family_id):
    if existing_family_id:
        prbs = children.loc[children.status == 2]
        assert len(prbs) > 0
        return sorted(prbs.familyId)[0]
    else:
        family_ids = set(children.familyId)
        assert len(family_ids) == 1
        return family_ids.pop()


def reduce_families(families, variants, set_family_id=False):
    sample_ids = set(variants.sampleId)
    samples = families.loc[families.personId.isin(sample_ids)]
    grouped = samples.groupby(['momId', 'dadId'])

    for ids, children in grouped:
        mom_id, dad_id = ids
        if mom_id == '0' and dad_id == '0':
            for _, child in children.iterrows():
                yield [child.personId, child.personId, 0, 0,
                       child.role, child.sex]
            continue

        assert mom_id != '0' and dad_id != '0'

        family_id = get_family_id(children, set_family_id)
        yield [family_id] + get_parent(families, mom_id, 'mom')
        yield [family_id] + get_parent(families, dad_id, 'dad')
        for _, child in children.iterrows():
            yield [family_id, child.personId, mom_id, dad_id,
                   child.role, child.sex]


def export(filename, prepared_data):
    prepared_data.to_csv(filename, sep='\t', index=False)
    print('Exported to filepath: {}'.format(filename), file=sys.stdout)


def denovo2DAE(args):
    v, f = prepare_variants_df(args), prepare_families_df(args)

#     f = pd.DataFrame(
#         reduce_families(f, v, args['familyId'] is None),
#         columns=['familyId', 'personId', 'momId', 'dadId', 'role', 'sex'])

    prepared_data = pd.DataFrame(
        generate_dae(v, f, args['zerobased'], args['force']),
        columns=['familyId', 'chr', 'pos', 'ref', 'alt',
                 'bestState', 'inChild', 'sampleIds'])
    prepared_data = prepared_data.sort_values(by=['chr', 'pos'])
    return prepared_data


def output_filename(args):
    if not args['outputFile']:
        return '.'.join(args['variantsFile'].split('.')[:-1]) + '_prepared.tsv'
    return args['outputFile']


if __name__ == '__main__':
    args_dict = parse_cli_arguments(sys.argv[1:])
    export(output_filename(args_dict), denovo2DAE(args_dict))
