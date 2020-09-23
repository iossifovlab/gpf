import os
import pathlib
import sys
import time
import copy
import numpy as np
import pandas as pd

from typing import Iterator, Tuple, List, Dict, Any, Optional, Sequence

from dae.genome.genomes_db import Genome

from dae.pedigrees.family import FamiliesData

from dae.variants.variant import SummaryVariant
from dae.variants.family_variant import (
    FamilyVariant,
    calculate_simple_best_state,
)
from dae.variants.attributes import Sex, GeneticModel

from dae.variants.attributes import TransmissionType

from dae.utils.variant_utils import get_locus_ploidy, best2gt


class FamiliesGenotypes:
    def __init__(self):
        pass

    def full_families_genotypes(self):
        raise NotImplementedError()

    def get_family_genotype(self, family):
        raise NotImplementedError()

    def get_family_best_state(self, family):
        raise NotImplementedError()

    def family_genotype_iterator(self):
        raise NotImplementedError()


class VariantsLoader:
    def __init__(
        self,
        families: FamiliesData,
        filenames: List[str],
        transmission_type: TransmissionType,
        params: Dict[str, Any] = {},
        attributes: Optional[Dict[str, Any]] = None,
    ):

        assert isinstance(families, FamiliesData)
        self.families = families
        assert all([os.path.exists(fn) for fn in filenames]), filenames
        self.filenames = filenames

        assert isinstance(transmission_type, TransmissionType)
        self.transmission_type = transmission_type
        self.params = params
        if attributes is None:
            self._attributes = {}
        else:
            self._attributes = copy.deepcopy(attributes)

    # @property
    # def variants_filenames(self):
    #     return self.filenames

    def full_variants_iterator(self):
        raise NotImplementedError()

    def family_variants_iterator(self):
        for _, fvs in self.full_variants_iterator():
            for fv in fvs:
                yield fv

    def get_attribute(self, key: str) -> Any:
        return self._attributes.get(key, None)

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value


class VariantsLoaderDecorator(VariantsLoader):
    def __init__(self, variants_loader: VariantsLoader):

        super(VariantsLoaderDecorator, self).__init__(
            variants_loader.families,
            variants_loader.filenames,
            variants_loader.transmission_type,
            params=variants_loader.params,
            attributes=variants_loader._attributes,
        )
        self.variants_loader = variants_loader

    def get_attribute(self, key: str) -> Any:
        result = self._attributes.get(key, None)
        if result is not None:
            return result

        return self.variants_loader.get_attribute(key)

    def __getattr__(self, attr):
        return getattr(self.variants_loader, attr, None)


class AnnotationDecorator(VariantsLoaderDecorator):

    SEP1 = "!"
    SEP2 = "|"
    SEP3 = ":"

    CLEAN_UP_COLUMNS = set(
        [
            "alternatives_data",
            "family_variant_index",
            "family_id",
            "variant_sexes",
            "variant_roles",
            "variant_inheritance",
            "variant_in_member",
            "genotype_data",
            "best_state_data",
            "genetic_model_data",
            "inheritance_data",
            "frequency_data",
            "genomic_scores_data",
            "effect_type",
            "effect_gene",
        ]
    )

    def __init__(self, variants_loader):
        super(AnnotationDecorator, self).__init__(variants_loader)

    @staticmethod
    def build_annotation_filename(filename):
        path = pathlib.Path(filename)
        suffixes = path.suffixes

        if not suffixes:
            return f"{filename}-eff.txt"
        else:
            suffix = "".join(suffixes)
            replace_with = suffix.replace(".", "-")
            filename = filename.replace(suffix, replace_with)

            return f"{filename}-eff.txt"

    @staticmethod
    def has_annotation_file(annotation_filename):
        return os.path.exists(annotation_filename)

    @staticmethod
    def save_annotation_file(variants_loader, filename, sep="\t"):
        # def convert_array_of_strings_to_string(a):
        #     if not a:
        #         return None
        #     return AnnotationDecorator.SEP1.join(a)

        common_columns = [
            "chrom",
            "position",
            "reference",
            "alternative",
            "bucket_index",
            "summary_variant_index",
            "allele_index",
            "allele_count",
        ]

        if variants_loader.annotation_schema is not None:
            other_columns = list(
                filter(
                    lambda col: col not in common_columns
                    and col not in AnnotationDecorator.CLEAN_UP_COLUMNS,
                    variants_loader.annotation_schema.col_names,
                )
            )
        else:
            other_columns = []

        header = common_columns[:]
        header.extend(["effects"])
        header.extend(other_columns)

        with open(filename, "w") as outfile:
            outfile.write(sep.join(header))
            outfile.write("\n")

            for summary_variant, _ in variants_loader.full_variants_iterator():
                for allele_index, summary_allele in enumerate(
                    summary_variant.alleles
                ):
                    line = []
                    rec = summary_allele.attributes
                    rec["allele_index"] = allele_index

                    line_values = [
                        *[rec.get(col, "") for col in common_columns],
                        summary_allele.effect,
                        *[rec.get(col, "") for col in other_columns],
                    ]

                    for value in line_values:
                        line.append(str(value) if value is not None else "")

                    outfile.write(sep.join(line))
                    outfile.write("\n")


