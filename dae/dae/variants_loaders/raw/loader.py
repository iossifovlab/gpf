"""Base classes and helpers for variant loaders."""

import argparse
import os
import pathlib
import time
import copy
import logging

from abc import ABC, abstractmethod
from enum import Enum

from typing import Iterator, Tuple, List, Dict, Any, Optional, Sequence

import numpy as np
import pandas as pd
from dae.annotation.annotation_pipeline import AnnotationPipeline

from dae.genomic_resources.reference_genome import ReferenceGenome

from dae.pedigrees.family import FamiliesData

from dae.effect_annotation.effect import AlleleEffects
from dae.variants.variant import SummaryVariant
from dae.variants.family_variant import (
    FamilyVariant,
    calculate_simple_best_state,
)
from dae.variants.attributes import Sex, GeneticModel
from dae.variants.attributes import TransmissionType
from dae.utils.variant_utils import get_locus_ploidy, best2gt


logger = logging.getLogger(__name__)


class ArgumentType(Enum):
    ARGUMENT = 1
    OPTION = 2


class CLIArgument:
    """Defines class for handling CLI arguments in variant loaders.

    This class handles the logic for CLI argument operations such as parsing
    arguments, transforming to dict, transforming a parsed argument back to
    a CLI argument and adding itself to an existing ArgumentParser.
    Construction closely mirrors the ArgumentParser argument format.
    """

    def __init__(
            self, argument_name, has_value=True,
            default_value=None, destination=None,
            help_text=None, action=None, value_type=None,
            metavar=None, nargs=None, raw=False):
        self.argument_name = argument_name
        self.has_value = has_value
        self.default_value = default_value
        self.destination = destination
        self.value_type = value_type
        self.metavar = metavar
        self.help_text = help_text
        self.nargs = nargs
        self.action = action
        self.raw = raw
        self.arg_type = ArgumentType.OPTION

        if destination is None:
            self.destination = self._default_destination()

    def __repr__(self):
        return f"{self.argument_name} ({self.arg_type})"

    def _default_destination(self):
        if self.argument_name.startswith("--"):
            self.arg_type = ArgumentType.OPTION
        else:
            self.arg_type = ArgumentType.ARGUMENT
            return None
        return self.argument_name[2:].replace("-", "_")

    def add_to_parser(self, parser):
        """Add this argument to argsparser."""
        kwargs = {
            "type": self.value_type,
            "help": self.help_text,
            "default": self.default_value
        }
        if self.arg_type == ArgumentType.OPTION:
            kwargs["dest"] = self.destination
        if self.action:
            # TODO:
            # For some reason kwargs["type"] = self.value_type gets tuple-ized
            # should find a different workaround
            del kwargs["type"]
            kwargs["action"] = self.action
        else:
            kwargs["metavar"] = self.metavar
            kwargs["nargs"] = self.nargs

        parser.add_argument(self.argument_name, **kwargs)

    def build_option(self, params, use_defaults=False) -> Optional[str]:
        """Build an option."""
        if self.arg_type == ArgumentType.ARGUMENT:
            return None
        for key, value in params.items():
            if key == self.destination:
                if self.has_value:
                    if value is not None:
                        if value == self.default_value:
                            continue
                        if self.raw:
                            value = value.encode("unicode-escape")\
                                .decode().replace("\\\\", "\\")
                        return f'{self.argument_name} "{value}"'
                    if use_defaults and self.default_value is not None:
                        value = self.default_value
                        if self.raw:
                            value = value.encode("unicode-escape")\
                                .decode().replace("\\\\", "\\")
                        return f'{self.argument_name} "{value}"'
                else:
                    return f"{self.argument_name}"
        return None

    def parse_cli_argument(self, argv, use_defaults=False):
        if self.destination not in argv:
            return
        argument = getattr(argv, self.destination)
        if argument is None:
            if self.default_value is not None and use_defaults:
                setattr(argv, self.destination, self.default_value)


class FamiliesGenotypes(ABC):
    """A base class for family genotypes."""

    def __init__(self):
        pass

    @abstractmethod
    def full_families_genotypes(self):
        pass

    @abstractmethod
    def get_family_genotype(self, family):
        pass

    @abstractmethod
    def get_family_best_state(self, family):
        pass

    @abstractmethod
    def family_genotype_iterator(self):
        pass


