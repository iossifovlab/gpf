# pylint: disable=W0621,C0114,C0116,W0212,W0613
from box import Box  # type: ignore
from dae.backends.storage.schema2_genotype_storage import \
    Schema2GenotypeStorage


def test_hdfs_upload_dataset():
    config = {
        "section_id": "genotype_impala",
        "impala": {
            "hosts": ["localhost"],
            "port": 21050,
            "pool_size": 3,
        },
        "hdfs": {
            "host": "locahost",
            "port": 8020,
        },
    }
    config = Box(config)

    Schema2GenotypeStorage(config, "genotype_impala")
    # storage.hdfs_upload_dataset("study_id", variants_dir, pedigree_file,
    #                             meta_file, partition_description)
