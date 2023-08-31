from __future__ import annotations
import os
import sys
import logging
import time
from abc import abstractmethod, ABC
from copy import deepcopy
from dataclasses import dataclass
from functools import cache
from typing import Callable, Optional, cast, Union, Generator, Any
from collections import defaultdict
from math import ceil

import yaml
from box import Box

from dae.annotation.annotation_factory import AnnotationConfigParser,\
    build_annotation_pipeline, AnnotationPipeline

from dae.variants_loaders.cnv.loader import CNVLoader
from dae.variants_loaders.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator,\
    VariantsLoader
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.genotype_storage.genotype_storage_registry import \
    GenotypeStorageRegistry
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.task_graph.graph import TaskGraph
from dae.pedigrees.family import FamiliesData
from dae.configuration.schemas.import_config import import_config_schema,\
    embedded_input_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.gpf_instance import GPFInstance
from dae.utils import fs_utils
from dae.utils.statistics import StatsCollection


logger = logging.getLogger(__file__)


@dataclass(frozen=True)
class Bucket:
    """A region of the input used for processing."""

    type: str
    region_bin: str
    regions: list[str]
    index: int

    def __str__(self) -> str:
        regions = ";".join(r if r else "all" for r in self.regions)
        if not regions:
            regions = "all"
        return f"Bucket({self.type},{self.region_bin},{regions},{self.index})"