class AnnotationPipelineDecorator(AnnotationDecorator):
    def __init__(self, variants_loader, annotation_pipeline):
        super(AnnotationPipelineDecorator, self).__init__(variants_loader)

        self.annotation_pipeline = annotation_pipeline
        self.annotation_schema = annotation_pipeline.build_annotation_schema()
        self.set_attribute("annotation_schema", self.annotation_schema)

    def full_variants_iterator(self):
        for (summary_variant, family_variants) in \
                self.variants_loader.full_variants_iterator():

            self.annotation_pipeline.annotate_summary_variant(summary_variant)
            yield summary_variant, family_variants


class StoredAnnotationDecorator(AnnotationDecorator):
    def __init__(self, variants_loader, annotation_filename):
        super(StoredAnnotationDecorator, self).__init__(variants_loader)

        assert os.path.exists(annotation_filename)
        self.annotation_filename = annotation_filename

    @staticmethod
    def decorate(variants_loader, source_filename):
        annotation_filename = StoredAnnotationDecorator \
            .build_annotation_filename(
                source_filename
            )
        # assert os.path.exists(annotation_filename), \
        #     annotation_filename
        if not os.path.exists(annotation_filename):
            return variants_loader
        else:
            variants_loader = StoredAnnotationDecorator(
                variants_loader, annotation_filename
            )
            return variants_loader

    @classmethod
    def _convert_array_of_strings(cls, token):
        if not token:
            return None
        token = token.strip()
        words = [w.strip() for w in token.split(cls.SEP1)]
        return words

    @staticmethod
    def _convert_string(token):
        if not token:
            return None
        return token

    @classmethod
    def _load_annotation_file(cls, filename, sep="\t"):
        assert os.path.exists(filename)
        with open(filename, "r") as infile:
            annot_df = pd.read_csv(
                infile,
                sep=sep,
                index_col=False,
                dtype={
                    "chrom": str,
                    "position": np.int32,
                    # 'effects': str,
                },
                converters={
                    "cshl_variant": cls._convert_string,
                    "effects": cls._convert_string,
                    "effect_gene_genes": cls._convert_array_of_strings,
                    "effect_gene_types": cls._convert_array_of_strings,
                    "effect_details_transcript_ids":
                    cls._convert_array_of_strings,
                    "effect_details_details": cls._convert_array_of_strings,
                },
                encoding="utf-8",
            )
        special_columns = set(annot_df.columns) & set(
            ["alternative", "effect_type"]
        )
        for col in special_columns:
            annot_df[col] = (
                annot_df[col]
                .astype(object)
                .where(pd.notnull(annot_df[col]), None)
            )
        return annot_df

    def full_variants_iterator(self):
        variant_iterator = self.variants_loader.full_variants_iterator()
        start = time.time()
        annot_df = self._load_annotation_file(self.annotation_filename)
        elapsed = time.time() - start
        print(
            f"Storred annotation file loaded in in {elapsed:.2f} sec",
            file=sys.stderr,
        )

        start = time.time()
        records = annot_df.to_dict(orient="records")
        index = 0

        while index < len(records):
            sv, family_variants = next(variant_iterator)
            variant_records = []

            current_record = records[index]
            while current_record["summary_variant_index"] == sv.summary_index:
                variant_records.append(current_record)
                index += 1
                if index >= len(records):
                    break
                current_record = records[index]

            assert len(variant_records) > 0, sv

            for sa in sv.alleles:
                sa.update_attributes(variant_records[sa.allele_index])
            yield sv, family_variants

        elapsed = time.time() - start
        print(
            f"Storred annotation file parsed in {elapsed:.2f} sec",
            file=sys.stderr,
        )


