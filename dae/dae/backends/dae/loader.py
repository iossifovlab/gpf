import os
import gzip
import sys
import warnings

from typing import List, Optional, Dict, Any
from contextlib import closing

import pysam
import numpy as np
import pandas as pd

from dae.utils.regions import Region

from dae.genome.genomes_db import Genome
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
    CLIArgument
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
            genome: Genome,
            regions: List[str] = None,
            params: Dict[str, Any] = {}):
        super(DenovoLoader, self).__init__(
            families=families,
            filenames=[denovo_filename],
            transmission_type=TransmissionType.denovo,
            genome=genome,
            regions=regions,
            expect_genotype=False,
            expect_best_state=False,
            params=params)

        self.genome = genome
        self.set_attribute("source_type", "denovo")

        self.denovo_df, extra_attributes = self._flexible_denovo_load_internal(
            denovo_filename,
            genome,
            families=families,
            adjust_chrom_prefix=self._adjust_chrom_prefix,
            **self.params,
        )
        self.set_attribute("extra_attributes", extra_attributes)
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

        all_chromosomes = self.genome.get_genomic_sequence().chromosomes
        if all([chrom in set(all_chromosomes) for chrom in self.chromosomes]):
            self.chromosomes = sorted(
                self.chromosomes,
                key=lambda chrom: all_chromosomes.index(chrom),
            )

    def reset_regions(self, regions):
        super(DenovoLoader, self).reset_regions(regions)

        result = []
        for r in self.regions:
            if r is None:
                result.append(r)
            else:
                result.append(Region.from_str(r))
        self.regions = result
        print("denovo reset regions:", self.regions)

    def _is_in_regions(self, summary_variant):
        isin = [
            r.isin(summary_variant.chrom, summary_variant.position)
            if r is not None
            else True
            for r in self.regions
        ]
        return any(isin)

    def _full_variants_iterator_impl(self):
        for region in self.regions:
            if region is None:
                continue
            region.chrom = self._adjust_chrom_prefix(region.chrom)

        print(self.denovo_df)
        group = self.denovo_df.groupby(
            ["chrom", "position", "reference", "alternative"],
            sort=False).agg(
                lambda x: list(x)
            )
        for num_idx, (idx, values) in enumerate(group.iterrows()):
            chrom, position, reference, alternative = idx
            position = int(position)
            summary_rec = {
                "chrom": chrom,
                "reference": reference,
                "alternative": alternative,
                "position": position,
                "summary_variant_index": num_idx,
                "allele_index": 1
            }

            sv = SummaryVariantFactory.summary_variant_from_records(
                [summary_rec], self.transmission_type
            )

            if not self._is_in_regions(sv):
                continue

            fvs = []
            extra_attributes_keys = list(filter(
                lambda x: x not in ["best_state", "family_id", "genotype"],
                values.keys()
            ))
            for f_idx, family_id in enumerate(values.get("family_id")):
                best_state = values.get("best_state")[f_idx]
                gt = values.get("genotype")[f_idx]
                family = self.families.get(family_id)
                if family is None:
                    continue
                family_genotypes = DenovoFamiliesGenotypes(
                    family, gt, best_state)
                for fam, gt, bs in family_genotypes.family_genotype_iterator():
                    fv = FamilyVariant(sv, fam, gt, bs)
                    extra_attributes = {}
                    for attr in extra_attributes_keys:
                        attr_val = values.get(attr)[f_idx]
                        extra_attributes[attr] = [attr_val]
                    if gt is None:
                        fv.gt, fv._genetic_model = self._calc_genotype(
                            fv, self.genome)
                        for fa in fv.alleles:
                            fa.gt = fv.gt
                            fa._genetic_model = fv.genetic_model
                    fv.update_attributes(extra_attributes)
                    fvs.append(fv)
            yield sv, fvs

    def full_variants_iterator(self):
        full_iterator = super(DenovoLoader, self).full_variants_iterator()
        for summary_variants, family_variants in full_iterator:
            for fv in family_variants:
                for fa in fv.alt_alleles:
                    inheritance = [
                        Inheritance.denovo if mem is not None else inh
                        for inh, mem in zip(
                            fa.inheritance_in_members, fa.variant_in_members
                        )
                    ]
                    fa._inheritance_in_members = inheritance

            yield summary_variants, family_variants

    @staticmethod
    def split_location(location):
        chrom, position = location.split(":")
        return chrom, int(position)

    @staticmethod
    def produce_genotype(
        chrom: str,
        pos: int,
        genome: Genome,
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
    def _arguments(cls):
        arguments = super()._arguments()
        arguments.append(CLIArgument(
            "denovo_file",
            value_type=str,
            metavar="<variants filename>",
            help_text="DAE denovo variants file",
        ))
        arguments.append(CLIArgument(
            "--denovo-variant",
            help_text="The label or index of the"
            " column containing the CSHL-style"
            " representation of the variant."
            "[Default: variant]",
        ))
        arguments.append(CLIArgument(
            "--denovo-ref",
            help_text="The label or index of the"
            " column containing the reference"
            " allele for the variant. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-alt",
            help_text="The label or index of the "
            " column containing the alternative"
            " allele for the variant. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-location",
            # default_value="location",
            help_text="The label or index of the"
            " column containing the CSHL-style"
            " location of the variant. [Default: location]",
        ))
        arguments.append(CLIArgument(
            "--denovo-chrom",
            help_text="The label or index of the"
            " column containing the chromosome"
            " upon which the variant is located. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-pos",
            help_text="The label or index of the"
            " column containing the position"
            " upon which the variant is located. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-family-id",
            # default_value="familyId",
            help_text="The label or index of the column containing the"
            " family's ID. [Default: familyId]",
        ))
        arguments.append(CLIArgument(
            "--denovo-best-state",
            # default_value="bestState",
            help_text="The label or index of the"
            " column containing the best state"
            " for the family. [Default: bestState]",
        ))
        arguments.append(CLIArgument(
            "--denovo-person-id",
            help_text="The label or index of the column containing the"
            " person's ID. [Default: none]",
        ))
        arguments.append(CLIArgument(
            "--denovo-sep",
            value_type=str,
            default_value="\t",
            help_text="Denovo file field separator [default: `\\t`]",
        ))
        return arguments

    @classmethod
    def parse_cli_arguments(cls, argv):
        print(argv)

        if argv.denovo_location and (argv.denovo_chrom or argv.denovo_pos):
            print(
                "--denovo-location and (--denovo-chrom, --denovo-pos) "
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
                argv.denovo_family_id or argv.denovo_best_state):
            print(
                "--denovo-person-id and (denovo-family-id, denovo-best-state) "
                "are mutually exclusive"
            )
            raise ValueError()

        if not (argv.denovo_location or
                (argv.denovo_chrom and argv.denovo_pos)):
            argv.denovo_location = "location"

        if not (argv.denovo_variant or (argv.denovo_ref and argv.denovo_alt)):
            argv.denovo_variant = "variant"

        if not (argv.denovo_person_id or
                (argv.denovo_family_id and argv.denovo_best_state)):
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
    def _flexible_denovo_load_internal(
            cls,
            filepath: str,
            genome: Genome,
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
            **kwargs) -> pd.DataFrame:
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

        :type genome: An instance of Genome.

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

        with warnings.catch_warnings(record=True) as _:
            warnings.filterwarnings(
                "ignore",
                category=pd.errors.ParserWarning,
                message="Both a converter and dtype were specified",
            )

            raw_df = pd.read_csv(
                filepath,
                sep=denovo_sep,
                converters={
                    denovo_pos: lambda p: int(p) if p else None,
                },
                dtype=str,
                comment="#",
                encoding="utf-8",
                na_filter=False)

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
                dae2vcf_variant(
                    variant_tuple[0], variant_tuple[1], variant_tuple[2],
                    genome.get_genomic_sequence()
                ) for variant_tuple in zip(chrom_col, pos_col, variant_col)
            ]
            pos_col, ref_col, alt_col = zip(*ref_alt_tuples)

        else:
            ref_col = raw_df.loc[:, denovo_ref]
            alt_col = raw_df.loc[:, denovo_alt]

        extra_attributes_cols = raw_df.columns.difference([
            denovo_location, denovo_variant, denovo_chrom, denovo_pos,
            denovo_ref, denovo_alt, denovo_person_id, denovo_family_id,
            denovo_best_state,
        ])

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

            grouped = temp_df.groupby(["chrom", "pos", "ref", "alt"])

            result = []

            # TODO Implement support for multiallelic variants
            for variant, variants_indices in grouped.groups.items():
                # Here we join and then split again by ',' to handle cases
                # where the person IDs are actually a list of IDs, separated
                # by a ','
                person_ids = ",".join(
                    temp_df.iloc[variants_indices].loc[:, "person_id"]
                ).split(",")

                variant_families = families.families_query_by_person_ids(
                    person_ids)

                # TODO Implement support for multiallelic variants

                for family_id, family in variant_families.items():
                    family_dict = {
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
                            person_ids,
                        ),
                        "best_state": None,
                    }
                    record = raw_df.loc[variants_indices[0]]
                    extra_attributes = record[extra_attributes_cols].to_dict()

                    result.append({**family_dict, **extra_attributes})

            denovo_df = pd.DataFrame(result)

        else:
            family_col = raw_df.loc[:, denovo_family_id]

            best_state_col = list(
                map(
                    lambda bs: str2mat(bs, col_sep=" "),  # type: ignore
                    raw_df[denovo_best_state],
                )
            )
            # genotype_col = list(map(best2gt, best_state_col))

            denovo_df = pd.DataFrame(
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

            extra_attributes_df = raw_df[extra_attributes_cols]
            denovo_df = denovo_df.join(extra_attributes_df)

        return (denovo_df, extra_attributes_cols.tolist())

    @classmethod
    def flexible_denovo_load(
            cls,
            filepath: str,
            genome: Genome,
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
            **kwargs) -> pd.DataFrame:
        denovo_df, _ = cls._flexible_denovo_load_internal(
            filepath,
            genome,
            families,
            denovo_location,
            denovo_variant,
            denovo_chrom,
            denovo_pos,
            denovo_ref,
            denovo_alt,
            denovo_person_id,
            denovo_family_id,
            denovo_best_state,
            denovo_sep,
            adjust_chrom_prefix,
            **kwargs
        )
        return denovo_df


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
            filenames=[summary_filename, toomany_filename],
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
            self.chromosomes = self.genome.chromosomes

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
            self.genome.get_genomic_sequence(),
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
            "variant_type": None,
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
            "variant_type": VariantType.from_cshl_variant(rec["cshl_variant"]),
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
            try:
                # using a context manager because of
                # https://stackoverflow.com/a/25968716/2316754
                with closing(pysam.Tabixfile(self.summary_filename)) \
                        as sum_tbf, \
                        closing(pysam.Tabixfile(self.toomany_filename)) \
                        as too_tbf:

                    summary_iterator = sum_tbf.fetch(
                        region=region, parser=pysam.asTuple()
                    )
                    toomany_iterator = too_tbf.fetch(
                        region=region, parser=pysam.asTuple()
                    )

                    for summary_line in summary_iterator:
                        rec = dict(zip(summary_columns, summary_line))

                        summary_variant = \
                            self._summary_variant_from_dae_record(
                                summary_index, rec)

                        family_data = rec["familyData"]
                        if family_data == "TOOMANY":
                            toomany_line = next(toomany_iterator)
                            toomany_rec = dict(zip(
                                toomany_columns, toomany_line))
                            family_data = toomany_rec["familyData"]

                            assert rec["cshl_position"] == int(
                                toomany_rec["cshl_position"]
                            )

                        best_states = self._explode_family_best_states(
                            family_data)

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
            except ValueError as ex:
                print(
                    f"could not find region {region} in "
                    f"{self.summary_filename} "
                    f"or {self.toomany_filename}:",
                    ex, file=sys.stderr)

            self.lines_iterator = None

    @classmethod
    def _arguments(cls):
        arguments = super()._arguments()
        arguments.append(CLIArgument(
            "dae_summary_file",
            value_type=str,
            metavar="<summary filename>",
            help_text="summary variants file to import",
        ))
        arguments.append(CLIArgument(
            "--dae-include-reference-genotypes",
            default_value=False,
            help_text="fill in reference only variants [default: %(default)s]",
            action="store_true",
        ))
        return arguments

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
