import os
import gzip

from typing import List, Optional, Dict, Any
from contextlib import closing

import pysam
import numpy as np
import pandas as pd

from dae.RegionOperations import Region

from dae.GenomeAccess import GenomicSequence
from dae.utils.variant_utils import str2mat, GENOTYPE_TYPE
from dae.utils.helpers import str2bool

from dae.utils.dae_utils import dae2vcf_variant

from dae.pedigrees.family import Family, FamiliesData
from dae.variants.attributes import Inheritance

from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant

from dae.backends.raw.loader import (
    VariantsGenotypesLoader,
    TransmissionType,
    FamiliesGenotypes,
)

from dae.variants.attributes import VariantType

from dae.utils.variant_utils import get_locus_ploidy


class DenovoFamiliesGenotypes(FamiliesGenotypes):
    def __init__(self, family, gt, best_state=None):
        super(DenovoFamiliesGenotypes, self).__init__()
        self.family = family
        self.gt = gt
        self.best_state = best_state

    def get_family_genotype(self):
        return self.gt

    def get_family_best_state(self):
        return self.best_state

    def family_genotype_iterator(self):
        yield self.family, self.gt, self.best_state


class DenovoLoader(VariantsGenotypesLoader):
    def __init__(
        self,
        families: FamiliesData,
        denovo_filename: str,
        genome: GenomicSequence,
        regions: List[str] = None,
        params: Dict[str, Any] = {},
    ):
        super(DenovoLoader, self).__init__(
            families=families,
            filenames=[denovo_filename],
            transmission_type=TransmissionType.denovo,
            genome=genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=False,
            params=params,
        )

        self.genome = genome
        self.set_attribute("source_type", "denovo")

        self.denovo_df = self.flexible_denovo_load(
            denovo_filename,
            genome,
            families=families,
            adjust_chrom_prefix=self._adjust_chrom_prefix,
            **self.params,
        )
        self._init_chromosomes()

        if np.all(pd.isnull(self.denovo_df["genotype"])):
            self.expect_best_state = True
        elif np.all(pd.isnull(self.denovo_df["best_state"])):
            self.expect_genotype = True
        else:
            assert False

    def _init_chromosomes(self):
        self.chromosomes = list(self.denovo_df.chrom.unique())
        self.chromosomes = [
            self._adjust_chrom_prefix(chrom) for chrom in self.chromosomes
        ]

        all_chromosomes = self.genome.allChromosomes
        if all([chrom in set(all_chromosomes) for chrom in self.chromosomes]):
            self.chromosomes = sorted(
                self.chromosomes,
                key=lambda chrom: all_chromosomes.index(chrom),
            )

    def _is_in_regions(self, summary_variant):
        isin = [
            r.isin(summary_variant.chrom, summary_variant.position)
            if r is not None
            else True
            for r in self.regions
        ]
        return any(isin)

    def _full_variants_iterator_impl(self):
        self.regions = [Region.from_str(r) for r in self.regions]
        for region in self.regions:
            if region is None:
                continue
            region.chrom = self._adjust_chrom_prefix(region.chrom)

        for index, rec in enumerate(self.denovo_df.to_dict(orient="records")):
            family_id = rec.pop("family_id")
            gt = rec.pop("genotype")
            best_state = rec.pop("best_state")

            rec["summary_variant_index"] = index
            rec["allele_index"] = 1

            summary_variant = SummaryVariantFactory.summary_variant_from_records(
                [rec], self.transmission_type
            )
            if not self._is_in_regions(summary_variant):
                continue

            family = self.families.get(family_id)
            if family is None:
                continue

            family_genotypes = DenovoFamiliesGenotypes(family, gt, best_state)

            family_variants = []
            for fam, gt, bs in family_genotypes.family_genotype_iterator():
                fv = FamilyVariant(summary_variant, fam, gt, bs)
                family_variants.append(fv)

            yield summary_variant, family_variants

    def full_variants_iterator(self):
        full_iterator = super(DenovoLoader, self).full_variants_iterator()
        for summary_vairants, family_variants in full_iterator:
            for fv in family_variants:
                for fa in fv.alt_alleles:
                    inheritance = [
                        Inheritance.denovo if mem is not None else inh
                        for inh, mem in zip(
                            fa.inheritance_in_members, fa.variant_in_members
                        )
                    ]
                    fa._inheritance_in_members = inheritance

            yield summary_vairants, family_variants

    @staticmethod
    def split_location(location):
        chrom, position = location.split(":")
        return chrom, int(position)

    @staticmethod
    def produce_genotype(
        chrom: str,
        pos: int,
        genome: GenomicSequence,
        family: Family,
        members_with_variant: List[str],
    ) -> np.array:
        # TODO Add support for multiallelic variants
        # This method currently assumes biallelic variants

        genotype = np.zeros(shape=(2, len(family)), dtype=GENOTYPE_TYPE)

        for person_id, person in family.persons.items():

            index = family.members_index([person_id])
            has_variant = int(person_id in members_with_variant)

            ploidy = get_locus_ploidy(chrom, pos, person.sex, genome)

            if ploidy == 2:
                genotype[1, index] = has_variant
            else:
                genotype[0, index] = has_variant
                genotype[1, index] = -2  # signifies haploid genotype

        return genotype

    @classmethod
    def cli_arguments(cls, parser):
        parser.add_argument(
            "denovo_file",
            type=str,
            metavar="<variants filename>",
            help="DAE denovo variants file",
        )
        DenovoLoader.cli_options(parser)

    @classmethod
    def cli_options(cls, parser):
        variant_group = parser.add_argument_group("variant specification")

        variant_group.add_argument(
            "--denovo-variant",
            help="The label or index of the column containing the CSHL-style"
            " representation of the variant."
            "[Default: variant]",
        )
        variant_group.add_argument(
            "--denovo-ref",
            help="The label or index of the column containing the reference"
            " allele for the variant. [Default: none]",
        )
        variant_group.add_argument(
            "--denovo-alt",
            help="The label or index of the column containing the alternative"
            " allele for the variant. [Default: none]",
        )

        location_group = parser.add_argument_group("variant location")
        location_group.add_argument(
            "--denovo-location",
            help="The label or index of the column containing the CSHL-style"
            " location of the variant. [Default: location]",
        )
        location_group.add_argument(
            "--denovo-chrom",
            help="The label or index of the column containing the chromosome"
            " upon which the variant is located. [Default: none]",
        )
        location_group.add_argument(
            "--denovo-pos",
            help="The label or index of the column containing the position"
            " upon which the variant is located. [Default: none]",
        )

        genotype_group = parser.add_argument_group("variant genotype")
        genotype_group.add_argument(
            "--denovo-family-id",
            help="The label or index of the column containing the "
            "family's ID. [Default: familyId]",
        )
        genotype_group.add_argument(
            "--denovo-best-state",
            help="The label or index of the column containing the best state"
            " for the family. [Default: bestState]",
        )
        genotype_group.add_argument(
            "--denovo-person-id",
            help="The label or index of the column containing the "
            "person's ID. [Default: none]",
        )

        parser.add_argument(
            "--denovo-sep",
            type=str,
            default=None,
            help="Denovo file field separator [default: `\\t`]",
        )

        parser.add_argument(
            "--add-chrom-prefix",
            type=str,
            default=None,
            help="Add specified prefix to each chromosome name in "
            "variants file",
        )
        parser.add_argument(
            "--del-chrom-prefix",
            type=str,
            default=None,
            help="Removes specified prefix from each chromosome name in "
            "variants file",
        )

    @classmethod
    def cli_defaults(cls):
        return {
            "denovo_variant": "variant",
            "denovo_ref": None,
            "denovo_alt": None,
            "denovo_location": "location",
            "denovo_chrom": None,
            "denovo_pos": None,
            "denovo_family_id": "familyId",
            "denovo_best_state": "bestState",
            "denovo_person_id": None,
            "add_chrom_prefix": None,
            "del_chrom_prefix": None,
            "denovo_sep": "\t",
        }

    @classmethod
    def build_cli_arguments(cls, params):
        param_defaults = DenovoLoader.cli_defaults()
        result = []
        for k, v in params.items():
            assert k in param_defaults, (k, list(param_defaults.keys()))
            if v != param_defaults[k]:
                param = k.replace("_", "-")
                result.append(f"--{param}")
                result.append(f"{v}")

        return " ".join(result)

    @classmethod
    def parse_cli_arguments(cls, argv):
        if argv.denovo_location and (argv.denovo_chrom or argv.denovo_pos):
            print(
                "--denovo-location and (--denovo-chorm, --denovo-pos) "
                "are mutually exclusive"
            )
            raise ValueError()

        if argv.denovo_variant and (argv.denovo_ref or argv.denovo_alt):
            print(
                "--denovo-variant and (denovo-ref, denovo-alt) "
                "are mutually exclusive"
            )
            raise ValueError()

        if argv.denovo_person_id and (
            argv.denovo_family_id or argv.denovo_best_state
        ):
            print(
                "--denovo-person-id and (denovo-family-id, denovo-best-state) "
                "are mutually exclusive"
            )
            raise ValueError()

        if not (
            argv.denovo_location or (argv.denovo_chrom and argv.denovo_pos)
        ):
            argv.denovo_location = "location"

        if not (argv.denovo_variant or (argv.denovo_ref and argv.denovo_alt)):
            argv.denovo_variant = "variant"

        if not (
            argv.denovo_person_id
            or (argv.denovo_family_id and argv.denovo_best_state)
        ):
            argv.denovo_family_id = "familyId"
            argv.denovo_best_state = "bestState"

        if not argv.denovo_location:
            if not argv.denovo_chrom:
                argv.denovo_chrom = "CHROM"
            if not argv.denovo_pos:
                argv.denovo_pos = "POS"

        if not argv.denovo_variant:
            if not argv.denovo_ref:
                argv.denovo_ref = "REF"
            if not argv.denovo_alt:
                argv.denovo_alt = "ALT"

        if not argv.denovo_person_id:
            if not argv.denovo_family_id:
                argv.denovo_family_id = "familyId"
            if not argv.denovo_best_state:
                argv.denovo_best_state = "bestState"

        if argv.denovo_sep is None:
            argv.denovo_sep = "\t"

        params = {
            "denovo_location": argv.denovo_location,
            "denovo_variant": argv.denovo_variant,
            "denovo_chrom": argv.denovo_chrom,
            "denovo_pos": argv.denovo_pos,
            "denovo_ref": argv.denovo_ref,
            "denovo_alt": argv.denovo_alt,
            "denovo_person_id": argv.denovo_person_id,
            "denovo_family_id": argv.denovo_family_id,
            "denovo_best_state": argv.denovo_best_state,
            "add_chrom_prefix": argv.add_chrom_prefix,
            "del_chrom_prefix": argv.del_chrom_prefix,
            "denovo_sep": argv.denovo_sep,
        }

        return argv.denovo_file, params

    @classmethod
    def flexible_denovo_load(
        cls,
        filepath: str,
        genome: GenomicSequence,
        families: FamiliesData,
        denovo_location: Optional[str] = None,
        denovo_variant: Optional[str] = None,
        denovo_chrom: Optional[str] = None,
        denovo_pos: Optional[str] = None,
        denovo_ref: Optional[str] = None,
        denovo_alt: Optional[str] = None,
        denovo_person_id: Optional[str] = None,
        denovo_family_id: Optional[str] = None,
        denovo_best_state: Optional[str] = None,
        denovo_sep: str = "\t",
        adjust_chrom_prefix=None,
        **kwargs,
    ) -> pd.DataFrame:

        """
        Read a text file containing variants in the form
        of delimiter-separted values and produce a dataframe.

        The text file may use different names for the columns
        containing the relevant data - these are specified
        with the provided parameters.

        :param str filepath: The path to the DSV file to read.

        :param genome: A reference genome object.

        :param str denovo_location: The label or index of the column containing
        the CSHL-style location of the variant.

        :param str denovo_variant: The label or index of the column containing
        the CSHL-style representation of the variant.

        :param str denovo_chrom: The label or index of the column containing
        the chromosome upon which the variant is located.

        :param str denovo_pos: The label or index of the column containing the
        position upon which the variant is located.

        :param str denovo_ref: The label or index of the column containing the
        variant's reference allele.

        :param str denovo_alt: The label or index of the column containing the
        variant's alternative allele.

        :param str denovo_person_id: The label or index of the column
        containing either a singular person ID or a comma-separated
        list of person IDs.

        :param str denovo_family_id: The label or index of the column
        containing a singular family ID.

        :param str denovo_best_state: The label or index of the column
        containing the best state for the variant.

        :param str families: An instance of the FamiliesData class for the
        pedigree of the relevant study.

        :type genome: An instance of GenomicSequence.

        :return: Dataframe containing the variants, with the following
        header - 'chrom', 'position', 'reference', 'alternative', 'family_id',
        'genotype'.

        :rtype: An instance of Pandas' DataFrame class.
        """

        assert families is not None
        assert isinstance(
            families, FamiliesData
        ), "families must be an instance of FamiliesData!"
        assert genome, "You must provide a genome object!"

        if not (denovo_location or (denovo_chrom and denovo_pos)):
            denovo_location = "location"

        if not (denovo_variant or (denovo_ref and denovo_alt)):
            denovo_variant = "variant"

        if not (denovo_person_id or (denovo_family_id and denovo_best_state)):
            denovo_family_id = "familyId"
            denovo_best_state = "bestState"

        if denovo_sep is None:
            denovo_sep = "\t"

        raw_df = pd.read_csv(
            filepath,
            sep=denovo_sep,
            dtype={
                denovo_chrom: str,
                denovo_pos: int,
                denovo_person_id: str,
                denovo_family_id: str,
                denovo_best_state: str,
            },
        )

        if denovo_location:
            chrom_col, pos_col = zip(
                *map(cls.split_location, raw_df[denovo_location])
            )
        else:
            chrom_col = raw_df.loc[:, denovo_chrom]
            pos_col = raw_df.loc[:, denovo_pos]

        if adjust_chrom_prefix is not None:
            chrom_col = tuple(map(adjust_chrom_prefix, chrom_col))

        if denovo_variant:
            variant_col = raw_df.loc[:, denovo_variant]
            ref_alt_tuples = [
                dae2vcf_variant(*variant_tuple, genome)
                for variant_tuple in zip(chrom_col, pos_col, variant_col)
            ]
            pos_col, ref_col, alt_col = zip(*ref_alt_tuples)

        else:
            ref_col = raw_df.loc[:, denovo_ref]
            alt_col = raw_df.loc[:, denovo_alt]

        if denovo_person_id:
            temp_df = pd.DataFrame(
                {
                    "chrom": chrom_col,
                    "pos": pos_col,
                    "ref": ref_col,
                    "alt": alt_col,
                    "person_id": raw_df.loc[:, denovo_person_id],
                }
            )

            variant_to_people = dict()
            variant_to_families = dict()

            for variant, variants_indices in temp_df.groupby(
                ["chrom", "pos", "ref", "alt"]
            ).groups.items():
                # Here we join and then split again by ',' to handle cases
                # where the person IDs are actually a list of IDs, separated
                # by a ','
                person_ids = ",".join(
                    temp_df.iloc[variants_indices].loc[:, "person_id"]
                ).split(",")

                variant_to_people[variant] = person_ids
                variant_to_families[
                    variant
                ] = families.families_query_by_person_ids(person_ids)

            # TODO Implement support for multiallelic variants
            result = []
            for variant, families in variant_to_families.items():

                for family_id, family in families.items():
                    result.append(
                        {
                            "chrom": variant[0],
                            "position": variant[1],
                            "reference": variant[2],
                            "alternative": variant[3],
                            "family_id": family_id,
                            "genotype": cls.produce_genotype(
                                variant[0],
                                variant[1],
                                genome,
                                family,
                                variant_to_people[variant],
                            ),
                            "best_state": None,
                        }
                    )

            return pd.DataFrame(result)

        else:
            family_col = raw_df.loc[:, denovo_family_id]

            best_state_col = list(
                map(
                    lambda bs: str2mat(bs, col_sep=" "),  # type: ignore
                    raw_df[denovo_best_state],
                )
            )
            # genotype_col = list(map(best2gt, best_state_col))

            return pd.DataFrame(
                {
                    "chrom": chrom_col,
                    "position": pos_col,
                    "reference": ref_col,
                    "alternative": alt_col,
                    "family_id": family_col,
                    "genotype": None,
                    "best_state": best_state_col,
                }
            )


