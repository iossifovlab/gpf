"""Base classes and helpers for variant loaders."""
from __future__ import annotations

import argparse
import copy
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
)

import numpy as np

from dae.annotation.annotation_pipeline import AttributeInfo
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Family
from dae.utils.regions import Region
from dae.utils.variant_utils import best2gt, get_locus_ploidy
from dae.variants.attributes import GeneticModel, Sex, TransmissionType
from dae.variants.family_variant import (
    FamilyVariant,
    calculate_simple_best_state,
)
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)


class ArgumentType(Enum):
    ARGUMENT = 1
    OPTION = 2


FamilyGenotypeIterator = Generator[
    tuple[Family, np.ndarray, np.ndarray | None], None, None]


FullVariantsIterator = Generator[
    tuple[SummaryVariant, list[FamilyVariant]], None, None]

FamilyVariantsIterator = Generator[
    FamilyVariant, None, None]


@dataclass
class FullVariant:
    """A dataclass to hold a full variant with its families."""
    summary_variant: SummaryVariant
    family_variants: Sequence[FamilyVariant]


FullVariantsIterable = Iterable[FullVariant]
FamilyVariantsIterable = Iterable[FamilyVariant]


class CLIArgument:
    """Defines class for handling CLI arguments in variant loaders.

    This class handles the logic for CLI argument operations such as parsing
    arguments, transforming to dict, transforming a parsed argument back to
    a CLI argument and adding itself to an existing ArgumentParser.
    Construction closely mirrors the ArgumentParser argument format.
    """

    def __init__(
        self, argument_name: str, *,
        has_value: bool = True,
        default_value: int | str | bool | None = None,
        destination: str | None = None,
        help_text: str | None = None,
        action: str | None = None,
        value_type: type[str] | None = None,
        metavar: str | None = None,
        nargs: str | None = None,
        raw: bool = False,
    ) -> None:
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

    def __repr__(self) -> str:
        return f"{self.argument_name} ({self.arg_type})"

    def _default_destination(self) -> str | None:
        if self.argument_name.startswith("--"):
            self.arg_type = ArgumentType.OPTION
        else:
            self.arg_type = ArgumentType.ARGUMENT
            return None
        return self.argument_name[2:].replace("-", "_")

    def add_to_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add this argument to argsparser."""
        kwargs = {
            "type": self.value_type,
            "help": self.help_text,
            "default": self.default_value,
        }
        if self.arg_type == ArgumentType.OPTION:
            kwargs["dest"] = self.destination
        if self.action:
            # For some reason kwargs["type"] = self.value_type gets tuple-ized
            # should find a different workaround
            del kwargs["type"]
            kwargs["action"] = self.action
        else:
            kwargs["metavar"] = self.metavar
            kwargs["nargs"] = self.nargs

        parser.add_argument(self.argument_name, **kwargs)  # type: ignore

    def build_option(
        self, params: dict[str, str], *,
        use_defaults: bool = False,
    ) -> str | None:
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
                            value = value.encode(
                                "unicode-escape",
                            ).decode().replace("\\\\", "\\")
                        return f'{self.argument_name} "{value}"'
                    if use_defaults and self.default_value is not None:
                        value = str(self.default_value)
                        if self.raw:
                            value = value.encode(
                                "unicode-escape",
                            ).decode().replace("\\\\", "\\")
                        return f'{self.argument_name} "{value}"'
                else:
                    return f"{self.argument_name}"
        return None

    def parse_cli_argument(
        self, argv: argparse.Namespace, *,
        use_defaults: bool = False,
    ) -> None:
        """Parse the command line argument from the `argv` object.

        Args:
            argv (argparse.Namespace): The command line arguments.
            use_defaults (bool, optional): Whether to use default values
                if the argument is None. Defaults to False.
        """
        if self.destination not in argv:  # type: ignore
            return
        assert self.destination is not None
        argument = getattr(argv, self.destination)
        if argument is None and self.default_value is not None \
                and use_defaults:
            setattr(argv, self.destination, self.default_value)


class FamiliesGenotypes(ABC):
    """A base class for family genotypes."""

    @abstractmethod
    def family_genotype_iterator(self) -> FamilyGenotypeIterator:
        pass


class CLILoader(ABC):  # noqa: B024
    """Base class for loader classes that require cli arguments."""

    def __init__(
        self, params: dict[str, Any] | None = None,
    ) -> None:
        self.arguments = self._arguments()
        self.params: dict[str, Any] = params or {}

    def _add_argument(self, argument: CLIArgument) -> None:
        self.arguments.append(argument)

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
        return []

    @classmethod
    def cli_defaults(cls) -> dict[str, Any]:
        """Build a dictionary with default values for CLI arguments."""
        argument_destinations = [
            arg.destination for arg in cls._arguments()
            if arg.destination is not None
        ]
        defaults = [
            arg.default_value for arg in cls._arguments()
            if arg.destination is not None
        ]
        return dict(zip(argument_destinations, defaults, strict=True))

    @classmethod
    def cli_arguments(
        cls, parser: argparse.ArgumentParser, *,
        options_only: bool = False,
    ) -> None:
        """Add command-line arguments specific for the CLILoader class.

        Args:
            parser (argparse.ArgumentParser): The ArgumentParser object to
                add the arguments to.
            options_only (bool, optional): If True, only adds options
            (not arguments) to the parser. Defaults to False.
        """
        for argument in cls._arguments():
            if options_only and argument.arg_type == ArgumentType.ARGUMENT:
                continue
            argument.add_to_parser(parser)

    @classmethod
    def build_cli_arguments(cls, params: dict) -> str:
        """Return a string with cli arguments."""
        built_arguments = []
        for argument in cls._arguments():
            logger.info("adding to CLI arguments: %s", argument)
            built_arguments.append(argument.build_option(params))
        nonnull_arguments = (x for x in built_arguments if x is not None)
        result = " ".join(nonnull_arguments)
        logger.info("result CLI arguments: %s", result)
        return result

    def build_arguments_dict(self) -> dict[str, str | bool]:
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
        cls, argv: argparse.Namespace, *,
        use_defaults: bool = False,
    ) -> tuple[list[str], dict[str, Any]]:
        """Parse cli arguments."""
        for arg in cls._arguments():
            arg.parse_cli_argument(argv, use_defaults=use_defaults)
        return [], {}


class VariantsLoader(CLILoader):
    """Base class for all variant loaders."""

    def __init__(
        self,
        families: FamiliesData,
        filenames: str | list[str],
        genome: ReferenceGenome, *,
        transmission_type: TransmissionType = TransmissionType.transmitted,
        params: dict[str, Any] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        params = params or {}
        super().__init__(params=params)
        assert isinstance(families, FamiliesData)
        self.families = families
        if isinstance(filenames, str):
            filenames = [filenames]
        self.filenames = filenames

        assert isinstance(transmission_type, TransmissionType)
        self.transmission_type = transmission_type
        self.genome = genome
        if attributes is None:
            self._attributes = {}
        else:
            self._attributes = copy.deepcopy(attributes)
        self.arguments = []

    @property
    def variants_filenames(self) -> list[str]:
        return self.filenames

    def get_attribute(self, key: str) -> Any:
        return self._attributes.get(key, None)

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def reset_regions(
        self,
        regions: list[Region] | Sequence[Region | None] | None,
    ) -> None:
        pass

    @property
    def annotation_schema(self) -> list[AttributeInfo] | None:
        return None

    @classmethod
    def _arguments(cls) -> list[CLIArgument]:
        return []

    @abstractmethod
    def full_variants_iterator(self) -> FullVariantsIterator:
        pass

    def family_variants_iterator(self) -> FamilyVariantsIterator:
        for _, fvs in self.full_variants_iterator():
            yield from fvs

    def fetch(self, region: Region | None = None) -> FullVariantsIterable:
        """Fetch variants for a given region."""
        self.reset_regions([region] if region else None)
        for variant, family_variants in self.full_variants_iterator():
            yield FullVariant(variant, family_variants)

    def fetch_summary_variants(
        self, region: Region | None = None,
    ) -> Iterable[SummaryVariant]:
        """Fetch summary variants for a given region."""
        for full_variant in self.fetch(region):
            yield full_variant.summary_variant

    def fetch_family_variants(
        self, region: Region | None = None,
    ) -> Iterable[FamilyVariant]:
        """Fetch summary variants for a given region."""
        for full_variant in self.fetch(region):
            yield from full_variant.family_variants

    @abstractmethod
    def close(self) -> None:
        """Close resources used by the loader."""

    @property
    @abstractmethod
    def chromosomes(self) -> list[str]:
        """Return list of all chromosomes."""


class VariantsLoaderDecorator(VariantsLoader):
    """Base class for wrapping and decoring a variant loader."""

    def __init__(self, variants_loader: VariantsLoader) -> None:

        super().__init__(
            variants_loader.families,
            variants_loader.filenames,
            genome=variants_loader.genome,
            transmission_type=variants_loader.transmission_type,
            params=variants_loader.params,
            attributes=variants_loader._attributes,  # noqa: SLF001
        )
        self.variants_loader = variants_loader

    def get_attribute(self, key: str) -> Any:
        result = self._attributes.get(key, None)
        if result is not None:
            return result

        return self.variants_loader.get_attribute(key)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.variants_loader, attr, None)

    @property
    def annotation_schema(self) -> list[AttributeInfo] | None:
        return self.variants_loader.annotation_schema

    @classmethod
    def build_cli_arguments(cls, params: dict) -> str:
        raise NotImplementedError

    @classmethod
    def cli_defaults(cls) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def cli_arguments(
        cls, parser: argparse.ArgumentParser, *,
        options_only: bool = False,
    ) -> None:
        raise NotImplementedError

    def build_arguments_dict(self) -> dict:
        return self.variants_loader.build_arguments_dict()

    def close(self) -> None:
        self.variants_loader.close()

    @property
    def chromosomes(self) -> list[str]:
        return self.variants_loader.chromosomes


class VariantsGenotypesLoader(VariantsLoader):
    """Base class for variants loaders.

    Calculate missing best states and adds a genetic model
    value to the family variant and its alleles.
    """

    def __init__(
            self,
            families: FamiliesData,
            filenames: str | list[str],
            genome: ReferenceGenome, *,
            transmission_type: TransmissionType = TransmissionType.transmitted,
            regions: list[Region] | None = None,
            expect_genotype: bool = True,
            expect_best_state: bool = False,
            params: dict[str, Any] | None = None) -> None:

        params = params or {}
        super().__init__(
            families=families,
            filenames=filenames,
            transmission_type=transmission_type,
            genome=genome,
            params=params)

        self.regions: Sequence[Region | None] = [None]
        if regions is not None:
            self.reset_regions(regions)

        self._adjust_chrom_prefix: Callable[[str], str] = lambda chrom: chrom
        self._unadjust_chrom_prefix: Callable[[str], str] = lambda chrom: chrom
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

    @abstractmethod
    def _full_variants_iterator_impl(self) -> FullVariantsIterator:
        pass

    def reset_regions(
        self,
        regions: list[Region] | Sequence[Region | None] | None,
    ) -> None:
        if regions is None:
            self.regions = [None]
            return

        self.regions = list(filter(
            lambda r: r is None or "HLA" not in r.chrom,
            regions,
        ))

    @classmethod
    def _get_diploid_males(cls, family_variant: FamilyVariant) -> list[bool]:
        res = []

        assert family_variant.gt is not None
        assert family_variant.gt.shape == (2, len(family_variant.family))

        for member_idx, member in enumerate(
            family_variant.family.members_in_order,
        ):
            if member.sex in (Sex.F, Sex.U):
                continue
            res.append(bool(family_variant.gt[1, member_idx] != -2))
        return res

    @classmethod
    def _calc_genetic_model(
        cls, family_variant: FamilyVariant, genome: ReferenceGenome,
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
        genome: ReferenceGenome, *,
        force: bool = True,
    ) -> np.ndarray | None:
        assert family_variant.gt is not None

        male_ploidy = get_locus_ploidy(
            family_variant.chromosome, family_variant.position, Sex.M, genome,
        )

        if family_variant.chromosome in ("X", "chrX") and male_ploidy == 1:
            best_state = calculate_simple_best_state(
                family_variant.gt, family_variant.allele_count,
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

            return best_state
        if force:
            return calculate_simple_best_state(
                family_variant.gt, family_variant.allele_count,
            )
        return None

    @classmethod
    def _calc_genotype(
            cls, family_variant: FamilyVariant,
            genome: ReferenceGenome) -> tuple[np.ndarray, GeneticModel]:
        # pylint: disable=protected-access
        best_state = family_variant._best_state  # noqa: SLF001
        assert best_state is not None
        genotype = best2gt(best_state)
        male_ploidy = get_locus_ploidy(
            family_variant.chromosome, family_variant.position,
            Sex.M, genome,
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

    def _add_chrom_prefix(self, chrom: str) -> str:
        # there is an important invariant between this and _del_chrom_prefix
        # we don't know if this or _del_chrom_prefix will be executed first so
        # _add_chrom_prefix should undo _del_chrom_prefix
        # _del_chrom_prefix should undo _add_chrom_prefix
        assert self._chrom_prefix is not None
        return f"{self._chrom_prefix}{chrom}"

    def _del_chrom_prefix(self, chrom: str) -> str:
        assert self._chrom_prefix is not None
        assert chrom.startswith(self._chrom_prefix)
        return chrom[len(self._chrom_prefix):]

    def full_variants_iterator(
        self,
    ) -> FullVariantsIterator:
        full_iterator = self._full_variants_iterator_impl()
        for summary_variant, family_variants in full_iterator:
            chrom = self._adjust_chrom_prefix(summary_variant.chromosome)
            if chrom not in self.genome.chromosomes:
                logger.warning(
                    "chromosome %s not found in the reference genome %s; "
                    "skipping variant %s",
                    chrom, self.genome.resource.resource_id,
                    summary_variant)
                continue
            # pylint: disable=protected-access
            summary_variant._chromosome = chrom  # noqa: SLF001
            for summary_allele in summary_variant.alleles:
                summary_allele._chrom = chrom  # noqa: SLF001
                summary_allele._attributes["chrom"] = chrom  # noqa: SLF001

            for fv in family_variants:

                if self.expect_genotype:
                    assert fv._best_state is None  # noqa: SLF001
                    assert fv._genetic_model is None  # noqa: SLF001
                    assert fv.gt is not None

                    fv._genetic_model = \
                        self._calc_genetic_model(  # noqa: SLF001
                            fv, self.genome,
                        )

                    fv._best_state = self._calc_best_state(  # noqa: SLF001
                        fv, self.genome, force=False,
                    )
                    for fa in fv.family_alleles:
                        fa._best_state = fv.best_state  # noqa: SLF001
                        fa._genetic_model = fv.genetic_model  # noqa: SLF001
                elif self.expect_best_state and fv.gt is None:
                    assert fv._best_state is not None  # noqa: SLF001
                    assert fv._genetic_model is None  # noqa: SLF001
                    assert fv.gt is None

                    (
                        fv.gt,
                        fv._genetic_model,  # noqa: SLF001
                    ) = self._calc_genotype(fv, self.genome)
                    for fa in fv.family_alleles:
                        fa.gt = fv.gt
                        fa._genetic_model = fv.genetic_model  # noqa: SLF001

            yield summary_variant, family_variants