class ImportProject():
    """Encapsulate the import configuration.

    This class creates the necessary objects needed to import a study
    (e.g. loaders, family data and so one).
    """

    # pylint: disable=too-many-public-methods
    def __init__(
            self, import_config: dict[str, Any],
            base_input_dir: Optional[str],
            base_config_dir: Optional[str] = None,
            gpf_instance: Optional[GPFInstance] = None,
            config_filenames: Optional[list[str]] = None) -> None:
        """Create a new project from the provided config.

        It is best not to call this ctor directly but to use one of the
        provided build_* methods.
        :param import_config: The parsed, validated and normalized config.
        :param gpf_instance: Allow overwiting the gpf instance as described in
        the configuration and instead injecting our own instance. Ideal for
        testing.
        """
        self.import_config: dict[str, Any] = import_config
        if "denovo" in import_config["input"]:
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
        gpf_instance: Optional[GPFInstance] = None
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
            gpf_instance=gpf_instance, config_filenames=external_files
        )

    @staticmethod
    def build_from_file(
            import_filename: Union[str, os.PathLike],
            gpf_instance: Optional[GPFInstance] = None) -> ImportProject:
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
        families_loader = FamiliesLoader(
            families_filename, **families_params
        )
        return families_loader

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
            self, loader_type: Optional[str] = None) -> list[str]:
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
        result = []
        for chrom in self.get_gpf_instance().reference_genome.chromosomes:
            if chrom in chromosomes:
                result.append(chrom)
        return result

    def get_import_variants_buckets(self) -> list[Bucket]:
        """Split variant files into buckets enabling parallel processing."""
        buckets = []
        for loader_type in ["denovo", "vcf", "cnv", "dae"]:
            config = self.import_config["input"].get(loader_type, None)
            if config is not None:
                for bucket in self._loader_region_bins(loader_type):
                    buckets.append(bucket)
        return buckets

    def get_variant_loader(
        self,
        bucket: Optional[Bucket] = None, loader_type: Optional[str] = None,
        reference_genome: Optional[ReferenceGenome] = None
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
            self, loader_type: str) -> tuple[list[str], dict[str, Any]]:
        """Return variant loader filenames and params."""
        assert loader_type in self.import_config["input"],\
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
            assert len(variants_filenames) == 1,\
                f"Support for multiple {loader_type} files is NYI"
            variants_filenames = variants_filenames[0]
        return variants_filenames, variants_params

    def _get_variant_loader(
        self, loader_type: str,
        reference_genome: Optional[ReferenceGenome] = None
    ) -> VariantsLoader:
        assert loader_type in self.import_config["input"],\
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

    def get_partition_description_dict(self) -> Optional[dict]:
        """Retrurn a dict describing the paritition description.

        The dict is sutable for passing to the from_dict function of a
        PartitionDescriptor. Return None if no partition description is
        specified in the input config.
        """
        if "partition_description" not in self.import_config:
            return None

        partition_desc: dict = self.import_config["partition_description"]
        chromosomes = partition_desc.get("region_bin", {})\
            .get("chromosomes", None)
        assert isinstance(chromosomes, list)

        # ParquetPartitionDescriptor expects a string
        # that gets parsed internally
        partition_desc = deepcopy(partition_desc)
        partition_desc["region_bin"]["chromosomes"] = \
            ",".join(chromosomes)

        return partition_desc

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
            self.import_config.get("processing_config", {}).get("work_dir", "")
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
            self.import_config["input"].get("input_dir", "")
        )

    def has_variants(self) -> bool:
        # FIXME: this method should check if the input has variants
        return True

    @property
    def study_id(self) -> str:
        return cast(str, self.import_config["id"])

    def get_processing_parquet_dataset_dir(self) -> Optional[str]:
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
        if len(self.import_config["destination"]) > 1:
            return True  # Embedded configuration
        # storage_type is the only property in destination
        # this is a special case and we assume there is no genotype storage
        return False

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
        # FIXME: switch to using new storage configuration
        return registry.register_storage_config(
            self.import_config["destination"])

    def _has_destination(self) -> bool:
        """Return if there is a *destination* section in the import config."""
        return "destination" in self.import_config

    def get_row_group_size(self, bucket: Bucket) -> int:
        res = self.import_config.get("parquet_row_group_size", {})\
            .get(bucket.type, 20_000)
        return cast(int, res)

    def build_variants_loader_pipeline(
            self, variants_loader: VariantsLoader,
            gpf_instance: GPFInstance) -> VariantsLoader:
        """Create an annotation pipeline around variants_loader."""
        annotation_pipeline = self._build_annotation_pipeline(gpf_instance)
        if annotation_pipeline is not None:
            variants_loader = AnnotationPipelineDecorator(
                variants_loader, annotation_pipeline
            )
        return variants_loader

    def _storage_type(self) -> str:
        if not self._has_destination():
            # get default storage schema from GPF instance
            gpf_instance = self.get_gpf_instance()
            storage: GenotypeStorage = gpf_instance\
                .genotype_storages.get_default_genotype_storage()
            return storage.get_storage_type()

        destination = self.import_config["destination"]
        if "storage_id" in destination:
            storage_id = destination["storage_id"]
            gpf_instance = self.get_gpf_instance()
            storage = gpf_instance\
                .genotype_storages\
                .get_genotype_storage(storage_id)
            return storage.get_storage_type()

        return cast(str, destination["storage_type"])

    @staticmethod
    def _get_default_bucket_index(loader_type: str) -> int:
        return {
            "denovo": 0,
            "vcf": 1_000_000,
            "dae": 2_000_000,
            "cnv": 3_000_000
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
        partition_description = PartitionDescriptor(
            chromosomes=target_chromosomes,
            region_length=processing_region_length  # type: ignore
        )

        partition_helper = MakefilePartitionHelper(
            partition_description,
            reference_genome,
        )

        processing_config = self._get_loader_processing_config(loader_type)
        mode = None
        if isinstance(processing_config, str):
            mode = processing_config
        elif len(processing_config) == 0:
            mode = "single_bucket"  # default mode when missing config
        variants_targets = partition_helper.generate_variants_targets(
            loader_chromosomes,
            mode=mode
        )

        default_bucket_index = self._get_default_bucket_index(loader_type)
        index = 0
        for region_bin, regions in variants_targets.items():
            bucket_index = default_bucket_index + index
            yield Bucket(loader_type, region_bin, regions, bucket_index)
            index += 1

    def _get_processing_region_length(self, loader_type: str) -> Optional[int]:
        processing_config = self._get_loader_processing_config(loader_type)
        if isinstance(processing_config, str):
            return None
        return cast(int, processing_config.get("region_length", sys.maxsize))

    def _get_loader_target_chromosomes(
            self, loader_type: str) -> Optional[list[str]]:
        processing_config = self._get_loader_processing_config(loader_type)
        if isinstance(processing_config, str):
            return None
        return cast(
            Optional[list[str]], processing_config.get("chromosomes", None))

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
                    "Consider removing add_chrom_prefix."
                )

        prefix = variants_params.get("del_chrom_prefix")
        if prefix:
            try:
                # the chromosomes getter will assert for us if the prefix
                # can be removed or not. If there is no prefix to begin with
                # we will get an assertion error
                loader.chromosomes
            except AssertionError as exp:
                raise ValueError(
                    f"Chromosomes already missing the prefix {prefix}. "
                    "Consider removing del_chrom_prefix."
                ) from exp

    def _build_annotation_pipeline(
            self, gpf_instance: GPFInstance) -> AnnotationPipeline:
        if "annotation" not in self.import_config:
            # build default annotation pipeline as described in the gpf
            return construct_import_annotation_pipeline(gpf_instance)

        annotation_config = self.import_config["annotation"]
        if "file" in annotation_config:
            # pipeline in external file
            assert self._base_config_dir is not None
            annotation_config_file = fs_utils.join(
                self._base_config_dir, annotation_config["file"]
            )
            return construct_import_annotation_pipeline(
                gpf_instance, annotation_configfile=annotation_config_file
            )

        # embedded annotation
        annotation_config = AnnotationConfigParser.parse_raw(annotation_config)
        return build_annotation_pipeline(
            pipeline_config=annotation_config, grr_repository=gpf_instance.grr
        )

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
            config, base_input_dir
        )

        self._map_for_key(config, "region_length", self._int_shorthand)
        self._map_for_key(config, "chromosomes", self._normalize_chrom_list)
        if "parquet_row_group_size" in config:
            group_size_config = config["parquet_row_group_size"]
            for loader in ["vcf", "denovo", "dae", "cnv"]:
                self._map_for_key(group_size_config, loader,
                                  self._int_shorthand)
        return config, base_input_dir, external_files

    @classmethod
    def _load_external_files(
            cls, config: dict, base_input_dir: str) -> tuple[str, list[str]]:
        external_files: list[str] = []

        base_input_dir = cls._load_external_file(
            config, "input", base_input_dir, embedded_input_schema,
            external_files
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
                external_fn
            )
            sub_config = GPFConfigParser.validate_config(
                sub_config, schema
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
    def _int_shorthand(obj: Union[str, int]) -> int:
        if isinstance(obj, int):
            return obj
        assert isinstance(obj, str)

        unit_suffixes = {
            "K": 1_000,
            "M": 1_000_000,
            "G": 1_000_000_000,
        }
        return int(obj[:-1]) * unit_suffixes[obj[-1].upper()]

    @classmethod
    def _normalize_chrom_list(cls, obj: Union[str, list[str]]) -> list[str]:
        if isinstance(obj, list):
            return cls._expand_chromosomes(obj)
        assert isinstance(obj, str)

        chrom_list = list(
            map(str.strip, obj.split(","))
        )
        return cls._expand_chromosomes(chrom_list)

    @staticmethod
    def _expand_chromosomes(chromosomes: list[str]) -> list[str]:
        if chromosomes is None:
            return None
        res = []
        for chrom in chromosomes:
            if chrom in {"autosomes", "autosomesXY"}:
                for i in range(1, 23):
                    res.append(f"{i}")
                    res.append(f"chr{i}")
                if chrom == "autosomesXY":
                    for j in ["X", "Y"]:
                        res.append(f"{j}")
                        res.append(f"chr{j}")
            else:
                res.append(chrom)
        return res


class ImportStorage(ABC):
    """Defines abstract base class for import storages."""

    def __init__(self) -> None:
        pass

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
        study_config: str, force: bool = False) -> None:
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
            with open(bak_path, "w") as outfile:
                outfile.write(study_config)
            return

        logger.info(
            "Backing up configuration for %s in %s", study_id, bak_path)
        os.rename(filename, bak_path)

    os.makedirs(dirname, exist_ok=True)
    with open(filename, "w") as outfile:
        outfile.write(study_config)


