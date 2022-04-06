import argparse
from dataclasses import dataclass
import logging
import os
from dae.backends.dae.loader import DenovoLoader
from dae.backends.vcf.loader import VcfLoader
from dae.backends.impala.parquet_io import ParquetManager,\
    ParquetPartitionDescriptor, NoPartitionDescriptor
from dae.backends.raw.loader import AnnotationPipelineDecorator,\
    EffectAnnotationDecorator, VariantsLoader
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.task_graph import SequentialExecutor, TaskGraph
from dae.pedigrees.family import FamiliesData
from dae.configuration.schemas.import_config import import_config_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.utils import fs_utils
from dae.backends.impala.import_commons import MakefilePartitionHelper,\
    construct_import_annotation_pipeline, construct_import_effect_annotator
import toml


logger = logging.getLogger(__file__)


@dataclass(frozen=True)
class BucketId:
    type: str
    region_bin: str


class ImportProject():
    def __init__(self, import_config, gpf_instance=None):
        self.import_config = import_config
        if "denovo" in import_config["input"]:
            len_files = len(import_config["input"]["denovo"]["files"])
            assert len_files == 1, "Support for multiple denovo files is NYI"

        self._gpf_instance = gpf_instance

    def get_pedigree(self) -> FamiliesData:
        families_filename = self.import_config["input"]["pedigree"]["file"]
        families_filename = fs_utils.join(self.input_dir, families_filename)

        families_params = self.import_config["input"]["pedigree"]
        families_params = self._add_loader_prefix(families_params, "ped_")

        families_loader = FamiliesLoader(
            families_filename, **families_params
        )
        return families_loader.load()

    def get_import_variants_buckets(self) -> list[BucketId]:
        types = {
            "denovo": self._denovo_region_bins,
            "vcf": self._vcf_region_bins,
        }  # TODO add the other two kinds
        for type, region_bins_func in types.items():
            config = self.import_config["input"].get(type, None)
            if config is not None:
                for rb in region_bins_func(config):
                    yield BucketId(type, rb)

    def get_variant_loader(self, loader_type, reference_genome=None) \
            -> VariantsLoader:
        assert loader_type in self.import_config["input"],\
            f"No input config for loader {loader_type}"
        if reference_genome is None:
            reference_genome = self.create_gpf_instance().reference_genome

        loader_config = self.import_config["input"][loader_type]
        variants_params = self._add_loader_prefix(loader_config,
                                                  loader_type + "_")

        variants_filenames = loader_config["files"]
        variants_filenames = [fs_utils.join(self.input_dir, f)
                              for f in variants_filenames]
        if loader_type == "denovo":
            assert len(variants_filenames) == 1,\
                "Support for multiple denovo files is NYI"
            variants_filenames = variants_filenames[0]

        loader_cls = {
            "denovo": DenovoLoader,
            "vcf": VcfLoader,
            # TODO add more loaders
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

    def create_gpf_instance(self):
        if self._gpf_instance is None:
            instance_config = self.import_config.get("gpf_instance", {})
            self._gpf_instance = GPFInstance(
                work_dir=instance_config.get("path", None))
        return self._gpf_instance

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

    def _loader_region_bins(self, loader_args, loader_type):
        # TODO pass the gpf instance as argument to this func
        reference_genome = self.create_gpf_instance().reference_genome

        target_chromosomes = loader_args.get("target_chromosomes", None)
        if target_chromosomes is None:
            loader = self.get_variant_loader(loader_type, reference_genome)
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

        yield from variants_targets.keys()


class Schema1ParquetWriter:
    @staticmethod
    def write_variant(variants_loader, bucket_id, gpf_instance, project,
                      out_dir):
        partition_description = project.get_partition_description(
            work_dir=out_dir)

        loader_args = project.import_config["input"][bucket_id.type]
        generator = MakefilePartitionHelper(
            partition_description,
            gpf_instance.reference_genome,
            add_chrom_prefix=loader_args.get("add_chrom_prefix", None),
            del_chrom_prefix=loader_args.get("del_chrom_prefix", None),
        )

        target_chromosomes = loader_args.get("target_chromosomes", None)
        if target_chromosomes is None:
            target_chromosomes = variants_loader.chromosomes

        variants_targets = generator.generate_variants_targets(
            target_chromosomes
        )

        bucket_index = project.get_default_bucket_index(bucket_id.type)
        if bucket_id.region_bin is not None and bucket_id.region_bin != "none":
            assert bucket_id.region_bin in variants_targets, (
                bucket_id.region_bin,
                list(variants_targets.keys()),
            )

            regions = variants_targets[bucket_id.region_bin]
            bucket_index = (
                project.get_default_bucket_index(bucket_id.type)
                + generator.bucket_index(bucket_id.region_bin)
            )
            logger.info(
                f"resetting regions (rb: {bucket_id.region_bin}): {regions}")
            variants_loader.reset_regions(regions)

        variants_loader = project.build_variants_loader_pipeline(
            variants_loader, gpf_instance
        )

        rows = 20_000  # TODO get this from the config?
        logger.debug(f"argv.rows: {rows}")

        ParquetManager.variants_to_parquet(
            variants_loader,
            partition_description,
            bucket_index=bucket_index,
            rows=rows,
        )

    @staticmethod
    def write_pedigree(families, out_dir, partition_description):
        if partition_description:
            if partition_description.family_bin_size > 0:
                families = partition_description \
                    .add_family_bins_to_families(families)

        output_filename = os.path.join(out_dir, "pedigree.parquet")

        ParquetManager.families_to_parquet(families, output_filename)


class HDFSHelper:
    def copy_local_to_hdfs_dir():
        # TODO implement
        pass


class ImpalaSchema1ImportStorage:
    @staticmethod
    def _pedigree_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_pedigree")

    @staticmethod
    def _variants_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_variants")

    @classmethod
    def _do_write_pedigree(cls, project):
        out_dir = cls._pedigree_dir(project)
        Schema1ParquetWriter.write_pedigree(
            project.get_pedigree(), out_dir,
            project.get_partition_description()
        )

    @classmethod
    def _do_write_variant(cls, project, bucket_id):
        out_dir = cls._variants_dir(project)
        gpf_instance = project.create_gpf_instance()
        Schema1ParquetWriter.write_variant(
            project.get_variant_loader(bucket_id.type,
                                       gpf_instance.reference_genome),
            bucket_id,
            gpf_instance,
            project, out_dir)

    @classmethod
    def _do_load_in_hdfs(cls, project):
        gpf_instance = project.create_gpf_instance()
        genotype_storage_db = gpf_instance.genotype_storage_db
        genotype_storage = genotype_storage_db.get_genotype_storage(
            project.genotype_storage_id
        )
        if genotype_storage is None or not genotype_storage.is_impala():
            logger.error("missing or non-impala genotype storage")
            return

        partition_description = project.get_partition_description()

        pedigree_file = fs_utils.join(cls._pedigree_dir(project),
                                      "pedigree.parquet")
        genotype_storage.hdfs_upload_dataset(
            project.study_id,
            cls._variants_dir(project),
            pedigree_file,
            partition_description)

    @classmethod
    def _do_load_in_impala(cls, project):
        gpf_instance = project.create_gpf_instance()
        genotype_storage_db = gpf_instance.genotype_storage_db
        genotype_storage = genotype_storage_db.get_genotype_storage(
            project.genotype_storage_id)

        if genotype_storage is None or not genotype_storage.is_impala():
            logger.error("missing or non-impala genotype storage")
            return

        study_id = project.study_id

        hdfs_variants_dir = \
            genotype_storage.default_variants_hdfs_dirname(study_id)

        hdfs_pedigree_file = \
            genotype_storage.default_pedigree_hdfs_filename(project.study_id)

        logger.info(f"HDFS variants dir: {hdfs_variants_dir}")
        logger.info(f"HDFS pedigree file: {hdfs_pedigree_file}")

        partition_description = project.get_partition_description()

        variants_schema_fn = fs_utils.join(
            cls._variants_dir(project), "_VARIANTS_SCHEMA")
        with open(variants_schema_fn) as infile:
            content = infile.read()
            schema = toml.loads(content)
            variants_schema = schema["variants_schema"]

        genotype_storage.impala_import_dataset(
            project.study_id,
            hdfs_pedigree_file,
            hdfs_variants_dir,
            partition_description=partition_description,
            variants_schema=variants_schema)

    def generate_import_task_graph(self, project) -> TaskGraph:
        G = TaskGraph()
        pedigree_task = G.create_task("ped task", self._do_write_pedigree,
                                      [project], [])

        bucket_tasks = []
        for b in project.get_import_variants_buckets():
            task = G.create_task(f"Task {b}", self._do_write_variant,
                                 [project, b], [])
            bucket_tasks.append(task)

        if project.has_destination():
            hdfs_task = G.create_task(
                "hdfs copy", self._do_load_in_hdfs,
                [project], [pedigree_task] + bucket_tasks)

            G.create_task("impala import", self._do_load_in_impala,
                          [project], [hdfs_task])

        return G


def main():
    parser = argparse.ArgumentParser(description="Import datasets into GPF")
    parser.add_argument("-f", "--config", type=str,
                        help="Path to the import configuration")
    args = parser.parse_args()

    import_config = GPFConfigParser.parse_and_interpolate_file(args.config)
    import_config = GPFConfigParser.validate_config(import_config,
                                                    import_config_schema)
    run(import_config)


def run(import_config, gpf_instance=None):
    project = ImportProject(import_config, gpf_instance)
    storage = ImpalaSchema1ImportStorage()
    task_graph = storage.generate_import_task_graph(project)
    task_graph_executor = SequentialExecutor()
    task_graph_executor.execute(task_graph)
