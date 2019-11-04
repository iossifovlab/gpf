def test_get_backend(
        impala_genotype_storage, quads_f1_impala_config, genomes_db):
    assert impala_genotype_storage

    backend = impala_genotype_storage.get_backend(
        quads_f1_impala_config, genomes_db
    )

    assert len(backend.families) == 1
    assert len(backend.families['f1'].members_ids) == 5
    assert len(list(backend.query_variants())) == 3


def test_is_impala(impala_genotype_storage):
    assert impala_genotype_storage.is_impala() is True


def test_is_filestorage(impala_genotype_storage):
    assert impala_genotype_storage.is_filestorage() is False


def test_impala_connection(impala_genotype_storage):
    impala_connection = impala_genotype_storage.impala_connection

    assert impala_connection is not None


def test_impala_helpers(impala_genotype_storage):
    impala_helpers = impala_genotype_storage.impala_helpers

    assert impala_helpers is not None
    assert impala_helpers.connection is not None


def test_hdfs_helpers(impala_genotype_storage):
    hdfs_helpers = impala_genotype_storage.hdfs_helpers

    assert hdfs_helpers is not None

    assert hdfs_helpers.host == 'localhost'
    assert hdfs_helpers.port == 8020
    assert hdfs_helpers.hdfs is not None