def construct_import_annotation_pipeline(
        gpf_instance: GPFInstance,
        annotation_configfile: Optional[str] = None) -> AnnotationPipeline:
    """Construct annotation pipeline for importing data."""
    pipeline_config = []
    if annotation_configfile is not None:
        assert os.path.exists(annotation_configfile), annotation_configfile
        with open(annotation_configfile, "rt", encoding="utf8") as infile:
            pipeline_config = yaml.safe_load(infile.read())
    else:
        if gpf_instance.dae_config.annotation is not None:
            config_filename = gpf_instance.dae_config.annotation.conf_file
            assert os.path.exists(config_filename), config_filename
            with open(config_filename, "rt", encoding="utf8") as infile:
                pipeline_config = yaml.safe_load(infile.read())

        pipeline_config.insert(
            0, _construct_import_effect_annotator_config(gpf_instance))

    grr = gpf_instance.grr
    pipeline = build_annotation_pipeline(
        pipeline_config_raw=pipeline_config, grr_repository=grr)
    return pipeline


def _construct_import_effect_annotator_config(
        gpf_instance: GPFInstance) -> dict[str, Any]:
    """Construct import effect annotator."""
    genome = gpf_instance.reference_genome
    gene_models = gpf_instance.gene_models

    config = {
        "effect_annotator": {
            "genome": genome.resource_id,
            "gene_models": gene_models.resource_id,
            "attributes": [
                {
                    "source": "allele_effects",
                    "destination": "allele_effects",
                    "internal": True
                }
            ]
        }
    }
    return config


