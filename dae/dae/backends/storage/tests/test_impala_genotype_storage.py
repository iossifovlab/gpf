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

