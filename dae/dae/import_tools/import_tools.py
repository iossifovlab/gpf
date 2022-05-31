from abc import abstractmethod
import argparse
from copy import deepcopy
from dataclasses import dataclass
import os
import sys
from dae.backends.cnv.loader import CNVLoader
from dae.backends.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.backends.vcf.loader import VcfLoader
from dae.backends.impala.parquet_io import ParquetPartitionDescriptor,\
    NoPartitionDescriptor, PartitionDescriptor
from dae.backends.raw.loader import AnnotationPipelineDecorator,\
    EffectAnnotationDecorator, VariantsLoader
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.task_graph import DaskExecutor, SequentialExecutor,\
    TaskGraph
from dae.pedigrees.family import FamiliesData
from dae.configuration.schemas.import_config import import_config_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.utils import fs_utils
from dae.backends.impala.import_commons import MakefilePartitionHelper,\
    construct_import_annotation_pipeline, construct_import_effect_annotator
from dae.dask.client_factory import DaskClient


@dataclass(frozen=True)
class Bucket:
    type: str
    region_bin: str
    regions: list[str]
    index: int


class ImportProject():
    def __init__(self, import_config, base_input_dir, gpf_instance):
        """
        Creates a new project from the provided config. It is best not to call
        this ctor directly but to use one of the provided build_* methods.
        :param import_config: The parsed, validated and normalized config.
        """
        self.import_config = import_config
        if "denovo" in import_config["input"]:
            len_files = len(import_config["input"]["denovo"]["files"])
            assert len_files == 1, "Support for multiple denovo files is NYI"

        self._base_input_dir = base_input_dir
        self._gpf_instance = gpf_instance

    @staticmethod
    def build_from_config(import_config, base_input_dir="", gpf_instance=None):
        """
        Creates a new project from the provided config. The config is first
        validated and normalized.
        :param import_config: The config to use for the import.
        :base_input_dir: Default input dir. Use cwd by default.
        """
        import_config = GPFConfigParser.validate_config(import_config,
                                                        import_config_schema)
        normalizer = ImportConfigNormalizer()
        import_config = normalizer.normalize(import_config)
        return ImportProject(import_config, base_input_dir, gpf_instance)

    @staticmethod
    def build_from_file(import_filename, gpf_instance=None):
        """Creates a new project from the provided config filename. The file
        is first parsed, validated and normalized. The path to the file is used
        as the default input path for the project.

        :param import_filename: Path to the config file
        :param gpf_instance: Gpf Instance to use.
        """
        base_input_dir = os.path.dirname(os.path.realpath(import_filename))
        import_config = GPFConfigParser.parse_and_interpolate_file(
            import_filename)
        return ImportProject.build_from_config(import_config, base_input_dir,
                                               gpf_instance)

    def get_pedigree(self) -> FamiliesData:
        """Loads, parses and returns the pedigree data"""
        families_filename = self.import_config["input"]["pedigree"]["file"]
        families_filename = fs_utils.join(self.input_dir, families_filename)

        families_params = self.import_config["input"]["pedigree"]
        families_params = self._add_loader_prefix(families_params, "ped_")

        families_loader = FamiliesLoader(
            families_filename, **families_params
        )
        return families_loader.load()

    def get_import_variants_buckets(self) -> list[Bucket]:
        """Splits the input variant files into buckets allowing
        for parallel processing"""
        types = ["denovo", "vcf", "cnv", "dae"]
        buckets = []
        for type in types:
            config = self.import_config["input"].get(type, None)
            if config is not None:
                for bucket in self._loader_region_bins(config, type):
                    buckets.append(bucket)
        return buckets

    def get_variant_loader(self, bucket, reference_genome=None):
        """Gets the appropriate variant loader for the specified bucket"""
        loader = self._get_variant_loader(bucket.type, reference_genome)
        loader.reset_regions(bucket.regions)
        return loader

    def _get_variant_loader(self, loader_type, reference_genome=None) \
            -> VariantsLoader:
        assert loader_type in self.import_config["input"],\
            f"No input config for loader {loader_type}"
        if reference_genome is None:
            reference_genome = self.get_gpf_instance().reference_genome

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

        loader_cls = {
            "denovo": DenovoLoader,
            "vcf": VcfLoader,
            "cnv": CNVLoader,
            "dae": DaeTransmittedLoader,
        }[loader_type]
        loader = loader_cls(
            self.get_pedigree(),
            variants_filenames,
            params=variants_params,
            genome=reference_genome,
        )
        return loader

    def get_partition_description(self, work_dir=None) -> PartitionDescriptor:
        """Retrurns a partition description object as described in the import
        config"""
        work_dir = work_dir if work_dir is not None else self.work_dir
        if "partition_description" in self.import_config:
            partition_desc = self.import_config["partition_description"]
            chromosomes = partition_desc.get("region_bin", {})\
                .get("chromosomes", None)
            assert isinstance(chromosomes, list)

            # ParquetPartitionDescriptor expects a string
            # that gets parsed internally
            partition_desc = deepcopy(partition_desc)
            partition_desc["region_bin"]["chromosomes"] = \
                ",".join(chromosomes)

            return ParquetPartitionDescriptor.from_dict(
                partition_desc,
                work_dir
            )
        else:
            return NoPartitionDescriptor(work_dir)

    def get_gpf_instance(self):
        if self._gpf_instance is None:
            instance_config = self.import_config.get("gpf_instance", {})
            return GPFInstance(work_dir=instance_config.get("path", None))
        else:
            return self._gpf_instance

    def get_storage(self):
        from dae.import_tools.impala_schema1 import ImpalaSchema1ImportStorage

        return ImpalaSchema1ImportStorage(self)

    @property
    def work_dir(self):
        """Returns the path where generated import files (e.g. parquet files)
        are stores"""
        return self.import_config.get("processing_config", {})\
            .get("work_dir", "")

    @property
    def input_dir(self):
        """Returns the path relative to which input files are specified"""
        return os.path.join(
            self._base_input_dir,
            self.import_config["input"].get("input_dir", "")
        )

    @property
    def study_id(self):
        return self.import_config["id"]

    @property
    def genotype_storage_id(self):
        # TODO handle inline storage configurations
        return self.import_config["destination"].get("storage_id")

    def has_destination(self) -> bool:
        """
        Returns True if there is a *destination* section in the import config
        """
        return "destination" in self.import_config

    def get_row_group_size(self, bucket) -> int:
        return self.import_config.get("parquet_row_group_size", {})\
            .get(bucket.type, 20_000)

    def build_variants_loader_pipeline(self, variants_loader, gpf_instance):
        """Creates an annotation pipeline around variants_loader"""
        effect_annotator = construct_import_effect_annotator(gpf_instance)

        variants_loader = EffectAnnotationDecorator(
            variants_loader, effect_annotator)

        annotation_config_file = self.import_config.get("annotation", {})\
            .get("file", None)
        # TODO what about embeded annotation config
        annotation_pipeline = construct_import_annotation_pipeline(
            gpf_instance, annotation_configfile=annotation_config_file,
        )
        if annotation_pipeline is not None:
            variants_loader = AnnotationPipelineDecorator(
                variants_loader, annotation_pipeline
            )

        return variants_loader

    def _get_default_bucket_index(self, loader_type):
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
        for k, v in params.items():
            if k not in exclude:
                res[prefix + k] = v
            else:
                res[k] = v
        return res

    def _loader_region_bins(self, loader_args, loader_type):
        reference_genome = self.get_gpf_instance().reference_genome

        loader = self._get_variant_loader(loader_type, reference_genome)
        loader_chromosomes = loader.chromosomes
        target_chromosomes = self._get_loader_target_chromosomes(loader_type)
        if target_chromosomes is None:
            target_chromosomes = loader_chromosomes

        partition_description = ParquetPartitionDescriptor(
            target_chromosomes,
            self._get_processing_region_length(loader_type),
        )

        partition_helper = MakefilePartitionHelper(
            partition_description,
            reference_genome,
            add_chrom_prefix=loader_args.get("add_chrom_prefix", None),
            del_chrom_prefix=loader_args.get("del_chrom_prefix", None),
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
        for rb, regions in variants_targets.items():
            bucket_index = default_bucket_index + index
            yield Bucket(loader_type, rb, regions, bucket_index)
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


class ImportConfigNormalizer:
    def normalize(self, import_config):
        config = deepcopy(import_config)
        self._map_for_key(config, "region_length", self._int_shorthand)
        self._map_for_key(config, "chromosomes", self._normalize_chrom_list)
        if "parquet_row_group_size" in config:
            group_size_config = config["parquet_row_group_size"]
            for loader in ["vcf", "denovo", "dae", "cnv"]:
                self._map_for_key(group_size_config, loader,
                                  self._int_shorthand)
        return config

    @classmethod
    def _map_for_key(cls, config, key, func):
        for k, v in config.items():
            if k == key:
                config[k] = func(v)
            elif isinstance(v, dict):
                cls._map_for_key(v, key, func)

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


class AbstractImportStorage:
    def __init__(self, project):
        pass

    @abstractmethod
    def generate_import_task_graph(self) -> TaskGraph:
        pass


def main():
    parser = argparse.ArgumentParser(description="Import datasets into GPF")
    parser.add_argument("-f", "--config", type=str,
                        help="Path to the import configuration")
    DaskClient.add_arguments(parser)
    args = parser.parse_args()

    if args.jobs == 1:
        executor = SequentialExecutor()
        run(args.config, executor)
    else:
        dask_client = DaskClient.from_arguments(args)
        if dask_client is None:
            sys.exit(1)
        with dask_client as client:
            executor = DaskExecutor(client)
            run(args.config, executor)


def run(import_config_fn, executor=SequentialExecutor(), gpf_instance=None):
    project = ImportProject.build_from_file(import_config_fn,
                                            gpf_instance=gpf_instance)
    run_with_project(project, executor)


def run_with_project(project, executor=SequentialExecutor()):
    storage = project.get_storage()
    task_graph = storage.generate_import_task_graph()
    executor.execute(task_graph)