class MakefilePartitionHelper:
    """Helper class for organizing partition targets."""

    def __init__(
            self,
            partition_descriptor: PartitionDescriptor,
            genome: ReferenceGenome):

        self.genome = genome
        self.partition_descriptor = partition_descriptor
        self.chromosome_lengths = dict(
            self.genome.get_all_chrom_lengths()
        )

    def region_bins_count(self, chrom: str) -> int:
        result = ceil(
            self.chromosome_lengths[chrom]
            / self.partition_descriptor.region_length
        )
        return result

    @staticmethod
    def build_target_chromosomes(target_chromosomes: list[str]) -> list[str]:
        return target_chromosomes[:]

    def generate_chrom_targets(
            self, target_chrom: str) -> list[tuple[str, str]]:
        """Generate variant targets based on partition descriptor."""
        target = target_chrom
        if target_chrom not in self.partition_descriptor.chromosomes:
            target = "other"
        region_bins_count = self.region_bins_count(target_chrom)

        chrom = target_chrom

        if region_bins_count == 1:
            return [(f"{target}_0", chrom)]
        result = []
        for region_index in range(region_bins_count):
            start = region_index * self.partition_descriptor.region_length + 1
            end = (region_index + 1) * self.partition_descriptor.region_length
            if end > self.chromosome_lengths[target_chrom]:
                end = self.chromosome_lengths[target_chrom]
            result.append(
                (f"{target}_{region_index}", f"{chrom}:{start}-{end}")
            )
        return result

    def bucket_index(self, region_bin: str) -> int:
        """Return bucket index based on variants target."""
        genome_chromosomes = [
            chrom
            for chrom, _ in
            self.genome.get_all_chrom_lengths()
        ]
        variants_targets = self.generate_variants_targets(genome_chromosomes)
        assert region_bin in variants_targets

        targets = list(variants_targets.keys())
        return targets.index(region_bin)

    def generate_variants_targets(
            self, target_chromosomes: list[str],
            mode: Optional[str] = None) -> dict[str, list]:
        """Produce variants targets."""
        if len(self.partition_descriptor.chromosomes) == 0:
            return {"none": [""]}

        generated_target_chromosomes = target_chromosomes[:]
        targets: dict[str, list]
        if mode == "single_bucket":
            targets = {"all": [None]}
            return targets
        if mode == "chromosome":
            targets = {chrom: [chrom]
                       for chrom in generated_target_chromosomes}
            return targets
        if mode is not None:
            raise ValueError(f"Invalid value for mode '{mode}'")

        targets = defaultdict(list)
        for target_chrom in generated_target_chromosomes:
            assert target_chrom in self.chromosome_lengths, (
                target_chrom,
                self.chromosome_lengths,
            )
            region_targets = self.generate_chrom_targets(target_chrom)

            for target, region in region_targets:
                # target = self.reset_target(target)
                targets[target].append(region)
        return targets