class DaeTransmittedFamiliesGenotypes(FamiliesGenotypes):
    def __init__(self, families, families_best_states):
        super(DaeTransmittedFamiliesGenotypes, self).__init__()
        self.families = families
        self.families_best_states = families_best_states

    # def get_family_genotype(self, family):
    #     gt = self.families_genotypes.get(family.family_id, None)
    #     if gt is not None:
    #         return gt
    #     else:
    #         # FIXME: what genotype we should return in case
    #         # we have no data in the file:
    #         # - reference
    #         # - unknown
    #         return reference_genotype(len(family))

    def get_family_best_state(self, family):
        return self.families_best_states.get(family.family_id, None)

    def family_genotype_iterator(self):
        for family_id, bs in self.families_best_states.items():
            fam = self.families.get(family_id)
            if fam is None:
                continue
            yield fam, bs

    def full_families_genotypes(self):
        raise NotImplementedError()
        # return self.families_genotypes


class DaeTransmittedLoader(VariantsGenotypesLoader):
    def __init__(
        self,
        families,
        summary_filename,
        genome,
        regions=None,
        params={},
        **kwargs,
    ):

        toomany_filename = DaeTransmittedLoader._build_toomany_filename(
            summary_filename
        )

        super(DaeTransmittedLoader, self).__init__(
            families=families,
            filenames=[summary_filename, toomany_filename,],
            transmission_type=TransmissionType.transmitted,
            genome=genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=True,
            params=params,
        )

        self.summary_filename = summary_filename
        self.toomany_filename = toomany_filename

        self.set_attribute("source_type", "dae")

        self.genome = genome

        self.params = params
        self.include_reference = self.params.get(
            "dae_include_reference_genotypes", False
        )
        try:
            with pysam.Tabixfile(self.summary_filename) as tbx:
                self.chromosomes = list(tbx.contigs)
        except Exception:
            self.chromosomes = self.genome.allChromosomes

    @property
    def variants_filenames(self):
        return [self.summary_filename]

    @staticmethod
    def _build_toomany_filename(summary_filename):
        assert os.path.exists(
            f"{summary_filename}.tbi"
        ), f"summary filename tabix index missing {summary_filename}"

        dirname = os.path.dirname(summary_filename)
        basename = os.path.basename(summary_filename)
        if basename.endswith(".txt.bgz"):
            result = os.path.join(dirname, f"{basename[:-8]}-TOOMANY.txt.bgz")
        elif basename.endswith(".txt.gz"):
            result = os.path.join(dirname, f"{basename[:-7]}-TOOMANY.txt.gz")
        else:
            assert False, (
                f"Bad summary filename {summary_filename}: "
                f"unexpected extention"
            )

        assert os.path.exists(result), f"missing TOOMANY file {result}"
        assert os.path.exists(
            f"{result}.tbi"
        ), f"missing tabix index for TOOMANY file {result}"

        return result

    @staticmethod
    def _rename_columns(columns):
        if "#chr" in columns:
            columns[columns.index("#chr")] = "chrom"
        if "chr" in columns:
            columns[columns.index("chr")] = "chrom"
        if "position" in columns:
            columns[columns.index("position")] = "cshl_position"
        if "variant" in columns:
            columns[columns.index("variant")] = "cshl_variant"
        return columns

    @staticmethod
    def _load_column_names(filename):
        with gzip.open(filename) as infile:
            column_names = (
                infile.readline().decode("utf-8").strip().split("\t")
            )
        return column_names

    @classmethod
    def _load_toomany_columns(cls, toomany_filename):
        toomany_columns = cls._load_column_names(toomany_filename)
        return cls._rename_columns(toomany_columns)

    @classmethod
    def _load_summary_columns(cls, summary_filename):
        summary_columns = cls._load_column_names(summary_filename)
        return cls._rename_columns(summary_columns)

    def _summary_variant_from_dae_record(self, summary_index, rec):
        rec["cshl_position"] = int(rec["cshl_position"])
        position, reference, alternative = dae2vcf_variant(
            self._adjust_chrom_prefix(rec["chrom"]),
            rec["cshl_position"],
            rec["cshl_variant"],
            self.genome,
        )
        rec["position"] = position
        rec["reference"] = reference
        rec["alternative"] = alternative
        rec["all.nParCalled"] = int(rec["all.nParCalled"])
        rec["all.nAltAlls"] = int(rec["all.nAltAlls"])
        rec["all.prcntParCalled"] = float(rec["all.prcntParCalled"])
        rec["all.altFreq"] = float(rec["all.altFreq"])
        rec["summary_variant_index"] = summary_index

        parents_called = int(rec.get("all.nParCalled", 0))
        ref_allele_count = 2 * int(rec.get("all.nParCalled", 0)) - int(
            rec.get("all.nAltAlls", 0)
        )
        ref_allele_prcnt = 0.0
        if parents_called > 0:
            ref_allele_prcnt = ref_allele_count / 2.0 / parents_called
        ref = {
            "chrom": rec["chrom"],
            "position": rec["position"],
            "reference": rec["reference"],
            "alternative": None,
            "variant_type": 0,
            "cshl_position": rec["cshl_position"],
            "cshl_variant": rec["cshl_variant"],
            "summary_variant_index": rec["summary_variant_index"],
            "allele_index": 0,
            "af_parents_called_count": parents_called,
            "af_parents_called_percent": float(
                rec.get("all.prcntParCalled", 0.0)
            ),
            "af_allele_count": ref_allele_count,
            "af_allele_freq": ref_allele_prcnt,
        }

        alt = {
            "chrom": rec["chrom"],
            "position": rec["position"],
            "reference": rec["reference"],
            "alternative": rec["alternative"],
            "variant_type": VariantType.from_cshl_variant(
                rec["cshl_variant"]
            ),
            "cshl_position": rec["cshl_position"],
            "cshl_variant": rec["cshl_variant"],
            "summary_variant_index": rec["summary_variant_index"],
            "allele_index": 1,
            "af_parents_called_count": int(rec.get("all.nParCalled", 0)),
            "af_parents_called_percent": float(
                rec.get("all.prcntParCalled", 0.0)
            ),
            "af_allele_count": int(rec.get("all.nAltAlls", 0)),
            "af_allele_freq": float(rec.get("all.altFreq", 0.0)),
        }
        summary_variant = SummaryVariantFactory.summary_variant_from_records(
            [ref, alt], transmission_type=self.transmission_type
        )
        return summary_variant

    @staticmethod
    def _explode_family_best_states(family_data, col_sep="", row_sep="/"):
        best_states = {
            fid: str2mat(bs, col_sep=col_sep, row_sep=row_sep)
            for (fid, bs) in [
                fg.split(":")[:2] for fg in family_data.split(";")
            ]
        }
        return best_states

    def _full_variants_iterator_impl(self):

        summary_columns = self._load_summary_columns(self.summary_filename)
        toomany_columns = self._load_toomany_columns(self.toomany_filename)

        summary_index = 0
        for region in self.regions:
            # using a context manager because of
            # https://stackoverflow.com/a/25968716/2316754
            with closing(
                pysam.Tabixfile(self.summary_filename)
            ) as sum_tbf, closing(
                pysam.Tabixfile(self.toomany_filename)
            ) as too_tbf:
                summary_iterator = sum_tbf.fetch(
                    region=region, parser=pysam.asTuple()
                )
                toomany_iterator = too_tbf.fetch(
                    region=region, parser=pysam.asTuple()
                )

                for summary_line in summary_iterator:
                    rec = dict(zip(summary_columns, summary_line))

                    summary_variant = self._summary_variant_from_dae_record(
                        summary_index, rec
                    )

                    family_data = rec["familyData"]
                    if family_data == "TOOMANY":
                        toomany_line = next(toomany_iterator)
                        toomany_rec = dict(zip(toomany_columns, toomany_line))
                        family_data = toomany_rec["familyData"]

                        assert rec["cshl_position"] == int(
                            toomany_rec["cshl_position"]
                        )

                    best_states = self._explode_family_best_states(family_data)

                    families_genotypes = DaeTransmittedFamiliesGenotypes(
                        self.families, best_states
                    )

                    family_variants = []
                    for (
                        fam,
                        bs,
                    ) in families_genotypes.family_genotype_iterator():
                        family_variants.append(
                            FamilyVariant(summary_variant, fam, None, bs)
                        )

                    yield summary_variant, family_variants
                    summary_index += 1

    @classmethod
    def cli_defaults(cls):
        return {
            "dae_include_reference_genotypes": False,
            "add_chrom_prefix": None,
            "del_chrom_prefix": None,
        }

    @classmethod
    def build_cli_arguments(cls, params):
        param_defaults = DaeTransmittedLoader.cli_defaults()
        result = []
        for key, value in params.items():
            assert key in param_defaults, (key, list(param_defaults.keys()))
            if value != param_defaults[key]:
                param = key.replace("_", "-")
                if key in ("dae_include_reference_genotypes"):
                    if value:
                        result.append(f"--{param}")
                else:
                    result.append(f"--{param}")
                    result.append(f"{value}")
        return " ".join(result)

    @classmethod
    def cli_arguments(cls, parser):
        parser.add_argument(
            "dae_summary_file",
            type=str,
            metavar="<summary filename>",
            help="summary variants file to import",
        )
        cls.cli_options(parser)

    @classmethod
    def cli_options(cls, parser):
        parser.add_argument(
            "--dae-include-reference-genotypes",
            default=False,
            dest="dae_include_reference_genotypes",
            help="fill in reference only variants [default: %(default)s]",
            action="store_true",
        )

        parser.add_argument(
            "--add-chrom-prefix",
            type=str,
            default=None,
            help="Add specified prefix to each chromosome name in "
            "variants file",
        )
        parser.add_argument(
            "--del-chrom-prefix",
            type=str,
            default=None,
            help="Removes specified prefix from each chromosome name in "
            "variants file",
        )

    @classmethod
    def parse_cli_arguments(cls, argv):
        filename = argv.dae_summary_file

        params = {
            "dae_include_reference_genotypes": str2bool(
                argv.dae_include_reference_genotypes
            ),
            "add_chrom_prefix": argv.add_chrom_prefix,
            "del_chrom_prefix": argv.del_chrom_prefix,
        }
        return filename, params
