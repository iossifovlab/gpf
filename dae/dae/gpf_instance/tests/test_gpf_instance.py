# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

def test_init(fixtures_gpf_instance):
    assert fixtures_gpf_instance

    assert fixtures_gpf_instance.dae_config
    print(fixtures_gpf_instance.dae_config)
    assert fixtures_gpf_instance.reference_genome
    assert fixtures_gpf_instance.gene_models
    assert fixtures_gpf_instance._pheno_db
    assert fixtures_gpf_instance.gene_scores_db is not None
    assert fixtures_gpf_instance.genomic_scores_db
    assert fixtures_gpf_instance._variants_db
    assert fixtures_gpf_instance.gene_sets_db
    assert fixtures_gpf_instance.denovo_gene_sets_db is not None
    assert fixtures_gpf_instance._background_facade


def test_eager_init(gpf_instance, global_dae_fixtures_dir):
    fixtures_gpf_instance = gpf_instance(
        work_dir=global_dae_fixtures_dir, load_eagerly=True)

    assert fixtures_gpf_instance

    assert fixtures_gpf_instance.dae_config
    assert fixtures_gpf_instance.reference_genome
    assert fixtures_gpf_instance.gene_models
    assert fixtures_gpf_instance._pheno_db
    assert fixtures_gpf_instance.gene_scores_db is not None
    assert fixtures_gpf_instance.genomic_scores_db
    assert fixtures_gpf_instance._variants_db
    assert fixtures_gpf_instance.gene_sets_db
    assert fixtures_gpf_instance.denovo_gene_sets_db is not None
    assert fixtures_gpf_instance._background_facade


def test_dae_config(fixtures_gpf_instance, global_dae_fixtures_dir):
    dae_config = fixtures_gpf_instance.dae_config

    assert dae_config.conf_dir == global_dae_fixtures_dir


def test_variants_db(fixtures_gpf_instance):
    variants_db = fixtures_gpf_instance._variants_db

    assert len(variants_db.get_all_genotype_data()) == 42