class VariantsGenotypesLoader(VariantsLoader):
    """
    Calculate missing best states and adds a genetic model
    value to the family variant and its alleles.
    """

    def __init__(
            self,
            families: FamiliesData,
            filenames: List[str],
            transmission_type: TransmissionType,
            genome: Genome,
            regions: List[str] = None,
            expect_genotype: bool = True,
            expect_best_state: bool = False,
            params: Dict[str, Any] = {}):

        super(VariantsGenotypesLoader, self).__init__(
            families=families,
            filenames=filenames,
            transmission_type=transmission_type,
            params=params)

        self.genome = genome

        self.regions: Sequence[Optional[str]]
        if regions is None or isinstance(regions, str):
            self.regions = [regions]
        else:
            self.regions = regions

        self._adjust_chrom_prefix = lambda chrom: chrom
        if params.get("add_chrom_prefix", None):
            self._chrom_prefix = params["add_chrom_prefix"]
            self._adjust_chrom_prefix = self._add_chrom_prefix
        elif params.get("del_chrom_prefix", None):
            self._chrom_prefix = params["del_chrom_prefix"]
            self._adjust_chrom_prefix = self._del_chrom_prefix

        self.expect_genotype = expect_genotype
        self.expect_best_state = expect_best_state

    @property
    def variants_filenames(self):
        return self.filenames

    def _full_variants_iterator_impl(self):
        raise NotImplementedError()

    def reset_regions(self, regions):
        # print("resetting regions to:", regions)
        if regions is None or isinstance(regions, str):
            self.regions = [regions]
        else:
            self.regions = regions

    @classmethod
    def _get_diploid_males(cls, family_variant: FamilyVariant) -> List[bool]:
        res = []

        assert family_variant.gt.shape == (2, len(family_variant.family))

        for member_idx, member in enumerate(
            family_variant.family.members_in_order
        ):
            if member.sex in (Sex.F, Sex.U):
                continue
            res.append(bool(family_variant.gt[1, member_idx] != -2))
        return res

    @classmethod
    def _calc_genetic_model(
        cls, family_variant: FamilyVariant, genome: Genome
    ) -> GeneticModel:
        if family_variant.chromosome in ("X", "chrX"):
            male_ploidy = get_locus_ploidy(
                family_variant.chromosome,
                family_variant.position,
                Sex.M,
                genome,
            )
            if male_ploidy == 2:
                if not all(cls._get_diploid_males(family_variant)):
                    return GeneticModel.X_broken
                else:
                    return GeneticModel.pseudo_autosomal
            elif any(cls._get_diploid_males(family_variant)):
                return GeneticModel.X_broken
            else:
                return GeneticModel.X
        else:
            # We currently assume all other chromosomes are autosomal
            return GeneticModel.autosomal

    @classmethod
    def _calc_best_state(
        cls,
        family_variant: FamilyVariant,
        genome: Genome,
        force: bool = True,
    ) -> np.array:

        male_ploidy = get_locus_ploidy(
            family_variant.chromosome, family_variant.position, Sex.M, genome
        )

        if family_variant.chromosome in ("X", "chrX") and male_ploidy == 1:
            best_state = calculate_simple_best_state(
                family_variant.gt, family_variant.allele_count
            )
            male_ids = [
                person_id
                for person_id, person in family_variant.family.persons.items()
                if person.sex == Sex.M
            ]
            male_indices = family_variant.family.members_index(male_ids)
            for idx in male_indices:
                # A male with a haploid genotype for X cannot
                # have two alternative alleles, therefore there
                # must be one or two reference alleles left over
                # from the simple best state calculation
                if best_state[0, idx] in (1, 2):
                    best_state[0, idx] -= 1
                elif np.any(best_state[:, idx] == 2):
                    best_state[best_state[:, idx] == 2, idx] -= 1
                # else:
                #     print(
                #         "WARN: can't handle broken X best state:",
                #         family_variant, mat2str(family_variant.gt),
                #         file=sys.stderr)

            return best_state
        elif force:
            return calculate_simple_best_state(
                family_variant.gt, family_variant.allele_count
            )

    @classmethod
    def _calc_genotype(
        cls, family_variant: FamilyVariant, genome: Genome
    ) -> np.array:
        best_state = family_variant._best_state
        genotype = best2gt(best_state)
        male_ploidy = get_locus_ploidy(
            family_variant.chromosome, family_variant.position, Sex.M, genome
        )
        ploidy = np.sum(best_state, 0)
        genetic_model = GeneticModel.autosomal

        if family_variant.chromosome in ("X", "chrX"):
            genetic_model = GeneticModel.X
            if male_ploidy == 2:
                genetic_model = GeneticModel.pseudo_autosomal

            male_ids = [
                person_id
                for person_id, person in family_variant.family.persons.items()
                if person.sex == Sex.M
            ]
            male_indices = family_variant.family.members_index(male_ids)
            for idx in male_indices:
                if ploidy[idx] != male_ploidy:
                    genetic_model = GeneticModel.X_broken
                    break

        elif np.any(ploidy == 1):
            genetic_model = GeneticModel.autosomal_broken

        return genotype, genetic_model

    def _add_chrom_prefix(self, chrom):
        assert self._chrom_prefix is not None
        if self._chrom_prefix not in chrom:
            return f"{self._chrom_prefix}{chrom}"
        else:
            return chrom

    def _del_chrom_prefix(self, chrom):
        assert self._chrom_prefix is not None
        if self._chrom_prefix in chrom:
            return chrom[len(self._chrom_prefix):]
        else:
            return chrom

    def full_variants_iterator(
        self,
    ) -> Iterator[Tuple[SummaryVariant, List[FamilyVariant]]]:
        full_iterator = self._full_variants_iterator_impl()
        for summary_variant, family_variants in full_iterator:
            chrom = self._adjust_chrom_prefix(summary_variant.chromosome)
            summary_variant._chromosome = chrom
            for summary_allele in summary_variant.alleles:
                summary_allele._chromosome = chrom
                summary_allele._attributes["chrom"] = chrom

            for family_variant in family_variants:

                if self.expect_genotype:
                    assert family_variant._best_state is None
                    assert family_variant._genetic_model is None
                    assert family_variant.gt is not None

                    family_variant._genetic_model = self._calc_genetic_model(
                        family_variant, self.genome
                    )

                    family_variant._best_state = self._calc_best_state(
                        family_variant, self.genome, force=False
                    )
                    for fa in family_variant.alleles:
                        fa._best_state = family_variant.best_state
                        fa._genetic_model = family_variant.genetic_model
                elif self.expect_best_state:
                    assert family_variant._best_state is not None
                    assert family_variant._genetic_model is None
                    assert family_variant.gt is None

                    (
                        family_variant.gt,
                        family_variant._genetic_model,
                    ) = self._calc_genotype(family_variant, self.genome)
                    for fa in family_variant.alleles:
                        fa.gt = family_variant.gt
                        fa._genetic_model = family_variant.genetic_model

            yield summary_variant, family_variants

    @classmethod
    def build_cli_params(cls, params):
        param_defaults = cls.cli_defaults()
        result = {}
        for key, value in params.items():
            assert key in param_defaults, (key, list(param_defaults.keys()))
            if value != param_defaults[key]:
                if value is None:
                    result[key] = ""
                else:
                    result[key] = f"{value}"

        return result

    @classmethod
    def cli_options(cls, parser):
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
            "add_chrom_prefix": None,
            "del_chrom_prefix": None,
        }
