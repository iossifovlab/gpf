# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import logging

import pytest

from dae.genotype_storage.genotype_storage_registry import \
    GenotypeStorageRegistry, GenotypeStorage

pytest_plugins = ["dae_conftests.dae_conftests"]
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def hdfs_host() -> str:
    return os.environ.get("DAE_HDFS_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_host() -> str:
    return os.environ.get("DAE_IMPALA_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def impala_genotype_storage(
        request: pytest.FixtureRequest,
        hdfs_host: str,
        impala_host: str) -> GenotypeStorage:

    storage_config = {
        "id": "impala2_test_storage",
        "storage_type": "impala2",
        "impala": {
            "hosts": [impala_host],
            "port": 21050,
            "db": "impala_test_db",
            "pool_size": 5,
        },
        "hdfs": {
            "host": hdfs_host,
            "port": 8020,
            "base_dir": "/tmp/test_data"},
    }
    registry = GenotypeStorageRegistry()
    registry.register_storage_config(storage_config)

    def fin() -> None:
        registry.shutdown()

    request.addfinalizer(fin)

    return registry.get_genotype_storage("impala2_test_storage")


# def collect_vcf(dirname: str) -> list[str]:
#     result = []
#     pattern = os.path.join(dirname, "*.vcf")
#     for filename in glob.glob(pattern):
#         prefix = os.path.splitext(filename)[0]
#         vcf_config = from_prefix_vcf(prefix)
#         result.append(vcf_config)
#     return result


# DATA_IMPORT_COUNT = 0


# @pytest.fixture(scope="session")
# def data_import(
#         request,
#         hdfs_host,
#         impala_host,
#         impala_genotype_storage,
#         reimport,
#         default_dae_config,
#         gpf_instance_2013):

#     global DATA_IMPORT_COUNT
#     DATA_IMPORT_COUNT += 1

#     assert DATA_IMPORT_COUNT == 1

#     from impala_storage.helpers.hdfs_helpers import HdfsHelpers

#     hdfs = HdfsHelpers(hdfs_host, 8020)

#     temp_dirname = hdfs.tempdir(prefix="variants_", suffix="_data")
#     hdfs.mkdir(temp_dirname)

#     def fin():
#         hdfs.delete(temp_dirname, recursive=True)

#     request.addfinalizer(fin)

#     from impala_storage.helpers.impala_helpers import ImpalaHelpers

#     impala_helpers = ImpalaHelpers(
#         impala_hosts=[impala_host], impala_port=21050)
#     gpf_instance_2013.genotype_storages.register_genotype_storage(
#         impala_genotype_storage)

#     def build(dirname):

#         if not impala_helpers.check_database(impala_test_dbname()):
#             impala_helpers.create_database(impala_test_dbname())

#         vcfdirname = relative_to_this_test_folder(
#             os.path.join("fixtures", dirname)
#         )
#         vcf_configs = collect_vcf(vcfdirname)

#         for config in vcf_configs:
#             logger.debug("importing: %s", config)

#             study_id = study_id_from_path(config.pedigree)
#             (variant_table, pedigree_table) = \
#                 impala_genotype_storage.study_tables(
#                     FrozenBox({"id": study_id}))

#             if not reimport and \
#                     impala_helpers.check_table(
#                         impala_test_dbname(), variant_table) and \
#                     impala_helpers.check_table(
#                         impala_test_dbname(), pedigree_table):
#                 continue

#             import_project = _import_project_from_prefix_config(
#                 config, temp_dirname, gpf_instance_2013)

#             run_with_project(import_project)

#     build("backends/")
#     return True


# @pytest.fixture(scope="session")
# def variants_impala(
#         request, data_import, impala_genotype_storage, gpf_instance_2013):

#     def builder(path):
#         study_id = os.path.basename(path)
#         fvars = impala_genotype_storage.build_backend(
#             FrozenBox({"id": study_id}),
#             gpf_instance_2013.reference_genome,
#             gpf_instance_2013.gene_models
#         )
#         return fvars

#     return builder
