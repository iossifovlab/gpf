import pytest
import os

from dae.studies.study_wrapper import StudyWrapper
from dae_conftests.dae_conftests import get_global_dae_fixtures_dir


def fixtures_dir():
    return get_global_dae_fixtures_dir()


def studies_dir():
    return os.path.abspath(
        os.path.join(fixtures_dir(), 'studies'))


def genotype_data_groups_dir():
    return os.path.abspath(
        os.path.join(fixtures_dir(), 'datasets'))


@pytest.fixture(scope='session')
def local_gpf_instance(gpf_instance):
    return gpf_instance(work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def mocked_gene_models(local_gpf_instance):
    return local_gpf_instance.genomes_db.get_gene_models()


@pytest.fixture(scope='session')
def dae_config_fixture(local_gpf_instance):
    return local_gpf_instance.dae_config


@pytest.fixture(scope='session')
def variants_db_fixture(local_gpf_instance):
    return local_gpf_instance._variants_db


@pytest.fixture(scope='session')
def pheno_db(local_gpf_instance):
    return local_gpf_instance._pheno_db


@pytest.fixture(scope='session')
def gene_weights_db(local_gpf_instance):
    return local_gpf_instance.gene_weights_db


@pytest.fixture(scope='session')
def genotype_storage_factory(local_gpf_instance):
    return local_gpf_instance.genotype_storage_db


@pytest.fixture(scope='session')
def genotype_data_study_configs(variants_db_fixture):
    return variants_db_fixture.genotype_data_study_configs


@pytest.fixture(scope='session')
def quads_f1_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f1')


@pytest.fixture(scope='session')
def quads_f2_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f2')


def load_study(variants_db_fixture, genotype_data_study_configs, study_name):
    config = genotype_data_study_configs.get(study_name)

    result = variants_db_fixture.make_genotype_data_study(config)
    assert result is not None
    return result


@pytest.fixture(scope='session')
def inheritance_trio(variants_db_fixture, genotype_data_study_configs):
    return load_study(
        variants_db_fixture, genotype_data_study_configs, 'inheritance_trio')


@pytest.fixture(scope='session')
def quads_f1(variants_db_fixture, genotype_data_study_configs):
    return load_study(
       variants_db_fixture, genotype_data_study_configs, 'quads_f1')


@pytest.fixture(scope='session')
def quads_f2(variants_db_fixture, genotype_data_study_configs):
    return load_study(
       variants_db_fixture, genotype_data_study_configs, 'quads_f2')


@pytest.fixture(scope='session')
def quads_variant_types(variants_db_fixture, genotype_data_study_configs):
    return load_study(
        variants_db_fixture,
        genotype_data_study_configs,
        'quads_variant_types'
    )


@pytest.fixture(scope='session')
def quads_two_families(variants_db_fixture, genotype_data_study_configs):
    return load_study(
        variants_db_fixture, genotype_data_study_configs, 'quads_two_families')


@pytest.fixture(scope='session')
def quads_in_child(variants_db_fixture, genotype_data_study_configs):
    return load_study(
        variants_db_fixture, genotype_data_study_configs, 'quads_in_child')


@pytest.fixture(scope='session')
def quads_in_parent(variants_db_fixture, genotype_data_study_configs):
    return load_study(
        variants_db_fixture, genotype_data_study_configs, 'quads_in_parent')


@pytest.fixture(scope='session')
def inheritance_trio_wrapper(inheritance_trio, pheno_db, gene_weights_db):
    return StudyWrapper(inheritance_trio, pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_f1_wrapper(quads_f1, pheno_db, gene_weights_db):
    return StudyWrapper(quads_f1, pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_f2_wrapper(quads_f2, pheno_db, gene_weights_db):
    return StudyWrapper(quads_f2, pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_variant_types_wrapper(
        quads_variant_types, pheno_db, gene_weights_db):
    return StudyWrapper(quads_variant_types, pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_two_families_wrapper(
        quads_two_families, pheno_db, gene_weights_db):
    return StudyWrapper(quads_two_families, pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_in_child_wrapper(quads_in_child, pheno_db, gene_weights_db):
    return StudyWrapper(quads_in_child, pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_in_parent_wrapper(quads_in_parent, pheno_db, gene_weights_db):
    return StudyWrapper(quads_in_parent, pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def genotype_data_group_configs(variants_db_fixture):
    return variants_db_fixture.genotype_data_group_configs


@pytest.fixture(scope='session')
def quads_composite_genotype_data_group_config(variants_db_fixture):
    return variants_db_fixture.get_genotype_data_group_config(
        'quads_composite_ds'
    )


@pytest.fixture(scope='session')
def composite_dataset_config(variants_db_fixture):
    return variants_db_fixture.get_genotype_data_group_config(
        'composite_dataset_ds'
    )


def load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs,
        genotype_data_group_name):
    config = genotype_data_group_configs.get(genotype_data_group_name)
    assert config is not None, genotype_data_group_name

    result = variants_db_fixture.make_genotype_data_group(config)
    assert result is not None
    return result


@pytest.fixture(scope='session')
def inheritance_trio_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs):
    return load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs,
        'inheritance_trio_ds')


@pytest.fixture(scope='session')
def inheritance_trio_genotype_data_group_wrapper(
        inheritance_trio_genotype_data_group, pheno_db, gene_weights_db):
    return StudyWrapper(
        inheritance_trio_genotype_data_group, pheno_db, gene_weights_db
    )


@pytest.fixture(scope='session')
def quads_two_families_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs):
    return load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs,
        'quads_two_families_ds')


@pytest.fixture(scope='session')
def quads_two_families_genotype_data_group_wrapper(
        quads_two_families_genotype_data_group, pheno_db, gene_weights_db):
    return StudyWrapper(
        quads_two_families_genotype_data_group, pheno_db, gene_weights_db
    )


@pytest.fixture(scope='session')
def quads_f1_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs):
    return load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs, 'quads_f1_ds')


@pytest.fixture(scope='session')
def quads_f1_genotype_data_group_wrapper(
        quads_f1_genotype_data_group, pheno_db, gene_weights_db):
    return StudyWrapper(quads_f1_genotype_data_group,
                        pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_f2_genotype_data_group(variants_db_fixture,
                                 genotype_data_group_configs):
    return load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs, 'quads_f2_ds')


@pytest.fixture(scope='session')
def quads_f2_genotype_data_group_wrapper(quads_f2_genotype_data_group,
                                         pheno_db, gene_weights_db):
    return StudyWrapper(quads_f2_genotype_data_group,
                        pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_variant_types_genotype_data_group(variants_db_fixture,
                                            genotype_data_group_configs):
    return load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs,
        'quads_variant_types_ds')


@pytest.fixture(scope='session')
def quads_variant_types_genotype_data_group_wrapper(
        quads_variant_types_genotype_data_group, pheno_db, gene_weights_db):
    return StudyWrapper(
        quads_variant_types_genotype_data_group, pheno_db, gene_weights_db
    )


@pytest.fixture(scope='session')
def quads_in_child_genotype_data_group(variants_db_fixture,
                                       genotype_data_group_configs):
    return load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs, 'quads_in_child_ds')


@pytest.fixture(scope='session')
def quads_in_child_genotype_data_group_wrapper(
        quads_in_child_genotype_data_group, pheno_db, gene_weights_db):
    return StudyWrapper(quads_in_child_genotype_data_group,
                        pheno_db, gene_weights_db)


@pytest.fixture(scope='session')
def quads_in_parent_genotype_data_group(variants_db_fixture,
                                        genotype_data_group_configs):
    return load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs,
        'quads_in_parent_ds')


@pytest.fixture(scope='session')
def quads_in_parent_genotype_data_group_wrapper(
        quads_in_parent_genotype_data_group, pheno_db, gene_weights_db):
    return StudyWrapper(
        quads_in_parent_genotype_data_group, pheno_db, gene_weights_db
    )


@pytest.fixture(scope='session')
def composite_dataset(variants_db_fixture, genotype_data_group_configs):
    return load_genotype_data_group(
        variants_db_fixture, genotype_data_group_configs,
        'composite_dataset_ds')


@pytest.fixture(scope='session')
def composite_dataset_wrapper(
        composite_dataset, pheno_db, gene_weights_db):
    return StudyWrapper(composite_dataset, pheno_db, gene_weights_db)