class CLILoader(ABC):
    """Base class for loader classes that require cli arguments."""

    def __init__(self, params=None):
        self.arguments = self._arguments()
        self.params: Dict[str, Any] = params if params else {}

    def _add_argument(self, argument):
        self.arguments.append(argument)

    @classmethod
    def _arguments(cls) -> List[CLIArgument]:
        return []

    @classmethod
    def cli_defaults(cls):
        argument_destinations = [arg.destination for arg in cls._arguments()]
        defaults = [arg.default_value for arg in cls._arguments()]
        return dict(zip(argument_destinations, defaults))

    @classmethod
    def cli_arguments(cls, parser, options_only=False):
        for argument in cls._arguments():
            if options_only and argument.arg_type == ArgumentType.ARGUMENT:
                continue
            argument.add_to_parser(parser)

    @classmethod
    def build_cli_arguments(cls, params) -> str:
        """Return a string with cli arguments."""
        built_arguments = []
        for argument in cls._arguments():
            logger.info("adding to CLI arguments: %s", argument)
            built_arguments.append(argument.build_option(params))
        nonnull_arguments = (x for x in built_arguments if x is not None)
        result = " ".join(nonnull_arguments)
        logger.info("result CLI arguments: %s", result)
        return result

    def build_arguments_dict(self):
        """Build a dictionary with the argument destinations as keys."""
        result = {}
        for argument in self._arguments():
            if argument.arg_type == ArgumentType.ARGUMENT:
                continue
            if argument.destination in self.params:
                result[argument.destination] = \
                    self.params[argument.destination]
        logger.debug(
            "building arguments from %s into dict: %s", self.params, result)
        return result

    @classmethod
    def parse_cli_arguments(
            cls, argv: argparse.Namespace,
            use_defaults=False) -> Tuple[str, Dict[str, Any]]:
        """Parse cli arguments."""
        for arg in cls._arguments():
            arg.parse_cli_argument(argv, use_defaults=use_defaults)
        return "", {}


