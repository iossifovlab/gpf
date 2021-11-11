import warnings
import logging
import pandas as pd

from functools import partial
from collections import defaultdict

from dae.utils.helpers import str2bool
from dae.variants.attributes import Role, Sex, Status
from dae.backends.raw.loader import CLILoader, CLIArgument

from dae.pedigrees.family import FamiliesData, Person, PEDIGREE_COLUMN_NAMES
from dae.pedigrees.family_role_builder import FamilyRoleBuilder
from dae.pedigrees.layout import Layout


logger = logging.getLogger(__name__)


PED_COLUMNS_REQUIRED = (
    PEDIGREE_COLUMN_NAMES["family"],
    PEDIGREE_COLUMN_NAMES["person"],
    PEDIGREE_COLUMN_NAMES["mother"],
    PEDIGREE_COLUMN_NAMES["father"],
    PEDIGREE_COLUMN_NAMES["sex"],
    PEDIGREE_COLUMN_NAMES["status"],
)


class FamiliesLoader(CLILoader):
    def __init__(self, families_filename, **params):

        super().__init__(params=params)
        self.filename = families_filename
        # TODO FIXME Params should be able to accept namedtuple instances
        # self.params["ped_sep"] = ped_sep
        self.file_format = self.params.get("ped_file_format", "pedigree")

    @staticmethod
    def load_pedigree_file(pedigree_filename, pedigree_format=None):
        if pedigree_format is None:
            pedigree_format = {}

        pedigree_format["ped_no_role"] = str2bool(
            pedigree_format.get("ped_no_role", False)
        )
        pedigree_format["ped_no_header"] = str2bool(
            pedigree_format.get("ped_no_header", False)
        )

        ped_df = FamiliesLoader.flexible_pedigree_read(
            pedigree_filename, **pedigree_format
        )
        families = FamiliesData.from_pedigree_df(ped_df)

        FamiliesLoader._build_families_layouts(families, pedigree_format)
        FamiliesLoader._build_families_roles(families, pedigree_format)

        return families

    @staticmethod
    def _build_families_layouts(families, pedigree_format):
        ped_layout_mode = pedigree_format.get("ped_layout_mode", "load")
        if ped_layout_mode == "generate":
            for family in families.values():
                logger.debug(
                    f"building layout for family: {family.family_id}; "
                    f"{family}")
                layouts = Layout.from_family(family)
                for layout in layouts:
                    layout.apply_to_family(family)
        elif ped_layout_mode == "load":
            pass
        else:
            raise ValueError(
                f"unexpected `--ped-layout-mode` option value "
                f"`{ped_layout_mode}`"
            )

    @staticmethod
    def _build_families_roles(families, pedigree_format):
        has_unknown_roles = any(
            [
                p.role is None  # or p.role == Role.unknown
                for p in families.persons.values()
            ]
        )

        if has_unknown_roles or pedigree_format.get("ped_no_role"):
            for family in families.values():
                logger.debug(f"building family roles: {family.family_id}")
                role_build = FamilyRoleBuilder(family)
                role_build.build_roles()
            families._ped_df = None

    # @staticmethod
    # def load_simple_families_file(families_filename):
    #     ped_df = FamiliesLoader.load_simple_family_file(families_filename)
    #     return FamiliesData.from_pedigree_df(ped_df)

    def load(self):
        if self.file_format == "simple":
            return self.load_simple_families_file(self.filename)
        else:
            assert self.file_format == "pedigree"
            return self.load_pedigree_file(
                self.filename, pedigree_format=self.params
            )

    @classmethod
    def _arguments(cls):
        arguments = []
        arguments.append(CLIArgument(
            "families",
            value_type=str,
            metavar="<families filename>",
            help_text="families filename in pedigree or simple family format",
        ))
        arguments.append(CLIArgument(
            "--ped-family",
            default_value="familyId",
            help_text="specify the name of the column in the pedigree"
            " file that holds the ID of the family the person belongs to"
            " [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-person",
            default_value="personId",
            help_text="specify the name of the column in the pedigree"
            " file that holds the person's ID [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-mom",
            default_value="momId",
            help_text="specify the name of the column in the pedigree"
            " file that holds the ID of the person's mother"
            " [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-dad",
            default_value="dadId",
            help_text="specify the name of the column in the pedigree"
            " file that holds the ID of the person's father"
            " [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-sex",
            default_value="sex",
            help_text="specify the name of the column in the pedigree"
            " file that holds the sex of the person [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-status",
            default_value="status",
            help_text="specify the name of the column in the pedigree"
            " file that holds the status of the person"
            " [default: %(default)s]",

        ))
        arguments.append(CLIArgument(
            "--ped-role",
            default_value="role",
            help_text="specify the name of the column in the pedigree"
            " file that holds the role of the person"
            " [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-no-role",
            action="store_true",
            default_value=False,
            help_text="indicates that the provided pedigree file has no role "
            "column. "
            "If this argument is provided, the import tool will guess the "
            "roles "
            'of individuals and write them in a "role" column.',
        ))
        arguments.append(CLIArgument(
            "--ped-proband",
            default_value=None,
            help_text="specify the name of the column in the pedigree"
            " file that specifies persons with role `proband`;"
            " this columns is used only when"
            " option `--ped-no-role` is specified. [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-no-header",
            action="store_true",
            default_value=False,
            help_text="indicates that the provided pedigree"
            " file has no header. The pedigree column arguments"
            " will accept indices if this argument is given."
            " [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-file-format",
            default_value="pedigree",
            help_text="Families file format. It should `pedigree` or `simple`"
            "for simple family format [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-layout-mode",
            default_value="load",
            help_text="Layout mode specifies how pedigrees "
            "drawing of each family is handled."
            " Available options are `generate` and `load`. When "
            "layout mode option is set to generate the loader"
            "tryes to generate a layout for the family pedigree. "
            "When `load` is specified, the loader tries to load the layout "
            "from the layout column of the pedigree. "
            "[default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-sep",
            default_value="\t",
            raw=True,
            help_text="Families file field separator [default: `\\t`]",
        ))
        return arguments

    @classmethod
    def parse_cli_arguments(cls, argv):
        filename = argv.families
        super().parse_cli_arguments(argv, use_defaults=False)

        ped_ped_args = [
            "ped_family",
            "ped_person",
            "ped_mom",
            "ped_dad",
            "ped_sex",
            "ped_status",
            "ped_role",
            "ped_file_format",
            "ped_sep",
            "ped_proband",
            "ped_layout_mode",
        ]
        columns = set(
            [
                "ped_family",
                "ped_person",
                "ped_mom",
                "ped_dad",
                "ped_sex",
                "ped_status",
                "ped_role",
                "ped_proband",
            ]
        )
        assert argv.ped_file_format in ("simple", "pedigree")
        assert argv.ped_layout_mode in ("generate", "load")

        res = {}

        res["ped_no_header"] = str2bool(argv.ped_no_header)
        res["ped_no_role"] = str2bool(argv.ped_no_role)

        for col in ped_ped_args:
            ped_value = getattr(argv, col)
            if not res["ped_no_header"] or col not in columns:
                res[col] = ped_value
            elif ped_value is not None and col in columns:
                res[col] = int(ped_value)

        return filename, res

    @staticmethod
    def produce_header_from_indices(
        ped_family=None,
        ped_person=None,
        ped_mom=None,
        ped_dad=None,
        ped_sex=None,
        ped_status=None,
        ped_role=None,
        ped_proband=None,
        ped_layout=None,
        ped_generated=None,
        ped_not_sequenced=None,
        ped_sample_id=None,
    ):
        header = (
            (ped_family, PEDIGREE_COLUMN_NAMES["family"]),
            (ped_person, PEDIGREE_COLUMN_NAMES["person"]),
            (ped_mom, PEDIGREE_COLUMN_NAMES["mother"]),
            (ped_dad, PEDIGREE_COLUMN_NAMES["father"]),
            (ped_sex, PEDIGREE_COLUMN_NAMES["sex"]),
            (ped_status, PEDIGREE_COLUMN_NAMES["status"]),
            (ped_role, PEDIGREE_COLUMN_NAMES["role"]),
            (ped_proband, PEDIGREE_COLUMN_NAMES["proband"]),
            (ped_layout, PEDIGREE_COLUMN_NAMES["layout"]),
            (ped_generated, PEDIGREE_COLUMN_NAMES["generated"]),
            (ped_not_sequenced, PEDIGREE_COLUMN_NAMES["not_sequenced"]),
            (ped_sample_id, PEDIGREE_COLUMN_NAMES["sample id"]),
        )
        header = tuple(filter(lambda col: type(col[0]) is int, header))
        for col in header:
            assert type(col[0]) is int, col[0]
        header = tuple(sorted(header, key=lambda col: col[0]))

        return zip(*header)

    @staticmethod
    def flexible_pedigree_read(
        pedigree_filepath,
        ped_sep="\t",
        ped_no_header=False,
        ped_family="familyId",
        ped_person="personId",
        ped_mom="momId",
        ped_dad="dadId",
        ped_sex="sex",
        ped_status="status",
        ped_role="role",
        ped_proband="proband",
        ped_layout="layout",
        ped_generated="generated",
        ped_not_sequenced="not_sequenced",
        ped_sample_id="sampleId",
        ped_no_role=False,
        **kwargs,
    ):

        if type(ped_no_role) == str:
            ped_no_role = str2bool(ped_no_role)
        if type(ped_no_header) == str:
            ped_no_header = str2bool(ped_no_header)

        read_csv_func = partial(
            pd.read_csv,
            sep=ped_sep,
            index_col=False,
            skipinitialspace=True,
            converters={
                ped_role: Role.from_name,
                ped_sex: Sex.from_name,
                ped_status: Status.from_name,
                ped_generated: lambda v: str2bool(v),
                ped_not_sequenced: lambda v: str2bool(v),
                ped_proband: lambda v: str2bool(v),
            },
            dtype=str,
            comment="#",
            encoding="utf-8",
        )
        with warnings.catch_warnings(record=True) as ws:
            warnings.filterwarnings(
                "ignore",
                category=pd.errors.ParserWarning,
                message="Both a converter and dtype were specified",
            )

            if ped_no_header:
                _, file_header = FamiliesLoader.produce_header_from_indices(
                    ped_family=ped_family,
                    ped_person=ped_person,
                    ped_mom=ped_mom,
                    ped_dad=ped_dad,
                    ped_sex=ped_sex,
                    ped_status=ped_status,
                    ped_role=ped_role,
                    ped_proband=ped_proband,
                    ped_layout=ped_layout,
                    ped_generated=ped_generated,
                    ped_not_sequenced=ped_not_sequenced,
                    ped_sample_id=ped_sample_id,
                )
                ped_family = PEDIGREE_COLUMN_NAMES["family"]
                ped_person = PEDIGREE_COLUMN_NAMES["person"]
                ped_mom = PEDIGREE_COLUMN_NAMES["mother"]
                ped_dad = PEDIGREE_COLUMN_NAMES["father"]
                ped_sex = PEDIGREE_COLUMN_NAMES["sex"]
                ped_status = PEDIGREE_COLUMN_NAMES["status"]
                ped_role = PEDIGREE_COLUMN_NAMES["role"]
                ped_proband = PEDIGREE_COLUMN_NAMES["proband"]
                ped_layout = PEDIGREE_COLUMN_NAMES["layout"]
                ped_generated = PEDIGREE_COLUMN_NAMES["generated"]
                ped_not_sequenced = PEDIGREE_COLUMN_NAMES["not_sequenced"]
                ped_sample_id = PEDIGREE_COLUMN_NAMES["sample id"]
                ped_df = read_csv_func(
                    pedigree_filepath, header=None, names=file_header
                )
            else:
                ped_df = read_csv_func(pedigree_filepath)

        for w in ws:
            warnings.showwarning(w.message, w.category, w.filename, w.lineno)

        if ped_sample_id in ped_df:
            if ped_generated in ped_df or ped_not_sequenced in ped_df:

                def fill_sample_id(r):
                    if not pd.isna(r.sampleId):
                        return r.sampleId
                    else:
                        if r.generated or r.not_sequenced:
                            return None
                        else:
                            return r.personId

            else:

                def fill_sample_id(r):
                    if not pd.isna(r.sampleId):
                        return r.sampleId
                    else:
                        return r.personId

            sample_ids = ped_df.apply(
                lambda r: fill_sample_id(r), axis=1, result_type="reduce",
            )
            ped_df[ped_sample_id] = sample_ids
        else:
            sample_ids = pd.Series(data=ped_df[ped_person].values)
            ped_df[ped_sample_id] = sample_ids
        if ped_generated in ped_df:
            ped_df[ped_generated] = ped_df[ped_generated].apply(
                lambda v: v if v else None
            )
        if ped_not_sequenced in ped_df:
            ped_df[ped_not_sequenced] = ped_df[ped_not_sequenced].apply(
                lambda v: v if v else None
            )

        ped_df = ped_df.rename(
            columns={
                ped_family: PEDIGREE_COLUMN_NAMES["family"],
                ped_person: PEDIGREE_COLUMN_NAMES["person"],
                ped_mom: PEDIGREE_COLUMN_NAMES["mother"],
                ped_dad: PEDIGREE_COLUMN_NAMES["father"],
                ped_sex: PEDIGREE_COLUMN_NAMES["sex"],
                ped_status: PEDIGREE_COLUMN_NAMES["status"],
                ped_role: PEDIGREE_COLUMN_NAMES["role"],
                ped_proband: PEDIGREE_COLUMN_NAMES["proband"],
                ped_sample_id: PEDIGREE_COLUMN_NAMES["sample id"],
            }
        )

        if not set(PED_COLUMNS_REQUIRED) <= set(ped_df.columns):
            missing_columns = set(PED_COLUMNS_REQUIRED).difference(
                set(ped_df.columns)
            )
            missing_columns = ", ".join(missing_columns)
            print(f"pedigree file missing columns {missing_columns}")
            raise ValueError(
                f"pedigree file missing columns {missing_columns}"
            )
        return ped_df

    @staticmethod
    def load_simple_families_file(infile, ped_sep="\t"):
        fam_df = pd.read_csv(
            infile,
            sep=ped_sep,
            index_col=False,
            skipinitialspace=True,
            converters={
                "role": lambda r: Role.from_name(r),
                "gender": lambda s: Sex.from_name(s),
                "sex": lambda s: Sex.from_name(s),
            },
            dtype={"familyId": str, "personId": str},
            comment="#",
        )

        fam_df = fam_df.rename(
            columns={
                "gender": "sex",
                "personId": "person_id",
                "familyId": "family_id",
                "momId": "mom_id",
                "dadId": "dad_id",
                "sampleId": "sample_id",
            },
        )

        fam_df["status"] = pd.Series(index=fam_df.index, data=1)
        fam_df.loc[fam_df.role == Role.prb, "status"] = 2
        fam_df["status"] = fam_df.status.apply(lambda s: Status.from_value(s))

        fam_df["mom_id"] = pd.Series(index=fam_df.index, data="0")
        fam_df["dad_id"] = pd.Series(index=fam_df.index, data="0")

        if "sample_id" not in fam_df.columns:
            sample_ids = pd.Series(data=fam_df["person_id"].values)
            fam_df["sample_id"] = sample_ids

        families = defaultdict(list)
        for rec in fam_df.to_dict(orient="records"):
            families[rec["family_id"]].append(rec)

        result = defaultdict(list)
        for fam_id, members in families.items():
            mom_id = None
            dad_id = None
            children = []
            for member in members:
                role = member["role"]
                if role == Role.mom:
                    mom_id = member["person_id"]
                elif role == Role.dad:
                    dad_id = member["person_id"]
                else:
                    assert role in set([Role.prb, Role.sib])
                    children.append(member)
            for child in children:
                child["mom_id"] = mom_id
                child["dad_id"] = dad_id

            result[fam_id] = [Person(**member) for member in members]

        return FamiliesData.from_family_persons(result)

    @staticmethod
    def save_pedigree(families, filename):
        df = families.ped_df.copy()

        df = df.rename(
            columns={
                "person_id": "personId",
                "family_id": "familyId",
                "mom_id": "momId",
                "dad_id": "dadId",
                "sample_id": "sampleId",
            }
        )
        df.sex = df.sex.apply(lambda v: v.name)
        df.role = df.role.apply(lambda v: v.name)
        df.status = df.status.apply(lambda v: v.name)

        df.to_csv(filename, index=False, sep="\t")

    @staticmethod
    def save_families(families, filename):
        assert isinstance(families, FamiliesData)
        FamiliesLoader.save_pedigree(families, filename)
