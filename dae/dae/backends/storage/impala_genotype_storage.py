import os
import sys
import glob
from time import time

from dae.backends.raw.loader import VariantsLoader, TransmissionType
from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.impala.hdfs_helpers import HdfsHelpers
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_variants import ImpalaFamilyVariants
from dae.backends.impala.parquet_io import ParquetManager, \
    ParquetPartitionDescriptor

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.utils.dict_utils import recursive_dict_update


class ImpalaGenotypeStorage(GenotypeStorage):

    def __init__(self, storage_config):
        super(ImpalaGenotypeStorage, self).__init__(storage_config)
        self.data_dir = self.storage_config.dir

        impala_hosts = self.storage_config.impala.hosts
        impala_port = self.storage_config.impala.port
        pool_size = self.storage_config.impala.pool_size

        self._impala_helpers = ImpalaHelpers(
            impala_hosts=impala_hosts, impala_port=impala_port,
            pool_size=pool_size
        )
        self._hdfs_helpers = HdfsHelpers(
            self.storage_config.hdfs.host, self.storage_config.hdfs.port
        )

    def get_db(self):
        return self.storage_config.impala.db

    def is_impala(self):
        return True

    def get_hdfs_dir(self, *path):
        hdfs_dirname = os.path.join(self.storage_config.hdfs.base_dir, *path)
        if not self.hdfs_helpers.hdfs.exists(hdfs_dirname):
            self.hdfs_helpers.hdfs.mkdir(hdfs_dirname)

        return hdfs_dirname

    @property
    def impala_helpers(self):
        assert self._impala_helpers is not None
        return self._impala_helpers

    @property
    def hdfs_helpers(self):
        assert self._hdfs_helpers is not None
        return self._hdfs_helpers

    @staticmethod
    def study_tables(study_config):
        storage_config = study_config.genotype_storage
        if (
            storage_config
            and storage_config.tables
            and storage_config.tables.pedigree
            and storage_config.tables.variants
        ):
            variant_table = storage_config.tables.variants
            pedigree_table = storage_config.tables.pedigree
        elif (
            storage_config
            and storage_config.tables
            and storage_config.tables.pedigree
        ):
            variant_table = None
            pedigree_table = storage_config.tables.pedigree
        else:
            # default study tables
            variant_table = "{}_variants".format(study_config.id)
            pedigree_table = "{}_pedigree".format(study_config.id)
        return variant_table, pedigree_table

    def _get_variant_table(self, study_id):
        return f"{study_id}_variants"

    def _get_pedigree_table(self, study_id):
        return f"{study_id}_pedigree"

    def build_backend(self, study_config, genomes_db):
        assert study_config is not None

        variant_table, pedigree_table = self.study_tables(study_config)
        family_variants = ImpalaFamilyVariants(
            self.impala_helpers,
            self.storage_config.impala.db,
            variant_table,
            pedigree_table,
            genomes_db.get_gene_models(),
        )

        return family_variants

    def impala_drop_study_tables(self, study_config):
        for table in self.study_tables(study_config):
            self.impala_helpers.drop_table(self.get_db(), table)

    def _hdfs_parquet_put_files(self, study_id, paths, dirname):
        hdfs_dirname = self.get_hdfs_dir(study_id, dirname)
        if self.hdfs_helpers.exists(hdfs_dirname):
            self.hdfs_helpers.delete(hdfs_dirname, recursive=True)
        for path in paths:
            self.hdfs_helpers.put_content(path, hdfs_dirname)

        return self.hdfs_helpers.list_dir(hdfs_dirname)

    def _hdfs_parquet_put_study_files(
        self, study_id, variant_paths, pedigree_paths
    ):
        print("pedigree_path:", pedigree_paths)
        print("variants_path:", variant_paths)

        pedigree_files = self._hdfs_parquet_put_files(
            study_id, pedigree_paths, "pedigree"
        )

        variant_files = self._hdfs_parquet_put_files(
            study_id, variant_paths, "variants"
        )

        return variant_files, pedigree_files

    def _generate_study_config(
        self, study_id, pedigree_table, variant_table=None
    ):
        assert study_id is not None

        study_config = {
            "id": study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "genotype_storage": {
                "id": self.storage_config.section_id(),
                "tables": {"pedigree": pedigree_table},
            },
            "genotype_browser": {"enabled": False},
        }

        if variant_table:
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["variants"] = variant_table
            study_config["genotype_browser"]["enabled"] = True

        return study_config

    def simple_study_import(
        self,
        study_id,
        families_loader=None,
        variant_loaders=None,
        study_config=None,
        output=".",
        include_reference=False,
    ):

        parquet_pedigrees = []
        parquet_variants = []
        parquet_filenames = None
        has_denovo = False
        has_cnv = False
        if variant_loaders:
            for index, variant_loader in enumerate(variant_loaders):
                assert isinstance(variant_loader, VariantsLoader), type(
                    variant_loader
                )

                if variant_loader.get_attribute("source_type") == "denovo":
                    has_denovo = True

                if variant_loader.get_attribute("source_type") == "cnv":
                    has_denovo = True
                    has_cnv = True

                if variant_loader.transmission_type == TransmissionType.denovo:
                    assert index < 100

                    bucket_index = index  # denovo buckets < 100
                elif (
                    variant_loader.transmission_type
                    == TransmissionType.transmitted
                ):
                    bucket_index = index + 100  # transmitted buckets (>=100)

                parquet_filenames = ParquetManager.build_parquet_filenames(
                    output, bucket_index=bucket_index, study_id=study_id
                )
                ParquetManager.variants_to_parquet_filename(
                    variant_loader,
                    parquet_filenames.variant,
                    bucket_index=bucket_index,
                    include_reference=include_reference
                )
                parquet_variants.append(parquet_filenames.variant)
        else:
            parquet_filenames = ParquetManager.build_parquet_filenames(
                output, bucket_index=0, study_id=study_id
            )

        print("variants and families saved in:", parquet_filenames)
        families = families_loader.load()

        ParquetManager.families_to_parquet(
            families, parquet_filenames.pedigree
        )

        parquet_pedigrees.append(parquet_filenames.pedigree)

        # study_dir = os.path.join(self.data_dir, study_id)

        config_dict = self.impala_load_study(
            study_id,
            variant_paths=parquet_variants,
            pedigree_paths=parquet_pedigrees,
        )

        config_dict["has_denovo"] = has_denovo
        config_dict["has_cnv"] = has_cnv

        if study_config is not None:
            study_config_dict = GPFConfigParser.load_config_raw(study_config)
            config_dict = recursive_dict_update(config_dict, study_config_dict)

        config_builder = StudyConfigBuilder(config_dict)

        return config_builder.build_config()

    def hdfs_upload_study(self, study_id, variant_paths=[], pedigree_paths=[]):
        assert variant_paths is not None
        assert pedigree_paths

        return self._hdfs_parquet_put_study_files(
                study_id, variant_paths, pedigree_paths)

    def impala_import_study(
            self, study_id, variant_hdfs_path,
            pedigree_hdfs_path, has_variants):
        db = self.storage_config.impala.db
        pedigree_table = self._get_pedigree_table(study_id)
        variant_table = self._get_variant_table(study_id)
        print(
            f"Loading `{study_id}` study in impala "
            f"`{self.storage_config.db}` db; "
            f"variants from hdfs: {variant_hdfs_path}; "
            f"pedigrees from hdfs: {pedigree_hdfs_path}",
            file=sys.stderr,
        )
        start = time()

        self.impala_helpers.drop_table(db, variant_table)
        self.impala_helpers.drop_table(db, pedigree_table)
        self.impala_helpers.import_variants(
            db,
            variant_table,
            pedigree_table,
            variant_hdfs_path,
            pedigree_hdfs_path,
        )

        end = time()
        total = end - start
        print(
            f"Loaded `{study_id}` study in impala `{self.storage_config.db}` "
            f"db for {total:.2f} sec",
            file=sys.stderr,
        )
        return self._generate_study_config(
            study_id, pedigree_table, variant_table if has_variants else None
        )

    def impala_load_study(self, study_id, variant_paths=[], pedigree_paths=[]):
        variant_hdfs_path, pedigree_hdfs_path = \
                self.hdfs_upload_study(study_id, variant_paths, pedigree_paths)

        has_variants = len(variant_paths)

        return self.impala_import_study(
            study_id, variant_hdfs_path, pedigree_hdfs_path, has_variants)

    def hdfs_upload_dataset(
            self, study_id, variants_path,
            pedigree_file, partition_descriptor):

        files_glob = partition_descriptor.generate_file_access_glob()
        files_glob = os.path.join(variants_path, files_glob)
        variants_files = glob.glob(files_glob)

        study_path = os.path.join(self.storage_config.hdfs.base_dir, study_id)
        variants_hdfs_path = os.path.join(study_path, "variants")
        for parquet_file in variants_files:
            file_dir = os.path.dirname(parquet_file)
            file_dir = file_dir[file_dir.find("region_bin"):]
            file_hdfs_dir = os.path.join(variants_hdfs_path, file_dir)
            self.hdfs_helpers.makedirs(file_hdfs_dir)
            self.hdfs_helpers.put_in_directory(parquet_file, file_hdfs_dir)

        pedigree_hdfs_path = os.path.join(
            study_path, "pedigree", "pedigree.ped"
        )

        self.hdfs_helpers.put(pedigree_file, pedigree_hdfs_path)

        variants_files = list(
            map(lambda f: f[f.find("region_bin"):], variants_files)
        )

        # TODO: Find valid workaround to avoid passing back these 3
        return (variants_files, variants_hdfs_path, pedigree_hdfs_path)

    def impala_import_dataset(
            self, study_id, variants_files, variants_hdfs_path,
            pedigree_hdfs_path, partition_descriptor):

        pedigree_table = self._get_pedigree_table(study_id)
        variants_table = self._get_variant_table(study_id)

        db = self.storage_config.impala.db

        self.impala_helpers.drop_table(db, variants_table)
        self.impala_helpers.drop_table(db, pedigree_table)

        self.impala_helpers.import_dataset_into_db(
            db,
            variants_table,
            pedigree_table,
            partition_descriptor,
            pedigree_hdfs_path,
            variants_hdfs_path,
            variants_files,
        )

        return self._generate_study_config(
            study_id, pedigree_table, variants_table
        )

    def impala_load_dataset(self, study_id, variants_path, pedigree_file):
        partition_config_file = os.path.join(
            variants_path, "_PARTITION_DESCRIPTION"
        )
        assert os.path.exists(partition_config_file)

        partition_descriptor = ParquetPartitionDescriptor.from_config(
            partition_config_file, root_dirname=variants_path
        )

        variants_files, variants_hdfs_path, pedigree_hdfs_path = \
            self.hdfs_upload_dataset(
                study_id, variants_path, pedigree_file, partition_descriptor)

        return self.impala_import_dataset(
            study_id, variants_files, variants_hdfs_path,
            pedigree_hdfs_path, partition_descriptor)


STUDY_CONFIG_TEMPLATE = """
id = "{id}"
conf_dir = "."

[genotype_storage]
id = "{genotype_storage}"

[genotype_storage.tables]
pedigree = "{pedigree_table}"
variants = "{variant_table}"
"""
