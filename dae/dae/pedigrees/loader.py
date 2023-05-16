"""Loader for pedigree files."""

import warnings
import logging
from functools import partial
from collections import defaultdict

import pandas as pd

from dae.utils.helpers import str2bool
from dae.variants.attributes import Role, Sex, Status
from dae.variants_loaders.raw.loader import CLILoader, CLIArgument

from dae.pedigrees.family import FamiliesData, Person, PEDIGREE_COLUMN_NAMES
from dae.pedigrees.family_role_builder import FamilyRoleBuilder
from dae.pedigrees.family_tag_builder import FamilyTagsBuilder
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
    """Pedigree files loader."""

    def __init__(self, families_filename, **params):

        super().__init__(params=params)
        self.filename = families_filename
        self.file_format = self.params.get("ped_file_format", "pedigree")

    @staticmethod
    def load_pedigree_file(
            pedigree_filename, pedigree_format=None) -> FamiliesData:
        """Load a pedigree files and return FamiliesData object."""
        if pedigree_format is None:
            pedigree_format = {}

        pedigree_format["ped_no_role"] = str2bool(
            pedigree_format.get("ped_no_role", False)
        )
        pedigree_format["ped_no_header"] = str2bool(
            pedigree_format.get("ped_no_header", False)
        )
        pedigree_format["ped_tags"] = str2bool(
            pedigree_format.get("ped_tags", False)
        )

        ped_df = FamiliesLoader.flexible_pedigree_read(
            pedigree_filename, **pedigree_format
        )
        families = FamiliesData.from_pedigree_df(ped_df)

        FamiliesLoader._build_families_layouts(families, pedigree_format)
        FamiliesLoader._build_families_roles(families, pedigree_format)
        FamiliesLoader._build_families_tags(families, pedigree_format)

        return families

    @staticmethod
    def _build_families_tags(families, pedigree_format):
        ped_tags = pedigree_format.get("ped_tags", False)
        if not ped_tags:
            return

        tagger = FamilyTagsBuilder()
        tagger.tag_families_data(families)

    @staticmethod
    def _build_families_layouts(families, pedigree_format):
        ped_layout_mode = pedigree_format.get("ped_layout_mode", "load")
        if ped_layout_mode == "generate":
            for family in families.values():
                logger.debug(
                    "building layout for family: %s; %s",
                    family.family_id, family)
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
            p.role is None  # or p.role == Role.unknown
            for p in families.persons.values())

        if has_unknown_roles or pedigree_format.get("ped_no_role"):
            for family in families.values():
                logger.debug("building family roles: %s", family.family_id)
                role_build = FamilyRoleBuilder(family)
                role_build.build_roles()
            families._ped_df = None  # pylint: disable=protected-access

    # @staticmethod
    # def load_simple_families_file(families_filename):
    #     ped_df = FamiliesLoader.load_simple_family_file(families_filename)
    #     return FamiliesData.from_pedigree_df(ped_df)

    def load(self) -> FamiliesData:
        if self.file_format == "simple":
            return self.load_simple_families_file(self.filename)
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
            "column. If this argument is provided, the import tool will guess "
            "the roles of individuals and write them in a 'role' column.",
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
            "--ped-tags",
            action="store_true",
            destination="ped_tags",
            default_value=True,
            help_text="when specified each family will be tagged with "
            "a number of predeined tags [default: %(default)s]",
        ))
        arguments.append(CLIArgument(
            "--ped-no-tags",
            action="store_false",
            destination="ped_tags",
            default_value=True,
            help_text="when specified tagging of families is disabled "
            "[default: %(default)s]",
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
            default_value="generate",
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
    def parse_cli_arguments(cls, argv, use_defaults=False):
        filename = argv.families
        super().parse_cli_arguments(argv, use_defaults=use_defaults)

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
            "ped_tags",
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
    def _produce_header_from_indices(**kwargs):
        header = (
            (kwargs.get("ped_family"), PEDIGREE_COLUMN_NAMES["family"]),
            (kwargs.get("ped_person"), PEDIGREE_COLUMN_NAMES["person"]),
            (kwargs.get("ped_mom"), PEDIGREE_COLUMN_NAMES["mother"]),
            (kwargs.get("ped_dad"), PEDIGREE_COLUMN_NAMES["father"]),
            (kwargs.get("ped_sex"), PEDIGREE_COLUMN_NAMES["sex"]),
            (kwargs.get("ped_status"), PEDIGREE_COLUMN_NAMES["status"]),
            (kwargs.get("ped_role"), PEDIGREE_COLUMN_NAMES["role"]),
            (kwargs.get("ped_proband"), PEDIGREE_COLUMN_NAMES["proband"]),
            (kwargs.get("ped_layout"), PEDIGREE_COLUMN_NAMES["layout"]),
            (kwargs.get("ped_generated"), PEDIGREE_COLUMN_NAMES["generated"]),
            (kwargs.get("ped_not_sequenced"),
             PEDIGREE_COLUMN_NAMES["not_sequenced"]),
            (kwargs.get("ped_sample_id"), PEDIGREE_COLUMN_NAMES["sample id"]),
        )
        header = tuple(  # type: ignore
            filter(lambda col: isinstance(col[0], int), header))
        for col in header:
            assert isinstance(col[0], int), col[0]
        header = tuple(sorted(header, key=lambda col: col[0]))  # type: ignore

        return zip(*header)

    @staticmethod
    def flexible_pedigree_read(
        pedigree_filepath,
        ped_sep="\t",
        ped_no_header=False,
        ped_no_role=False,
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
        **kwargs,  # pylint: disable=unused-argument
    ):
        """Read a pedigree from file."""
        # pylint: disable=too-many-arguments, too-many-locals
        if isinstance(ped_no_role, str):
            ped_no_role = str2bool(ped_no_role)
        if isinstance(ped_no_header, str):
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
                ped_generated: str2bool,
                ped_not_sequenced: str2bool,
                ped_proband: str2bool,
            },
            dtype=str,
            comment="#",
            encoding="utf-8",
        )
        with warnings.catch_warnings(record=True) as warn_messages:
            warnings.filterwarnings(
                "ignore",
                category=pd.errors.ParserWarning,
                message="Both a converter and dtype were specified",
            )

            if ped_no_header:
                _, file_header = FamiliesLoader._produce_header_from_indices(
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

        for warn in warn_messages:
            warnings.showwarning(
                warn.message, warn.category, warn.filename, warn.lineno)

        if ped_sample_id in ped_df:
            if ped_generated in ped_df or ped_not_sequenced in ped_df:

                def fill_sample_id(rec):
                    if not pd.isna(rec.sampleId):
                        return rec.sampleId
                    if rec.generated or rec.not_sequenced:
                        return None
                    return rec.personId

            else:

                def fill_sample_id(rec):
                    if not pd.isna(rec.sampleId):
                        return rec.sampleId
                    return rec.personId

            sample_ids = ped_df.apply(  # type: ignore
                fill_sample_id, axis=1, result_type="reduce",
            )
            ped_df[ped_sample_id] = sample_ids  # type: ignore
        else:
            sample_ids = pd.Series(
                data=ped_df[ped_person].values)  # type: ignore
            ped_df[ped_sample_id] = sample_ids  # type: ignore
        if ped_generated in ped_df:
            ped_df[ped_generated] = ped_df[  # type: ignore
                ped_generated].apply(  # type: ignore
                    lambda v: v if v else None)
        if ped_not_sequenced in ped_df:
            ped_df[ped_not_sequenced] = ped_df[  # type: ignore
                ped_not_sequenced].apply(
                    lambda v: v if v else None)  # type: ignore

        ped_df = ped_df.rename(  # type: ignore
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

        if not set(PED_COLUMNS_REQUIRED) <= set(
                ped_df.columns):  # type: ignore
            missing_columns = set(PED_COLUMNS_REQUIRED).difference(
                set(ped_df.columns)  # type: ignore
            )
            message = ", ".join(missing_columns)
            print(f"pedigree file missing columns {message}")
            raise ValueError(
                f"pedigree file missing columns {message}"
            )
        return ped_df

    @staticmethod
    def load_simple_families_file(infile, ped_sep="\t") -> FamiliesData:
        """Load a pedigree from a DAE simple family format file."""
        fam_df = pd.read_csv(
            infile,
            sep=ped_sep,
            index_col=False,
            skipinitialspace=True,
            converters={
                "role": Role.from_name,
                "gender": Sex.from_name,
                "sex": Sex.from_name,
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
        fam_df["status"] = fam_df.status.apply(Status.from_value)

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

            result[fam_id] = [
                Person(**member)  # type: ignore
                for member in members
            ]

        return FamiliesData.from_family_persons(result)

    @staticmethod
    def save_pedigree(families: FamiliesData, filename):
        """Save FamiliesData object into a pedigree file."""
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
        df.sex = df.sex.apply(lambda v: v.name)  # type: ignore
        df.role = df.role.apply(lambda v: v.name)  # type: ignore
        df.status = df.status.apply(lambda v: v.name)  # type: ignore

        df.to_csv(filename, index=False, sep="\t")

    @staticmethod
    def save_families(families: FamiliesData, filename):
        assert isinstance(families, FamiliesData)
        FamiliesLoader.save_pedigree(families, filename)
