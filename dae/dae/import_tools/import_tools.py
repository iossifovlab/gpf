from __future__ import annotations

import logging
import os
import pathlib
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from copy import deepcopy
from dataclasses import dataclass
from functools import cache
from typing import Any, cast

import yaml
from box import Box

from dae.annotation.annotation_factory import (
    AnnotationPipeline,
    build_annotation_pipeline,
)
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.import_config import (
    embedded_input_schema,
    import_config_schema,
)
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from dae.gpf_instance import GPFInstance
from dae.parquet.partition_descriptor import (
    PartitionDescriptor,
)
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.task_graph.graph import TaskGraph
from dae.utils import fs_utils
from dae.utils.statistics import StatsCollection
from dae.variants_loaders.cnv.loader import CNVLoader
from dae.variants_loaders.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.variants_loaders.raw.loader import (
    AnnotationPipelineDecorator,
    VariantsLoader,
)
from dae.variants_loaders.vcf.loader import VcfLoader

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Bucket:
    """A region of the input used for processing."""

    type: str
    region_bin: str
    regions: list[str]
    index: int

    def __str__(self) -> str:
        regions = ";".join(r or "all" for r in self.regions)
        if not regions:
            regions = "all"
        return f"Bucket({self.type},{self.region_bin},{regions},{self.index})"


