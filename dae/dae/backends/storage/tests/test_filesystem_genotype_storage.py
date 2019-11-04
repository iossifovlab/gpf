def test_get_backend(
        filesystem_genotype_storage, quads_f1_vcf_config, genomes_db):
    assert filesystem_genotype_storage

    backend = filesystem_genotype_storage.get_backend(
        quads_f1_vcf_config, genomes_db
    )

    assert len(backend.families) == 1
    assert len(backend.families['f1'].members_ids) == 5
    assert len(list(backend.query_variants())) == 3


def test_is_impala(filesystem_genotype_storage):
    assert filesystem_genotype_storage.is_impala() is False


def test_is_filestorage(filesystem_genotype_storage):
    assert filesystem_genotype_storage.is_filestorage() is True
