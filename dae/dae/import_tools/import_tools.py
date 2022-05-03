import argparse
from dataclasses import dataclass
from dae.backends.cnv.loader import CNVLoader
from dae.backends.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.backends.vcf.loader import VcfLoader
from dae.backends.impala.parquet_io import ParquetPartitionDescriptor,\
    NoPartitionDescriptor
from dae.backends.raw.loader import AnnotationPipelineDecorator,\
    EffectAnnotationDecorator, VariantsLoader
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.impala_schema1 import ImpalaSchema1ImportStorage
from dae.import_tools.task_graph import DaskExecutor, SequentialExecutor
from dae.pedigrees.family import FamiliesData
from dae.configuration.schemas.import_config import import_config_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.utils import fs_utils
from dae.backends.impala.import_commons import MakefilePartitionHelper,\
    construct_import_annotation_pipeline, construct_import_effect_annotator


@dataclass(frozen=True)
class BucketId:
    type: str
    region_bin: str
    regions: list[str]
    index: int


class ImportProject():
    def __init__(self, import_config, gpf_instance=None):
        self.import_config = import_config
        if "denovo" in import_config["input"]:
            len_files = len(import_config["input"]["denovo"]["files"])
            assert len_files == 1, "Support for multiple denovo files is NYI"

        self._gpf_instance = gpf_instance

    @staticmethod
    def build_from_config(import_config, gpf_instance=None):
        return ImportProject(import_config, gpf_instance)

    @staticmethod
    def build_from_file(import_filename, gpf_instance=None):
        import_config = GPFConfigParser.parse_and_interpolate_file(
            import_filename)
        import_config = GPFConfigParser.validate_config(import_config,
                                                        import_config_schema)
        return ImportProject(import_config, gpf_instance)

    def get_pedigree(self) -> FamiliesData:
        families_filename = self.import_config["input"]["pedigree"]["file"]
        families_filename = fs_utils.join(self.input_dir, families_filename)

        families_params = self.import_config["input"]["pedigree"]
        families_params = self._add_loader_prefix(families_params, "ped_")

        families_loader = FamiliesLoader(
            families_filename, **families_params
        )
        return families_loader.load()

    def get_import_variants_bucket_ids(self) -> list[BucketId]:
        types = {
            "denovo": self._denovo_region_bins,
            "vcf": self._vcf_region_bins,
            "cnv": self._cnv_region_bins,
            "dae": self._dae_region_bins,
        }
        buckets = []
        for type, region_bins_func in types.items():
            config = self.import_config["input"].get(type, None)
            if config is not None:
                for rb, regions in region_bins_func(config):
                    buckets.append(BucketId(type, rb, regions, 0))  #TODO bucket index
        return buckets

    def get_variant_loader(self, bucket_id, reference_genome=None):
        loader = self._get_variant_loader(bucket_id.type, reference_genome)
        loader.reset_regions(bucket_id.regions)
        return loader

    def _get_variant_loader(self, loader_type, reference_genome=None) \
            -> VariantsLoader:
        assert loader_type in self.import_config["input"],\
            f"No input config for loader {loader_type}"
        if reference_genome is None:
            reference_genome = self.get_gpf_instance().reference_genome

        loader_config = self.import_config["input"][loader_type]
        variants_params = self._add_loader_prefix(loader_config,
                                                  loader_type + "_")

        variants_filenames = loader_config["files"]
        variants_filenames = [fs_utils.join(self.input_dir, f)
                              for f in variants_filenames]
        if loader_type in {"denovo", "cnv"}:
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

    def get_partition_description(self, work_dir=None):
        work_dir = work_dir or self.work_dir
        if "partition_description" in self.import_config:
            return ParquetPartitionDescriptor.from_dict(
                self.import_config["partition_description"],
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
        return ImpalaSchema1ImportStorage(self)

    @property
    def work_dir(self):
        return self.import_config["processing_config"]["work_dir"]

    @property
    def input_dir(self):
        return self.import_config["input"]["input_dir"]

    @property
    def study_id(self):
        return self.import_config["id"]

    @property
    def genotype_storage_id(self):
        # TODO handle inline storage configurations
        return self.import_config["destination"].get("storage_id")

    def has_destination(self):
        return "destination" in self.import_config

    def build_variants_loader_pipeline(self, variants_loader, gpf_instance):
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

    def get_default_bucket_index(self, loader_type):
        return {
            "denovo": 1,
            "vcf": 1000,
            "dae": 1000,
            "cnv": 2
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

    def _denovo_region_bins(self, input_config):
        yield from self._loader_region_bins(input_config, "denovo")

    def _vcf_region_bins(self, input_config):
        yield from self._loader_region_bins(input_config, "vcf")

    def _cnv_region_bins(self, input_config):
        yield from self._loader_region_bins(input_config, "cnv")

    def _dae_region_bins(self, input_config):
        yield from self._loader_region_bins(input_config, "dae")

    def _loader_region_bins(self, loader_args, loader_type):
        # TODO pass the gpf instance as argument to this func
        reference_genome = self.get_gpf_instance().reference_genome

        target_chromosomes = loader_args.get("target_chromosomes", None)
        if target_chromosomes is None:
            loader = self._get_variant_loader(loader_type, reference_genome)
            target_chromosomes = loader.chromosomes

        partition_description = self.get_partition_description()

        partition_helper = MakefilePartitionHelper(
            partition_description,
            reference_genome,
            add_chrom_prefix=loader_args.get("add_chrom_prefix", None),
            del_chrom_prefix=loader_args.get("del_chrom_prefix", None),
        )

        variants_targets = partition_helper.generate_variants_targets(
            target_chromosomes
        )

        yield from variants_targets.items()


def main():
    parser = argparse.ArgumentParser(description="Import datasets into GPF")
    parser.add_argument("-f", "--config", type=str,
                        help="Path to the import configuration")
    parser.add_argument("-j", "--jobs", type=int, default=None,
                        help="Number of jobs to run in parallel. \
 Defaults to the number of processors on the machine")
    args = parser.parse_args()

    import_config = GPFConfigParser.parse_and_interpolate_file(args.config)
    import_config = GPFConfigParser.validate_config(import_config,
                                                    import_config_schema)
    if args.jobs == 1:
        executor = SequentialExecutor()
    else:
        from dask.distributed import Client, LocalCluster
        import os
        n_jobs = args.jobs if args.jobs and args.jobs >= 1 else os.cpu_count()
        cluster = LocalCluster(n_workers=n_jobs, threads_per_worker=1)
        client = Client(cluster)
        executor = DaskExecutor(client)
    run(import_config, executor)


def run(import_config, executor=SequentialExecutor(), gpf_instance=None):
    project = ImportProject.build_from_config(import_config, gpf_instance)
    storage = project.get_storage()
    task_graph = storage.generate_import_task_graph()
    executor.execute(task_graph)