class ImportProject:
    """Encapsulate the import configuration.

    This class creates the necessary objects needed to import a study
    (e.g. loaders, family data and so one).
    """

    # pylint: disable=too-many-public-methods
    def __init__(
            self, import_config: dict[str, Any],
            base_input_dir: str | None,
            base_config_dir: str | None = None,
            gpf_instance: GPFInstance | None = None,
            config_filenames: list[str] | None = None) -> None:
        """Create a new project from the provided config.

        It is best not to call this ctor directly but to use one of the
        provided build_* methods.
        :param import_config: The parsed, validated and normalized config.
        :param gpf_instance: Allow overwiting the gpf instance as described in
        the configuration and instead injecting our own instance. Ideal for
        testing.
        """
        self.import_config: dict[str, Any] = import_config
        if "denovo" in import_config.get("input", {}):
            len_files = len(import_config["input"]["denovo"]["files"])
            assert len_files == 1, "Support for multiple denovo files is NYI"

        self._base_input_dir = base_input_dir
        self._base_config_dir = base_config_dir or base_input_dir
        self._gpf_instance = gpf_instance
        self.config_filenames = config_filenames or []
        self.stats: StatsCollection = StatsCollection()
        self._input_filenames_cache: dict[str, list[str]] = {}

    @staticmethod
    def build_from_config(
        import_config: dict[str, Any],
        base_input_dir: str = "",
        gpf_instance: GPFInstance | None = None,
    ) -> ImportProject:
        """Create a new project from the provided config.

        The config is first validated and normalized.
        :param import_config: The config to use for the import.
        :base_input_dir: Default input dir. Use cwd by default.
        """
        import_config = GPFConfigParser.validate_config(
            import_config,
            import_config_schema)
        normalizer = ImportConfigNormalizer()
        base_config_dir = base_input_dir
        import_config, base_input_dir, external_files = \
            normalizer.normalize(import_config, base_input_dir)
        return ImportProject(
            import_config, base_input_dir, base_config_dir,
            gpf_instance=gpf_instance, config_filenames=external_files,
        )

    @staticmethod
    def build_from_file(
            import_filename: str | os.PathLike,
            gpf_instance: GPFInstance | None = None) -> ImportProject:
        """Create a new project from the provided config filename.

        The file is first parsed, validated and normalized. The path to the
        file is used as the default input path for the project.

        :param import_filename: Path to the config file
        :param gpf_instance: Gpf Instance to use.
        """
        base_input_dir = fs_utils.containing_path(import_filename)
        import_config = GPFConfigParser.parse_and_interpolate_file(
            import_filename, conf_dir=base_input_dir)
        project = ImportProject.build_from_config(
            import_config, base_input_dir, gpf_instance=gpf_instance)
        # the path to the import filename should be the first config file
        project.config_filenames.insert(0, str(import_filename))
        return project

    def get_pedigree_params(self) -> tuple[str, dict[str, Any]]:
        """Get params for loading the pedigree."""
        families_filename = self.get_pedigree_filename()

        families_params = {}
        families_params.update(FamiliesLoader.cli_defaults())
        config_params = self.import_config["input"]["pedigree"]
        config_params = self._add_loader_prefix(config_params, "ped_")
        families_params.update(config_params)

        return families_filename, families_params

    def get_pedigree_filename(self) -> str:
        """Return the path to the pedigree file."""
        families_filename = self.import_config["input"]["pedigree"]["file"]
        families_filename = fs_utils.join(self.input_dir, families_filename)
        return cast(str, families_filename)

    def get_pedigree_loader(self) -> FamiliesLoader:
        families_filename, families_params = self.get_pedigree_params()
        return FamiliesLoader(
            families_filename, **families_params,
        )

    def get_pedigree(self) -> FamiliesData:
        """Load, parse and return the pedigree data."""
        families_loader = self.get_pedigree_loader()
        return families_loader.load()

    def get_variant_loader_types(self) -> set[str]:
        """Collect all variant import types used in the project."""
        result = set()
        for loader_type in ["denovo", "vcf", "cnv", "dae"]:
            config = self.import_config["input"].get(loader_type)
            if config is not None:
                result.add(loader_type)
        return result

    def has_denovo_variants(self) -> bool:
        """Check if the resulting imported study has denovo variants."""
        if "denovo" in self.get_variant_loader_types():
            return True
        if "vcf" in self.get_variant_loader_types():
            _, variants_params = \
                self.get_variant_params("vcf")
            if variants_params.get("vcf_denovo_mode") == "denovo":
                return True
        return False

    def get_variant_loader_chromosomes(
            self, loader_type: str | None = None) -> list[str]:
        """Collect all chromosomes available in input files."""
        if loader_type is None:
            loader_types = self.get_variant_loader_types()
        else:
            if loader_type not in self.get_variant_loader_types():
                return []
            loader_types = {loader_type}
        chromosomes = set()
        for ltype in loader_types:
            loader = self.get_variant_loader(loader_type=ltype)
            chromosomes.update(loader.chromosomes)
        return [
            chrom
            for chrom in self.get_gpf_instance().reference_genome.chromosomes
            if chrom in chromosomes
        ]

    def get_variant_loader_chrom_lens(
            self, loader_type: str | None = None) -> dict[str, int]:
        """Collect all chromosomes and their length available in input files."""
        all_chrom_lens = dict(
            self.get_gpf_instance().reference_genome.get_all_chrom_lengths())
        return {chrom: all_chrom_lens[chrom] for chrom in
                self.get_variant_loader_chromosomes(loader_type)}

    def get_import_variants_buckets(self) -> list[Bucket]:
        """Split variant files into buckets enabling parallel processing."""
        buckets: list[Bucket] = []
        for loader_type in ["denovo", "vcf", "cnv", "dae"]:
            config = self.import_config["input"].get(loader_type, None)
            if config is not None:
                buckets.extend(self._loader_region_bins(loader_type))

        return buckets

    def get_variant_loader(
        self,
        bucket: Bucket | None = None, loader_type: str | None = None,
        reference_genome: ReferenceGenome | None = None,
    ) -> VariantsLoader:
        """Get the appropriate variant loader for the specified bucket."""
        if bucket is None and loader_type is None:
            raise ValueError("loader_type or bucket is required")
        if bucket is not None:
            loader_type = bucket.type
        assert loader_type is not None
        loader = self._get_variant_loader(loader_type, reference_genome)
        if bucket is not None and bucket.region_bin != "all":
            loader.reset_regions(bucket.regions)
        return loader

    def get_input_filenames(self, bucket: Bucket) -> list[str]:
        """Get a list of input files for a specific bucket."""
        # creating a loader is expensive so cache the results
        if bucket.type not in self._input_filenames_cache:
            loader = self.get_variant_loader(bucket)
            self._input_filenames_cache[bucket.type] = loader.filenames
        return self._input_filenames_cache[bucket.type]

    def get_variant_params(
        self, loader_type: str,
    ) -> tuple[str | list[str], dict[str, Any]]:
        """Return variant loader filenames and params."""
        assert loader_type in self.import_config["input"], \
            f"No input config for loader {loader_type}"

        loader_config = self.import_config["input"][loader_type]
        if loader_type == "vcf" and "chromosomes" in loader_config:
            # vcf loader expects chromosomes to be in a string separated by ;
            loader_config = deepcopy(loader_config)
            loader_config["chromosomes"] = ";".join(
                loader_config["chromosomes"])
        variants_params = self._add_loader_prefix(loader_config,
                                                  loader_type + "_")

        variants_filenames = loader_config["files"]
        variants_filenames = [fs_utils.join(self.input_dir, f)
                              for f in variants_filenames]
        if loader_type in {"denovo", "dae"}:
            assert len(variants_filenames) == 1, \
                f"Support for multiple {loader_type} files is NYI"
            variants_filenames = variants_filenames[0]
        return variants_filenames, variants_params

    def _get_variant_loader(
        self, loader_type: str,
        reference_genome: ReferenceGenome | None = None,
    ) -> VariantsLoader:
        assert loader_type in self.import_config["input"], \
            f"No input config for loader {loader_type}"
        if reference_genome is None:
            reference_genome = self.get_gpf_instance().reference_genome
        variants_filenames, variants_params = \
            self.get_variant_params(loader_type)
        loader_cls = {
            "denovo": DenovoLoader,
            "vcf": VcfLoader,
            "cnv": CNVLoader,
            "dae": DaeTransmittedLoader,
        }[loader_type]
        loader: VariantsLoader = loader_cls(
            self.get_pedigree(),
            variants_filenames,
            params=variants_params,
            genome=reference_genome,
        )
        self._check_chrom_prefix(loader, variants_params)
        return loader

    def get_partition_descriptor(self) -> PartitionDescriptor:
        if "partition_description" not in self.import_config:
            return PartitionDescriptor()

        config_dict: dict = self.import_config["partition_description"]
        return PartitionDescriptor.parse_dict(config_dict)

    def get_gpf_instance(self) -> GPFInstance:
        """Create and return a gpf instance as desribed in the config."""
        if self._gpf_instance is not None:
            return self._gpf_instance

        instance_config = self.import_config.get("gpf_instance", {})
        instance_dir = instance_config.get("path")
        if instance_dir is None:
            config_filename = None
        else:
            config_filename = fs_utils.join(
                instance_dir, "gpf_instance.yaml")
        self._gpf_instance = GPFInstance.build(config_filename)
        return self._gpf_instance

    def get_import_storage(self) -> ImportStorage:
        """Create an import storage as described in the import config."""
        storage_type = self._storage_type()
        return self._get_import_storage(storage_type)

    @staticmethod
    @cache
    def _get_import_storage(storage_type: str) -> ImportStorage:
        factory = get_import_storage_factory(storage_type)
        return factory()

    @property
    def work_dir(self) -> str:
        """Where to store generated import files (e.g. parquet files)."""
        return cast(
            str,
            self.import_config.get("processing_config", {}).get("work_dir", ""),
        )

    @property
    def include_reference(self) -> bool:
        """Check if the import should include ref allele in the output data."""
        return cast(
            bool,
            self.import_config.get("processing_config", {}).get(
                "include_reference", False))

    @property
    def input_dir(self) -> str:
        """Return the path relative to which input files are specified."""
        assert self._base_input_dir is not None
        return fs_utils.join(
            self._base_input_dir,
            self.import_config["input"].get("input_dir", ""),
        )

    @property
    def study_id(self) -> str:
        return cast(str, self.import_config["id"])

    def get_processing_parquet_dataset_dir(self) -> str | None:
        """Return processing parquet dataset dir if configured and exists."""
        processing_config = self.import_config.get("processing_config", {})
        parquet_dataset_dir = processing_config.get("parquet_dataset_dir")
        if parquet_dataset_dir is None:
            return None
        if not fs_utils.exists(parquet_dataset_dir):
            return None
        return cast(str, parquet_dataset_dir)

    def get_parquet_dataset_dir(self) -> str:
        """Return parquet dataset direcotry.

        If processing parquet dataset dir is configured this method will
        return it. Otherwise it will construct work dir parquet dataset
        directory.
        """
        parquet_dataset_dir = self.get_processing_parquet_dataset_dir()
        if parquet_dataset_dir is not None:
            return parquet_dataset_dir
        return fs_utils.join(self.work_dir, self.study_id)

    def has_genotype_storage(self) -> bool:
        """Return if a genotype storage can be created."""
        if not self._has_destination():
            return True  # Use default genotype storage
        if "storage_type" not in self.import_config["destination"]:
            return True  # External genotype storage
        # Embedded configuration
        # storage_type is the only property in destination
        # this is a special case and we assume there is no genotype storage
        return len(self.import_config["destination"]) > 1

    def get_genotype_storage(self) -> GenotypeStorage:
        """Find, create and return the correct genotype storage."""
        explicit_config = (
            self._has_destination()
            and "storage_id" not in self.import_config["destination"]
        )
        if not explicit_config:
            gpf_instance = self.get_gpf_instance()
            genotype_storages: GenotypeStorageRegistry = \
                gpf_instance.genotype_storages
            storage_id = self.import_config.get("destination", {})\
                .get("storage_id", None)
            if storage_id is not None:
                return genotype_storages.get_genotype_storage(storage_id)
            return genotype_storages.get_default_genotype_storage()
        # explicit storage config
        registry = GenotypeStorageRegistry()
        return registry.register_storage_config(
            self.import_config["destination"])

    def _has_destination(self) -> bool:
        """Return if there is a *destination* section in the import config."""
        return "destination" in self.import_config

    def get_row_group_size(self) -> int:
        res = self.import_config \
            .get("processing_config", {}) \
            .get("parquet_row_group_size", 50_000)
        return cast(int, res)

    def build_variants_loader_pipeline(
        self, variants_loader: VariantsLoader,
    ) -> VariantsLoader:
        """Create an annotation pipeline around variants_loader."""
        annotation_pipeline = self.build_annotation_pipeline()
        if annotation_pipeline is not None:
            variants_loader = cast(
                VariantsLoader,
                AnnotationPipelineDecorator(
                    variants_loader, annotation_pipeline,
                ))
        return variants_loader

    def _storage_type(self) -> str:
        if not self._has_destination():
            # get default storage schema from GPF instance
            gpf_instance = self.get_gpf_instance()
            storage: GenotypeStorage = gpf_instance\
                .genotype_storages.get_default_genotype_storage()
            return storage.storage_type

        destination = self.import_config["destination"]
        if "storage_id" in destination:
            storage_id = destination["storage_id"]
            gpf_instance = self.get_gpf_instance()
            storage = gpf_instance\
                .genotype_storages\
                .get_genotype_storage(storage_id)
            return storage.storage_type

        return cast(str, destination["storage_type"])

    @staticmethod
    def _get_default_bucket_index(loader_type: str) -> int:
        return {
            "denovo": 0,
            "vcf": 100_000,
            "dae": 200_000,
            "cnv": 300_000,
        }[loader_type]

    @staticmethod
    def _add_loader_prefix(
            params: dict[str, Any], prefix: str) -> dict[str, Any]:
        res = {}
        exclude = {"add_chrom_prefix", "del_chrom_prefix", "files"}
        for k, val in params.items():
            if k not in exclude:
                res[prefix + k] = val
            else:
                res[k] = val
        return res

    @staticmethod
    def del_loader_prefix(
            params: dict[str, Any], prefix: str) -> dict[str, Any]:
        """Remove prefix from parameter keys."""
        res = {}
        for k, val in params.items():
            if val is None:
                continue
            key = k
            if k.startswith(prefix):
                key = k[len(prefix):]
            res[key] = val
        return res

    def _loader_region_bins(
            self, loader_type: str) -> Generator[Bucket, None, None]:
        # pylint: disable=too-many-locals
        reference_genome = self.get_gpf_instance().reference_genome

        loader = self._get_variant_loader(loader_type, reference_genome)
        loader_chromosomes = loader.chromosomes
        target_chromosomes = self._get_loader_target_chromosomes(loader_type)
        if target_chromosomes is None:
            target_chromosomes = loader_chromosomes

        # cannot use self.get_partition_description() here as the
        # processing region length might be different than the region length
        # specified in the parition description section of the import config
        processing_region_length = \
            self._get_processing_region_length(loader_type)
        processing_descriptor = PartitionDescriptor(
            chromosomes=target_chromosomes,
            region_length=processing_region_length,  # type: ignore
        )

        processing_config = self._get_loader_processing_config(loader_type)
        mode = None
        if isinstance(processing_config, str):
            mode = processing_config
        elif len(processing_config) == 0:
            mode = "single_bucket"  # default mode when missing config

        if mode == "single_bucket":
            processing_regions: dict[str, list[str]] = {"all": []}
        elif mode == "chromosome":
            processing_regions = {
                chrom: [chrom] for chrom in loader_chromosomes}
        else:
            assert mode is None
            processing_regions = {
                chrom: [str(r) for r in regions]
                for chrom, regions in processing_descriptor
                    .make_region_bins_regions(
                        chromosomes=loader_chromosomes,
                        chromosome_lengths=reference_genome
                        .get_all_chrom_lengths(),
                    ).items()
            }

        default_bucket_index = self._get_default_bucket_index(loader_type)
        for index, (region_bin, regions) in enumerate(
                processing_regions.items()):
            assert index <= 100_000, f"Too many buckets {loader_type}"
            bucket_index = default_bucket_index + index

            yield Bucket(
                loader_type,
                region_bin,
                regions,
                bucket_index,
            )

    def _get_processing_region_length(self, loader_type: str) -> int | None:
        processing_config = self._get_loader_processing_config(loader_type)
        if isinstance(processing_config, str):
            return None
        return cast(int, processing_config.get("region_length", sys.maxsize))

    def _get_loader_target_chromosomes(
            self, loader_type: str) -> list[str] | None:
        processing_config = self._get_loader_processing_config(loader_type)
        if isinstance(processing_config, str):
            return None
        return cast(
            list[str] | None, processing_config.get("chromosomes", None))

    def _get_loader_processing_config(
            self, loader_type: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.import_config.get("processing_config", {}).get(
                loader_type, {}))

    @staticmethod
    def _check_chrom_prefix(
            loader: VariantsLoader,
            variants_params: dict[str, Any]) -> None:
        prefix = variants_params.get("add_chrom_prefix")
        if prefix:
            all_already_have_prefix = True
            for chrom in loader.chromosomes:
                # the loader should have already added the prefix
                assert chrom.startswith(prefix)
                if not chrom[len(prefix):].startswith(prefix):
                    all_already_have_prefix = False
                    break
            if all_already_have_prefix and len(loader.chromosomes):
                raise ValueError(
                    f"All chromosomes already have the prefix {prefix}. "
                    "Consider removing add_chrom_prefix.",
                )

        prefix = variants_params.get("del_chrom_prefix")
        if prefix:
            try:
                # the chromosomes getter will assert for us if the prefix
                # can be removed or not. If there is no prefix to begin with
                # we will get an assertion error
                loader.chromosomes  # noqa: B018
            except AssertionError as exp:
                raise ValueError(
                    f"Chromosomes already missing the prefix {prefix}. "
                    "Consider removing del_chrom_prefix.",
                ) from exp

    def get_annotation_pipeline_config(
        self,
    ) -> list[dict]:
        """Return the annotation pipeline configuration."""
        gpf_instance = self.get_gpf_instance()
        if "annotation" not in self.import_config:
            # build default annotation pipeline as described in the gpf
            return construct_import_annotation_pipeline_config(gpf_instance)

        annotation_config = self.import_config["annotation"]
        if "file" in annotation_config:
            # pipeline in external file
            assert self._base_config_dir is not None
            annotation_config_file = fs_utils.join(
                self._base_config_dir, annotation_config["file"],
            )
            return construct_import_annotation_pipeline_config(
                gpf_instance, annotation_configfile=annotation_config_file,
            )
        return cast(list[dict], annotation_config)

    def build_annotation_pipeline(self) -> AnnotationPipeline:
        config = self.get_annotation_pipeline_config()
        gpf_instance = self.get_gpf_instance()
        return build_annotation_pipeline(config, gpf_instance.grr)

    def __str__(self) -> str:
        return f"Project({self.study_id})"

    def __getstate__(self) -> dict[str, Any]:
        """Return state of object used for pickling.

        The state is the default state but doesn't include the _gpf_instance
        as this property is transient.
        """
        gpf_instance = self.get_gpf_instance()
        state = self.__dict__.copy()
        del state["_gpf_instance"]
        state["_gpf_dae_config"] = gpf_instance.dae_config
        state["_gpf_dae_dir"] = gpf_instance.dae_dir
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Set state of object after unpickling."""
        self.__dict__.update(state)
        self._gpf_instance = GPFInstance(
            state["_gpf_dae_config"], state["_gpf_dae_dir"])


class ImportConfigNormalizer:
    """Class to normalize import configs.

    Most of the normalization is done by Cerberus but it fails short in a few
    cases. This class picks up the slack. It also reads external files and
    embeds them in the final configuration dict.
    """

    def normalize(
            self, import_config: dict,
            base_input_dir: str) -> tuple[dict[str, Any], str, list[str]]:
        """Normalize the import config."""
        config = deepcopy(import_config)

        base_input_dir, external_files = self._load_external_files(
            config, base_input_dir,
        )

        self._map_for_key(config, "region_length", self._int_shorthand)
        self._map_for_key(config, "chromosomes", self._normalize_chrom_list)
        if "parquet_row_group_size" in config.get("processing_config", {}):
            group_size_config = \
                config["processing_config"]["parquet_row_group_size"]
            if group_size_config is None:
                del config["processing_config"]["parquet_row_group_size"]
            else:
                config["processing_config"]["parquet_row_group_size"] = \
                    self._int_shorthand(group_size_config)
        return config, base_input_dir, external_files

    @classmethod
    def _load_external_files(
            cls, config: dict, base_input_dir: str) -> tuple[str, list[str]]:
        external_files: list[str] = []

        base_input_dir = cls._load_external_file(
            config, "input", base_input_dir, embedded_input_schema,
            external_files,
        )

        if "file" in config.get("annotation", {}):
            # don't load the config just add it to the list of external files
            external_files.append(config["annotation"]["file"])

        return base_input_dir, external_files

    @staticmethod
    def _load_external_file(
            config: dict, section_key: str, base_input_dir: str,
            schema: dict,
            external_files: list[str]) -> str:
        if section_key not in config:
            return base_input_dir

        sub_config = config[section_key]
        while "file" in sub_config:
            external_fn = fs_utils.join(base_input_dir, sub_config["file"])
            external_files.append(external_fn)
            sub_config = GPFConfigParser.parse_and_interpolate_file(
                external_fn,
            )
            sub_config = GPFConfigParser.validate_config(
                sub_config, schema,
            )
            base_input_dir = fs_utils.containing_path(external_fn)
        config[section_key] = sub_config
        return base_input_dir

    @classmethod
    def _map_for_key(
            cls, config: dict[str, Any], key: str,
            func: Callable[[Any], Any]) -> None:
        for k, val in config.items():
            if k == key:
                config[k] = func(val)
            elif isinstance(val, dict):
                cls._map_for_key(val, key, func)

    @staticmethod
    def _int_shorthand(obj: str | int) -> int:
        if isinstance(obj, int):
            return obj
        assert isinstance(obj, str)
        val = obj.strip()
        unit_suffixes = {
            "K": 1_000,
            "M": 1_000_000,
            "G": 1_000_000_000,
        }
        if val[-1].upper() not in unit_suffixes:
            return int(val)
        return int(val[:-1]) * unit_suffixes[val[-1].upper()]

    @classmethod
    def _normalize_chrom_list(cls, obj: str | list[str]) -> list[str]:
        if isinstance(obj, list):
            return cls._expand_chromosomes(obj)
        assert isinstance(obj, str)

        chrom_list = list(
            map(str.strip, obj.split(",")),
        )
        return cls._expand_chromosomes(chrom_list)

    @staticmethod
    def _expand_chromosomes(chromosomes: list[str]) -> list[str]:
        if chromosomes is None:
            return None
        res: list[str] = []
        for chrom in chromosomes:
            if chrom in {"autosomes", "autosomesXY"}:
                for i in range(1, 23):
                    res.extend((f"{i}", f"chr{i}"))
                if chrom == "autosomesXY":
                    for j in ["X", "Y"]:
                        res.extend((f"{j}", f"chr{j}"))
            else:
                res.append(chrom)
        return res


class ImportStorage(ABC):
    """Defines abstract base class for import storages."""

    @abstractmethod
    def generate_import_task_graph(self, project: ImportProject) -> TaskGraph:
        """Generate task grap for import of the project into this storage."""


_REGISTERED_IMPORT_STORAGE_FACTORIES: dict[
    str, Callable[[], ImportStorage]] = {}
_EXTENTIONS_LOADED = False


def _load_import_storage_factory_plugins() -> None:
    # pylint: disable=global-statement
    global _EXTENTIONS_LOADED
    if _EXTENTIONS_LOADED:
        return
    # pylint: disable=import-outside-toplevel
    from importlib_metadata import entry_points
    discovered_entries = entry_points(group="dae.import_tools.storages")
    for entry in discovered_entries:
        storage_type = entry.name
        factory = entry.load()
        if storage_type in _REGISTERED_IMPORT_STORAGE_FACTORIES:
            logger.warning("overwriting import storage type: %s", storage_type)
        _REGISTERED_IMPORT_STORAGE_FACTORIES[storage_type] = factory
    _EXTENTIONS_LOADED = True


def get_import_storage_factory(
        storage_type: str) -> Callable[[], ImportStorage]:
    """Find and return a factory function for creation of a storage type."""
    _load_import_storage_factory_plugins()
    if storage_type not in _REGISTERED_IMPORT_STORAGE_FACTORIES:
        raise ValueError(f"unsupported import storage type: {storage_type}")
    return _REGISTERED_IMPORT_STORAGE_FACTORIES[storage_type]


def get_import_storage_types() -> list[str]:
    _load_import_storage_factory_plugins()
    return list(_REGISTERED_IMPORT_STORAGE_FACTORIES.keys())


def register_import_storage_factory(
        storage_type: str,
        factory: Callable[[], ImportStorage]) -> None:
    _load_import_storage_factory_plugins()
    if storage_type in _REGISTERED_IMPORT_STORAGE_FACTORIES:
        logger.warning("overwriting import storage type: %s", storage_type)
    _REGISTERED_IMPORT_STORAGE_FACTORIES[storage_type] = factory


def save_study_config(
        dae_config: Box, study_id: str,
        study_config: str, *,
        force: bool = False) -> None:
    """Save the study config to a file."""
    dirname = os.path.join(dae_config.studies.dir, study_id)
    filename = os.path.join(dirname, f"{study_id}.yaml")

    if os.path.exists(filename):
        logger.info(
            "configuration file already exists: %s", filename)
        bak_name = os.path.basename(filename) + "." + str(time.time_ns())
        bak_path = os.path.join(os.path.dirname(filename), bak_name)

        if not force:
            logger.info(
                "skipping overwring the old config file... "
                "storing new config in %s", bak_path)
            pathlib.Path(bak_path).write_text(study_config)
            return

        logger.info(
            "Backing up configuration for %s in %s", study_id, bak_path)
        os.rename(filename, bak_path)

    os.makedirs(dirname, exist_ok=True)
    pathlib.Path(filename).write_text(study_config)


def construct_import_annotation_pipeline_config(
    gpf_instance: GPFInstance,
    annotation_configfile: str | None = None,
) -> list[dict]:
    """Construct annotation pipeline config for importing data."""
    if annotation_configfile is not None:
        assert os.path.exists(annotation_configfile), annotation_configfile
        with open(annotation_configfile, "rt", encoding="utf8") as infile:
            return cast(list[dict], yaml.safe_load(infile.read()))
    return gpf_instance.get_annotation_pipeline_config()


def construct_import_annotation_pipeline(
        gpf_instance: GPFInstance,
        annotation_configfile: str | None = None) -> AnnotationPipeline:
    """Construct annotation pipeline for importing data."""
    pipeline_config = construct_import_annotation_pipeline_config(
        gpf_instance, annotation_configfile)
    grr = gpf_instance.grr
    return build_annotation_pipeline(pipeline_config, grr)