class VariantsLoader(CLILoader):
    """Base class for all variant loaders."""

    def __init__(
        self,
        families: FamiliesData,
        filenames: List[str],
        transmission_type: TransmissionType,
        params: Optional[Dict[str, Any]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        params = params if params else {}
        super().__init__(params=params)
        assert isinstance(families, FamiliesData)
        self.families = families
        self.filenames = filenames

        assert isinstance(transmission_type, TransmissionType)
        self.transmission_type = transmission_type
        if attributes is None:
            self._attributes = {}
        else:
            self._attributes = copy.deepcopy(attributes)
        self.arguments = []

    def get_attribute(self, key: str) -> Any:
        return self._attributes.get(key, None)

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def reset_regions(self, regions) -> None:
        pass

    @property
    def annotation_schema(self):
        return None

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
        return []

    @abstractmethod
    def full_variants_iterator(self):
        pass

    def family_variants_iterator(self):
        for _, fvs in self.full_variants_iterator():
            for fvariant in fvs:
                yield fvariant

    @abstractmethod
    def close(self):
        """Close resources used by the loader."""


class VariantsLoaderDecorator(VariantsLoader):
    """Base class for wrapping and decoring a variant loader."""

    def __init__(self, variants_loader: VariantsLoader):

        super().__init__(
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

    @property
    def annotation_schema(self):
        return self.variants_loader.annotation_schema

    @classmethod
    def build_cli_params(cls, params):
        return cls.variants_loader.build_cli_params(params)

    @classmethod
    def cli_defaults(cls):
        return cls.variants_loader.cli_defaults()

    @classmethod
    def cli_options(cls, parser):
        return cls.variants_loader.cli_options(parser)

    def build_arguments_dict(self):
        return self.variants_loader.build_arguments_dict()

    def close(self):
        self.variants_loader.close()


class AnnotationDecorator(VariantsLoaderDecorator):
    """Base class for annotators."""

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

    @staticmethod
    def build_annotation_filename(filename):
        """Return the corresponding annotation file for filename."""
        path = pathlib.Path(filename)
        suffixes = path.suffixes

        if not suffixes:
            return f"{filename}-eff.txt"

        suffix = "".join(suffixes)
        replace_with = suffix.replace(".", "-")
        filename = filename.replace(suffix, replace_with)

        return f"{filename}-eff.txt"

    @staticmethod
    def has_annotation_file(variants_filename):
        annotation_filename = AnnotationDecorator\
            .build_annotation_filename(variants_filename)
        return os.path.exists(annotation_filename)

    @staticmethod
    def save_annotation_file(variants_loader, filename, sep="\t"):
        """Save annotation file."""
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
                    variants_loader.annotation_schema.names,
                )
            )
        else:
            other_columns = []

        header = common_columns[:]
        header.extend(["effects"])
        header.extend(other_columns)

        with open(filename, "w", encoding="utf8") as outfile:
            outfile.write(sep.join(header))
            outfile.write("\n")

            for summary_variant, _ in variants_loader.full_variants_iterator():
                for allele_index, summary_allele in enumerate(
                        summary_variant.alleles):

                    line = []
                    rec = summary_allele.attributes
                    rec["allele_index"] = allele_index

                    line_values = [
                        *[rec.get(col, "") for col in common_columns],
                        summary_allele.effects,
                        *[rec.get(col, "") for col in other_columns],
                    ]

                    for value in line_values:
                        line.append(str(value) if value is not None else "")

                    outfile.write(sep.join(line))
                    outfile.write("\n")


class EffectAnnotationDecorator(AnnotationDecorator):
    """Annotate variants with an effect."""

    def __init__(self, variants_loader, effect_annotator):
        super().__init__(variants_loader)

        self.set_attribute(
            "extra_attributes",
            variants_loader.get_attribute("extra_attributes")
        )

        self.effect_annotator = effect_annotator

    def full_variants_iterator(self):
        self.effect_annotator.open()

        for (summary_variant, family_variants) in \
                self.variants_loader.full_variants_iterator():
            for sallele in summary_variant.alt_alleles:
                context = {}
                attributes = self.effect_annotator.annotate(
                    sallele.get_annotatable(), context)
                assert "allele_effects" in attributes, attributes
                allele_effects = attributes["allele_effects"]
                assert isinstance(allele_effects, AlleleEffects), \
                    (type(allele_effects), allele_effects)
                # pylint: disable=protected-access
                sallele._effects = allele_effects
            yield summary_variant, family_variants

    def close(self):
        self.effect_annotator.close()
        super().close()


class AnnotationPipelineDecorator(AnnotationDecorator):
    """Annotate variants by processing them through an annotation pipeline."""

    def __init__(
            self, variants_loader, annotation_pipeline: AnnotationPipeline):
        super().__init__(variants_loader)

        self.annotation_pipeline = annotation_pipeline
        logger.debug(
            "creating annotation pipeline decorator with "
            "annotation pipeline: %s", annotation_pipeline.annotation_schema)

        self.set_attribute("annotation_schema", self.annotation_schema)
        self.set_attribute(
            "extra_attributes",
            variants_loader.get_attribute("extra_attributes")
        )

    @property
    def annotation_schema(self):
        return self.annotation_pipeline.annotation_schema

    def full_variants_iterator(self):
        with self.annotation_pipeline.open() as annotation_pipeline:
            for (summary_variant, family_variants) in \
                    self.variants_loader.full_variants_iterator():
                for sallele in summary_variant.alt_alleles:
                    attributes = annotation_pipeline.annotate(
                        sallele.get_annotatable())
                    if "allele_effects" in attributes:
                        allele_effects = attributes["allele_effects"]
                        assert isinstance(allele_effects, AlleleEffects), \
                            attributes
                        # pylint: disable=protected-access
                        sallele._effects = allele_effects
                    sallele.update_attributes(attributes)
                yield summary_variant, family_variants

    def close(self):
        self.annotation_pipeline.close()


class StoredAnnotationDecorator(AnnotationDecorator):
    """Annotate variant using a stored annotator."""

    def __init__(self, variants_loader, annotation_filename):
        super().__init__(variants_loader)

        assert os.path.exists(annotation_filename)
        self.annotation_filename = annotation_filename

    @staticmethod
    def decorate(variants_loader, source_filename):
        """Wrap variants_loader into a StoredAnnotationDecorator."""
        annotation_filename = StoredAnnotationDecorator \
            .build_annotation_filename(
                source_filename
            )
        if not os.path.exists(annotation_filename):
            logger.warning("stored annotation missing %s", annotation_filename)
            return variants_loader
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
        with open(filename, "r", encoding="utf8") as infile:
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
            ).replace({np.nan: None})
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
        logger.info(
            "Storred annotation file (%s) loaded in in %.2f sec",
            self.annotation_filename, elapsed)

        start = time.time()
        records = annot_df.to_dict(orient="records")
        index = 0

        while index < len(records):
            sumary_variant, family_variants = next(
                variant_iterator, (None, None))
            if sumary_variant is None:
                return
            variant_records = []

            current_record = records[index]
            while current_record["summary_variant_index"] == \
                    sumary_variant.summary_index:
                variant_records.append(current_record)
                index += 1
                if index >= len(records):
                    break
                current_record = records[index]

            assert len(variant_records) > 0, sumary_variant

            for sallele in sumary_variant.alleles:
                sallele.update_attributes(
                    variant_records[sallele.allele_index])
            yield sumary_variant, family_variants

        elapsed = time.time() - start
        logger.info(
            "Storred annotation file (%s) parsed in %.2f sec",
            self.annotation_filename, elapsed)


