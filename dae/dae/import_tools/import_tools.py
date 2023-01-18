import sys
import logging
from abc import abstractmethod, ABC
from copy import deepcopy
from dataclasses import dataclass
from functools import cache
from typing import Callable, List, Optional, cast
from typing import Dict, Tuple, Any
from dae.annotation.annotation_factory import AnnotationConfigParser,\
    build_annotation_pipeline

from dae.variants_loaders.cnv.loader import CNVLoader
from dae.variants_loaders.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator,\
    EffectAnnotationDecorator, VariantsLoader

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry
)
from dae.parquet.schema1.parquet_io import ParquetPartitionDescriptor
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.task_graph.graph import TaskGraph
from dae.pedigrees.family import FamiliesData
from dae.configuration.schemas.import_config import import_config_schema,\
    embedded_input_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.utils import fs_utils
from dae.impala_storage.schema1.import_commons import MakefilePartitionHelper,\
    construct_import_annotation_pipeline, construct_import_effect_annotator
from dae.utils.statistics import StatsCollection


logger = logging.getLogger(__file__)


@dataclass(frozen=True)
class Bucket:
    """A region of the input used for processing."""

    type: str
    region_bin: str
    regions: list[str]
    index: int

    def __str__(self):
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
    def __init__(self, import_config, base_input_dir, base_config_dir=None,
                 gpf_instance=None, config_filenames=None):
        """Create a new project from the provided config.

        It is best not to call this ctor directly but to use one of the
        provided build_* methods.
        :param import_config: The parsed, validated and normalized config.
        :param gpf_instance: Allow overwiting the gpf instance as described in
        the configuration and instead injecting our own instance. Ideal for
        testing.
        """
        self.import_config = import_config
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
    def build_from_config(import_config, base_input_dir="", gpf_instance=None):
        """Create a new project from the provided config.

        The config is first validated and normalized.
        :param import_config: The config to use for the import.
        :base_input_dir: Default input dir. Use cwd by default.
        """
        import_config = GPFConfigParser.validate_config(import_config,
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
    def build_from_file(import_filename, gpf_instance=None):
        """Create a new project from the provided config filename.

        The file is first parsed, validated and normalized. The path to the
        file is used as the default input path for the project.

        :param import_filename: Path to the config file
        :param gpf_instance: Gpf Instance to use.
        """
        base_input_dir = fs_utils.containing_path(import_filename)
        import_config = GPFConfigParser.parse_and_interpolate_file(
            import_filename)
        project = ImportProject.build_from_config(
            import_config, base_input_dir, gpf_instance=gpf_instance)
        # the path to the import filename should be the first config file
        project.config_filenames.insert(0, import_filename)
        return project

    def get_pedigree_params(self) -> Tuple[str, Dict[str, Any]]:
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

    def get_import_variants_types(self) -> set[str]:
        """Collect all variant import types used in the project."""
        result = set()
        for loader_type in ["denovo", "vcf", "cnv", "dae"]:
            config = self.import_config["input"].get(loader_type)
            if config is not None:
                result.add(loader_type)
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
            reference_genome=None):
        """Get the appropriate variant loader for the specified bucket."""
        if bucket is None and loader_type is None:
            raise ValueError("loader_type or bucket is required")
        if bucket is not None:
            loader_type = bucket.type
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

    def get_variant_params(self, loader_type):
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
        if loader_type in {"denovo", "cnv", "dae"}:
            assert len(variants_filenames) == 1,\
                f"Support for multiple {loader_type} files is NYI"
            variants_filenames = variants_filenames[0]
        return variants_filenames, variants_params

    def _get_variant_loader(self, loader_type, reference_genome=None) \
            -> VariantsLoader:
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

    def get_gpf_instance(self):
        """Create and return a gpf instance as desribed in the config."""
        if self._gpf_instance is not None:
            return self._gpf_instance

        # pylint: disable=import-outside-toplevel
        from dae.gpf_instance.gpf_instance import GPFInstance

        instance_config = self.import_config.get("gpf_instance", {})
        instance_dir = instance_config.get("path")
        if instance_dir is None:
            config_filename = None
        else:
            config_filename = fs_utils.join(
                instance_dir, "gpf_instance.yaml")
        self._gpf_instance = GPFInstance.build(config_filename)
        return self._gpf_instance

    def get_import_storage(self):
        """Create an import storage as described in the import config."""
        storage_type = self._storage_type()
        return self._get_import_storage(storage_type)

    @staticmethod
    @cache
    def _get_import_storage(storage_type):
        factory = get_import_storage_factory(storage_type)
        return factory()

    @property
    def work_dir(self):
        """Where to store generated import files (e.g. parquet files)."""
        return self.import_config.get("processing_config", {})\
            .get("work_dir", "")

    @property
    def include_reference(self):
        """Check if the import should include ref allele in the output data."""
        return self.import_config.get("processing_config", {})\
            .get("include_reference", False)

    @property
    def input_dir(self):
        """Return the path relative to which input files are specified."""
        return fs_utils.join(
            self._base_input_dir,
            self.import_config["input"].get("input_dir", "")
        )

    def has_variants(self):
        # FIXME: this method should check if the input has variants
        return True

    def has_gpf_instance(self):
        # FIXME: this method should check if project has access to a
        # GPF instance - configured in the project or through the
        # environment variable DAE_DB_DIR
        return True

    @property
    def study_id(self):
        return self.import_config["id"]

    def get_genotype_storage(self):
        """Find, create and return the correct genotype storage."""
        explicit_config = (
            self.has_destination()
            and "storage_id" not in self.import_config["destination"]
        )
        if not explicit_config:
            gpf_instance = self.get_gpf_instance()
            genotype_storages = gpf_instance.genotype_storages
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

    def has_destination(self) -> bool:
        """Return if there is a *destination* section in the import config."""
        return "destination" in self.import_config

    def get_row_group_size(self, bucket) -> int:
        res = self.import_config.get("parquet_row_group_size", {})\
            .get(bucket.type, 20_000)
        return cast(int, res)

    def build_variants_loader_pipeline(
            self, variants_loader: VariantsLoader,
            gpf_instance) -> VariantsLoader:
        """Create an annotation pipeline around variants_loader."""
        effect_annotator = construct_import_effect_annotator(gpf_instance)

        variants_loader = EffectAnnotationDecorator(
            variants_loader, effect_annotator)

        annotation_pipeline = self._build_annotation_pipeline(gpf_instance)
        if annotation_pipeline is not None:
            variants_loader = AnnotationPipelineDecorator(
                variants_loader, annotation_pipeline
            )
        return variants_loader

    def _storage_type(self) -> str:
        if not self.has_destination():
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
    def _get_default_bucket_index(loader_type):
        return {
            "denovo": 0,
            "vcf": 1_000_000,
            "dae": 2_000_000,
            "cnv": 3_000_000
        }[loader_type]

    @staticmethod
    def _add_loader_prefix(params, prefix):
        res = {}
        exclude = {"add_chrom_prefix", "del_chrom_prefix", "files"}
        for k, val in params.items():
            if k not in exclude:
                res[prefix + k] = val
            else:
                res[k] = val
        return res

    @staticmethod
    def del_loader_prefix(params, prefix):
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

    def _loader_region_bins(self, loader_type):
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
        partition_description = ParquetPartitionDescriptor(
            target_chromosomes,
            self._get_processing_region_length(loader_type),
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

    def _get_processing_region_length(self, loader_type):
        processing_config = self._get_loader_processing_config(loader_type)
        if isinstance(processing_config, str):
            return None
        return processing_config.get("region_length", sys.maxsize)

    def _get_loader_target_chromosomes(self, loader_type):
        processing_config = self._get_loader_processing_config(loader_type)
        if isinstance(processing_config, str):
            return None
        return processing_config.get("chromosomes", None)

    def _get_loader_processing_config(self, loader_type):
        return self.import_config.get("processing_config", {})\
            .get(loader_type, {})

    @staticmethod
    def _check_chrom_prefix(loader, variants_params):
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

    def _build_annotation_pipeline(self, gpf_instance):
        if "annotation" not in self.import_config:
            # build default annotation pipeline as described in the gpf
            return construct_import_annotation_pipeline(gpf_instance)

        annotation_config = self.import_config["annotation"]
        if "file" in annotation_config:
            # pipeline in external file
            annotation_config_file = fs_utils.join(
                self._base_config_dir, annotation_config["file"]
            )
            return construct_import_annotation_pipeline(
                gpf_instance, annotation_configfile=annotation_config_file
            )

        # embedded annotation
        annotation_config = AnnotationConfigParser.normalize(annotation_config)
        return build_annotation_pipeline(
            pipeline_config=annotation_config, grr_repository=gpf_instance.grr
        )

    def __str__(self):
        return f"Project({self.study_id})"

    def __getstate__(self):
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

    def __setstate__(self, state):
        """Set state of object after unpickling."""
        self.__dict__.update(state)
        # pylint: disable=import-outside-toplevel
        from dae.gpf_instance.gpf_instance import GPFInstance
        self._gpf_instance = GPFInstance(
            state["_gpf_dae_config"], state["_gpf_dae_dir"])


class ImportConfigNormalizer:
    """Class to normalize import configs.

    Most of the normalization is done by Cerberus but it fails short in a few
    cases. This class picks up the slack. It also reads external files and
    embeds them in the final configuration dict.
    """

    def normalize(self, import_config: dict, base_input_dir: str):
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
    def _load_external_files(cls, config, base_input_dir):
        external_files = []

        base_input_dir = cls._load_external_file(
            config, "input", base_input_dir, embedded_input_schema,
            external_files
        )

        if "file" in config.get("annotation", {}):
            # don't load the config just add it to the list of external files
            external_files.append(config["annotation"]["file"])

        return base_input_dir, external_files

    @staticmethod
    def _load_external_file(config, section_key, base_input_dir, schema,
                            external_files):
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
    def _map_for_key(cls, config, key, func):
        for k, val in config.items():
            if k == key:
                config[k] = func(val)
            elif isinstance(val, dict):
                cls._map_for_key(val, key, func)

    @staticmethod
    def _int_shorthand(obj):
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
    def _normalize_chrom_list(cls, obj):
        if isinstance(obj, list):
            return cls._expand_chromosomes(obj)
        assert isinstance(obj, str)

        chrom_list = list(
            map(str.strip, obj.split(","))
        )
        return cls._expand_chromosomes(chrom_list)

    @staticmethod
    def _expand_chromosomes(chromosomes):
        if chromosomes is None:
            return None
        res = []
        for chrom in chromosomes:
            if chrom in {"autosomes", "autosomesXY"}:
                for i in range(1, 23):
                    res.append(f"{i}")
                    res.append(f"chr{i}")
                if chrom == "autosomesXY":
                    for i in ["X", "Y"]:
                        res.append(f"{i}")
                        res.append(f"chr{i}")
            else:
                res.append(chrom)
        return res


class ImportStorage(ABC):
    """Defines abstract base class for import storages."""

    def __init__(self):
        pass

    @abstractmethod
    def generate_import_task_graph(self, project: ImportProject) -> TaskGraph:
        """Generate task grap for import of the project into this storage."""


_REGISTERED_IMPORT_STORAGE_FACTORIES: \
    Dict[str, Callable[[], ImportStorage]] = {}
_EXTENTIONS_LOADED = False


def _load_import_storage_factory_plugins():
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


def get_import_storage_types() -> List[str]:
    _load_import_storage_factory_plugins()
    return list(_REGISTERED_IMPORT_STORAGE_FACTORIES.keys())


def register_import_storage_factory(
        storage_type: str,
        factory: Callable[[], ImportStorage]) -> None:
    _load_import_storage_factory_plugins()
    if storage_type in _REGISTERED_IMPORT_STORAGE_FACTORIES:
        logger.warning("overwriting import storage type: %s", storage_type)
    _REGISTERED_IMPORT_STORAGE_FACTORIES[storage_type] = factory
