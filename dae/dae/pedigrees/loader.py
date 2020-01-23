import warnings
import pandas as pd
import numpy as np

from functools import partial

from dae.utils.helpers import str2bool
from dae.variants.attributes import Role, Sex, Status

from dae.pedigrees.family import FamiliesData, PEDIGREE_COLUMN_NAMES
from dae.pedigrees.family_role_builder import FamilyRoleBuilder


PED_COLUMNS_REQUIRED = (
    PEDIGREE_COLUMN_NAMES['family'],
    PEDIGREE_COLUMN_NAMES['person'],
    PEDIGREE_COLUMN_NAMES['mother'],
    PEDIGREE_COLUMN_NAMES['father'],
    PEDIGREE_COLUMN_NAMES['sex'],
    PEDIGREE_COLUMN_NAMES['status'],
)


class FamiliesLoader:

    def __init__(self, families_filename, params={}, ped_sep='\t'):

        self.filename = families_filename
        self.params = params
        self.params['ped_sep'] = ped_sep
        self.file_format = params.get('ped_file_format', 'pedigree')

    @staticmethod
    def load_pedigree_file(pedigree_filename, pedigree_format={}):
        pedigree_format['ped_no_role'] = \
            str2bool(pedigree_format.get('ped_no_role', False))
        pedigree_format['ped_no_header'] = \
            str2bool(pedigree_format.get('ped_no_header', False))

        ped_df = FamiliesLoader.flexible_pedigree_read(
            pedigree_filename, **pedigree_format
        )
        families = FamiliesData.from_pedigree_df(ped_df)
        families._ped_df = ped_df
        if pedigree_format.get('ped_no_role'):
            for family in families.values():
                role_build = FamilyRoleBuilder(family)
                role_build.build_roles()
            families._ped_df = None
        return families

    @staticmethod
    def load_simple_families_file(families_filename):
        ped_df = FamiliesLoader.load_simple_family_file(
            families_filename
        )
        return FamiliesData.from_pedigree_df(ped_df)

    def load(self):
        if self.file_format == 'simple':
            return self.load_simple_families_file(self.filename)
        else:
            assert self.file_format == 'pedigree'
            return self.load_pedigree_file(
                self.filename, pedigree_format=self.params)

    @staticmethod
    def cli_defaults():
        return {
            'ped_family': 'familyId',
            'ped_person': 'personId',
            'ped_mom': 'momId',
            'ped_dad': 'dadId',
            'ped_sex': 'sex',
            'ped_status': 'status',
            'ped_role': 'role',
            'ped_file_format': 'pedigree',
            'ped_sep': '\t',
            'ped_no_header': False,
            'ped_no_role': False,
        }

    @staticmethod
    def build_cli_arguments(params):
        param_defaults = FamiliesLoader.cli_defaults()
        result = []
        for key, value in params.items():
            assert key in param_defaults, (key, list(param_defaults.keys()))
            if value != param_defaults[key]:
                param = key.replace('_', '-')
                if key in ('ped_no_header', 'ped_no_role'):
                    if value:
                        result.append(f'--{param}')
                else:
                    result.append(f'--{param}')
                    result.append(f'{value}')
        return ' '.join(result)

    @staticmethod
    def cli_arguments(parser):
        parser.add_argument(
            'families', type=str,
            metavar='<families filename>',
            help='families filename in pedigree or simple family format'
        )

        parser.add_argument(
            '--ped-family',
            default='familyId',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the ID of the family the person belongs to [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-person',
            default='personId',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the person\'s ID [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-mom',
            default='momId',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the ID of the person\'s mother [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-dad',
            default='dadId',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the ID of the person\'s father [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-sex',
            default='sex',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the sex of the person [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-status',
            default='status',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the status of the person [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-role',
            default='role',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the role of the person [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-no-role',
            action='store_true',
            help='indicates that the provided pedigree file has no role '
            'column. '
            'If this argument is provided, the import tool will guess the '
            'roles '
            'of individuals and write them in a "role" column.'
        )

        parser.add_argument(
            '--ped-no-header',
            action='store_true',
            help='indicates that the provided pedigree file has no header. '
            'The '
            'pedigree column arguments will accept indices if this argument '
            'is '
            'given. [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-file-format',
            default='pedigree',
            help='Families file format. It should `pedigree` or `simple`'
            'for simple family format [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-sep',
            default='\t',
            help='Families file field separator [default: `\\t`]'
        )

    @classmethod
    def parse_cli_arguments(cls, argv):
        filename = argv.families

        ped_ped_args = [
            'ped_family',
            'ped_person',
            'ped_mom',
            'ped_dad',
            'ped_sex',
            'ped_status',
            'ped_role',
            'ped_file_format',
            'ped_sep',
        ]
        res = {}

        res['ped_no_header'] = str2bool(argv.ped_no_header)
        res['ped_no_role'] = str2bool(argv.ped_no_role)

        for col in ped_ped_args:
            ped_value = getattr(argv, col)
            if not res['ped_no_header']:
                res[col] = ped_value
            else:
                assert ped_value.isnumeric(), \
                    '{} must hold an integer value!'.format(col)
                res[col] = int(ped_value)

        return filename, res

    @staticmethod
    def produce_header_from_indices(
       ped_family,
       ped_person,
       ped_mom,
       ped_dad,
       ped_sex,
       ped_status,
       ped_role,
       ped_layout,
       ped_generated,
       ped_sample_id,
    ):
        header = (
            (ped_family, PEDIGREE_COLUMN_NAMES['family']),
            (ped_person, PEDIGREE_COLUMN_NAMES['person']),
            (ped_mom, PEDIGREE_COLUMN_NAMES['mother']),
            (ped_dad, PEDIGREE_COLUMN_NAMES['father']),
            (ped_sex, PEDIGREE_COLUMN_NAMES['sex']),
            (ped_status, PEDIGREE_COLUMN_NAMES['status']),
            (ped_role, PEDIGREE_COLUMN_NAMES['role']),
            (ped_layout, PEDIGREE_COLUMN_NAMES['layout']),
            (ped_generated, PEDIGREE_COLUMN_NAMES['generated']),
            (ped_sample_id, PEDIGREE_COLUMN_NAMES['sample id']),
        )
        header = tuple(filter(lambda col: type(col[0]) is int, header))
        for col in header:
            assert type(col[0]) is int, col[0]
        header = tuple(sorted(header, key=lambda col: col[0]))
        return zip(*header)

    @staticmethod
    def flexible_pedigree_read(
            pedigree_filepath,
            ped_sep='\t',
            ped_has_header=True,
            ped_family='familyId',
            ped_person='personId',
            ped_mom='momId',
            ped_dad='dadId',
            ped_sex='sex',
            ped_status='status',
            ped_role='role',
            ped_layout='layout',
            ped_generated='generated',
            ped_sample_id='sampleId',
            ped_no_role=False,
            **kwargs):

        if type(ped_no_role) == str:
            ped_no_role = str2bool(ped_no_role)
        if type(ped_has_header) == str:
            ped_has_header = str2bool(ped_has_header)

        read_csv_func = partial(
            pd.read_csv,
            sep=ped_sep,
            index_col=False,
            skipinitialspace=True,
            converters={
                ped_role: Role.from_name,
                ped_sex: Sex.from_name_or_value,
                ped_status: Status.from_name_or_value,
                ped_layout: lambda lc: lc.split(':')[-1],
                ped_generated: lambda g: True if g == '1.0' else False,
            },
            dtype=str,
            comment='#',
            encoding='utf-8'
        )
        with warnings.catch_warnings(record=True) as ws:
            warnings.filterwarnings(
                'ignore',
                category=pd.errors.ParserWarning,
                message="Both a converter and dtype were specified"
            )

            if not ped_has_header:
                _, file_header = FamiliesLoader.produce_header_from_indices(
                    ped_family, ped_person, ped_mom,
                    ped_dad, ped_sex, ped_status,
                    ped_role, ped_layout, ped_generated, ped_sample_id,
                )
                ped_family = PEDIGREE_COLUMN_NAMES['family']
                ped_person = PEDIGREE_COLUMN_NAMES['person']
                ped_mom = PEDIGREE_COLUMN_NAMES['mother']
                ped_dad = PEDIGREE_COLUMN_NAMES['father']
                ped_sex = PEDIGREE_COLUMN_NAMES['sex']
                ped_status = PEDIGREE_COLUMN_NAMES['status']
                ped_role = PEDIGREE_COLUMN_NAMES['role']
                ped_layout = PEDIGREE_COLUMN_NAMES['layout']
                ped_generated = PEDIGREE_COLUMN_NAMES['generated']
                ped_sample_id = PEDIGREE_COLUMN_NAMES['sample id']
                ped_df = read_csv_func(
                    pedigree_filepath, header=None, names=file_header
                )
            else:
                ped_df = read_csv_func(pedigree_filepath)

        for w in ws:
            warnings.showwarning(
                w.message, w.category, w.filename, w.lineno)

        if ped_sample_id in ped_df:
            sample_ids = ped_df.apply(
                lambda r: r.personId if pd.isna(r.sampleId) else r.sampleId,
                axis=1,
                result_type='reduce',
            )
            ped_df[ped_sample_id] = sample_ids
        else:
            sample_ids = pd.Series(data=ped_df[ped_person].values)
            ped_df[ped_sample_id] = sample_ids

        ped_df = ped_df.rename(columns={
            ped_family: PEDIGREE_COLUMN_NAMES['family'],
            ped_person: PEDIGREE_COLUMN_NAMES['person'],
            ped_mom: PEDIGREE_COLUMN_NAMES['mother'],
            ped_dad: PEDIGREE_COLUMN_NAMES['father'],
            ped_sex: PEDIGREE_COLUMN_NAMES['sex'],
            ped_status: PEDIGREE_COLUMN_NAMES['status'],
            ped_role: PEDIGREE_COLUMN_NAMES['role'],
            ped_sample_id: PEDIGREE_COLUMN_NAMES['sample id'],
        })

        if not set(PED_COLUMNS_REQUIRED) <= set(ped_df.columns):
            missing_columns = \
                set(PED_COLUMNS_REQUIRED).difference(set(ped_df.columns))
            missing_columns = ', '.join(missing_columns)
            print(f"pedigree file missing missing columns {missing_columns}")
            raise ValueError(
                f"pedigree file missing missing columns {missing_columns}"
            )

        return ped_df

    @staticmethod
    def load_simple_family_file(infile, ped_sep="\t"):
        fam_df = pd.read_csv(
            infile, sep=ped_sep, index_col=False,
            skipinitialspace=True,
            converters={
                'role': lambda r: Role.from_name(r),
                'gender': lambda s: Sex.from_name(s),
                'sex': lambda s: Sex.from_name(s),
            },
            dtype={
                'familyId': str,
                'personId': str,
            },
            comment="#",
        )

        fam_df = fam_df.rename(columns={"gender": "sex"})

        fam_df['status'] = pd.Series(
            index=fam_df.index, data=1)
        fam_df.loc[fam_df.role == Role.prb, 'status'] = 2
        fam_df['status'] = fam_df.status.apply(lambda s: Status.from_value(s))

        fam_df['momId'] = pd.Series(
            index=fam_df.index, data='0')
        fam_df['dadId'] = pd.Series(
            index=fam_df.index, data='0')
        for fid, fam in fam_df.groupby(by='familyId'):
            mom_id = fam[fam.role == Role.mom]['personId'].iloc[0]
            dad_id = fam[fam.role == Role.dad]['personId'].iloc[0]
            children_mask = np.logical_and(
                fam_df['familyId'] == fid,
                np.logical_or(
                    fam_df.role == Role.prb,
                    fam_df.role == Role.sib))
            fam_df.loc[children_mask, 'momId'] = mom_id
            fam_df.loc[children_mask, 'dadId'] = dad_id

        if 'sampleId' not in fam_df.columns:
            sample_ids = pd.Series(data=fam_df['personId'].values)
            fam_df['sampleId'] = sample_ids

        fam_df.rename(columns={
            'personId': 'person_id',
            'familyId': 'family_id',
            'momId': 'mom_id',
            'dadId': 'dad_id',
            'sampleId': 'sample_id',
        }, inplace=True)
        return fam_df

    @staticmethod
    def save_pedigree(ped_df, filename):
        df = ped_df.copy()

        df = df.rename(columns={
            'person_id': 'personId',
            'family_id': 'familyId',
            'mom_id': 'momId',
            'dad_id': 'dadId',
            'sample_id': 'sampleId',
        })
        df.sex = df.sex.apply(lambda v: v.name)
        df.role = df.role.apply(lambda v: v.name)
        df.status = df.status.apply(lambda v: v.name)

        df.to_csv(filename, index=False, sep='\t')

    @staticmethod
    def save_families(families, filename):
        assert isinstance(families, FamiliesData)
        FamiliesLoader.save_pedigree(families.ped_df, filename)

    @staticmethod
    def get_default_colum_labels():
        return {
            "family_id": "familyId",
            "person_id": "personId",
            "father": "dadId",
            "mother": "momId",
            "sex": "sex",
            "status": "status",
            "role": "role",
            "layout": "layout"
        }