class VariantsGenotypesLoader(VariantsLoader):
    """Base class for variants loaders.

    Calculate missing best states and adds a genetic model
    value to the family variant and its alleles.
    """

    def __init__(
            self,
            families: FamiliesData,
            filenames: List[str],
            transmission_type: TransmissionType,
            genome: ReferenceGenome,
            regions: List[str] = None,
            expect_genotype: bool = True,
            expect_best_state: bool = False,
            params: Optional[Dict[str, Any]] = None):

        params = params if params else {}
        super().__init__(
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
        self._unadjust_chrom_prefix = lambda chrom: chrom
        if params.get("add_chrom_prefix", None):
            self._chrom_prefix = params["add_chrom_prefix"]
            self._adjust_chrom_prefix = self._add_chrom_prefix
            self._unadjust_chrom_prefix = self._del_chrom_prefix
        elif params.get("del_chrom_prefix", None):
            self._chrom_prefix = params["del_chrom_prefix"]
            self._adjust_chrom_prefix = self._del_chrom_prefix
            self._unadjust_chrom_prefix = self._add_chrom_prefix

        self.expect_genotype = expect_genotype
        self.expect_best_state = expect_best_state

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
        arguments = super()._arguments()
        arguments.append(CLIArgument(
            "--add-chrom-prefix",
            value_type=str,
            help_text="Add specified prefix to each chromosome name in "
            "variants file",
        ))
        arguments.append(CLIArgument(
            "--del-chrom-prefix",
            value_type=str,
            help_text="Remove specified prefix to each chromosome name in "
            "variants file",
        ))
        return arguments

    @property
    def variants_filenames(self):
        return self.filenames

    @abstractmethod
    def _full_variants_iterator_impl(self):
        pass

    def reset_regions(self, regions):
        if regions is None:
            self.regions = []
        elif isinstance(regions, str):
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
        cls, family_variant: FamilyVariant, genome: ReferenceGenome
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
                return GeneticModel.pseudo_autosomal
            if any(cls._get_diploid_males(family_variant)):
                return GeneticModel.X_broken

            return GeneticModel.X
        # We currently assume all other chromosomes are autosomal
        return GeneticModel.autosomal

    @classmethod
    def _calc_best_state(
            cls,
            family_variant: FamilyVariant,
            genome: ReferenceGenome,
            force: bool = True) -> Optional[np.ndarray]:

        male_ploidy = get_locus_ploidy(
            family_variant.chromosome, family_variant.position, Sex.M, genome
        )

        if family_variant.chromosome in ("X", "chrX") and male_ploidy == 1:
            best_state = calculate_simple_best_state(
                family_variant.gt, family_variant.allele_count
            )
            male_ids = [
                person.person_id
                for person in family_variant.family.members_in_order
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
        if force:
            return calculate_simple_best_state(
                family_variant.gt, family_variant.allele_count
            )
        return None

    @classmethod
    def _calc_genotype(
            cls, family_variant: FamilyVariant,
            genome: ReferenceGenome) -> Tuple[np.ndarray, GeneticModel]:
        # pylint: disable=protected-access
        best_state = family_variant._best_state
        genotype = best2gt(best_state)
        male_ploidy = get_locus_ploidy(
            family_variant.chromosome, family_variant.position,
            Sex.M, genome
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
        # there is an important invariant between this and _del_chrom_prefix
        # we don't know if this or _del_chrom_prefix will be executed first so
        # _add_chrom_prefix should undo _del_chrom_prefix
        # _del_chrom_prefix should undo _add_chrom_prefix
        assert self._chrom_prefix is not None
        return f"{self._chrom_prefix}{chrom}"

    def _del_chrom_prefix(self, chrom):
        assert self._chrom_prefix is not None
        assert chrom.startswith(self._chrom_prefix)
        return chrom[len(self._chrom_prefix):]

    def full_variants_iterator(
        self,
    ) -> Iterator[Tuple[SummaryVariant, List[FamilyVariant]]]:
        full_iterator = self._full_variants_iterator_impl()
        for summary_variant, family_variants in full_iterator:
            chrom = self._adjust_chrom_prefix(summary_variant.chromosome)
            # pylint: disable=protected-access
            summary_variant._chromosome = chrom
            for summary_allele in summary_variant.alleles:
                summary_allele._chrom = chrom
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
                    for fallele in family_variant.alleles:
                        fallele._best_state = family_variant.best_state
                        fallele._genetic_model = family_variant.genetic_model
                elif self.expect_best_state and family_variant.gt is None:
                    assert family_variant._best_state is not None
                    assert family_variant._genetic_model is None
                    assert family_variant.gt is None

                    (
                        family_variant.gt,
                        family_variant._genetic_model,
                    ) = self._calc_genotype(family_variant, self.genome)
                    for fallele in family_variant.alleles:
                        fallele.gt = family_variant.gt
                        fallele._genetic_model = family_variant.genetic_model

            yield summary_variant, family_variants