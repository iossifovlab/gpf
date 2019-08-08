import os
import pytest

from pheno.pheno_factory import PhenoFactory
from studies.study_factory import StudyFactory
from studies.study_facade import StudyFacade
from studies.study_wrapper import StudyWrapper
from studies.study_config_parser import StudyConfigParser
from studies.dataset_factory import DatasetFactory
from studies.dataset_facade import DatasetFacade
from studies.dataset_config_parser import DatasetConfigParser
from studies.factory import VariantsDb

from gene.config import GeneInfoConfigParser
from gene.weights import WeightsLoader

from configuration.configuration import DAEConfig


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def studies_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/studies'))


def datasets_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/datasets'))


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig.make_config(fixtures_dir())
    return dae_config


@pytest.fixture(scope='module')
def study_configs(dae_config_fixture):
    study_configs = StudyConfigParser.read_directory_configurations(
        dae_config_fixture.studies_dir,
        dae_config_fixture.dae_data_dir,
        default_conf=dae_config_fixture.default_configuration_conf
    )
    return {
        sc[StudyConfigParser.SECTION].id: sc for sc in study_configs
    }


@pytest.fixture(scope='module')
def study_factory(dae_config_fixture):
    return StudyFactory(dae_config_fixture)


@pytest.fixture(scope='module')
def study_facade(
        dae_config_fixture, study_factory, study_configs, pheno_factory):
    return StudyFacade(
        dae_config_fixture,
        pheno_factory,
        study_factory=study_factory, study_configs=study_configs.values())


@pytest.fixture(scope='module')
def quads_f1_config(study_facade):
    return study_facade.get_study_config('quads_f1')


@pytest.fixture(scope='module')
def quads_f2_config(study_facade):
    return study_facade.get_study_config('quads_f2')


def load_study(study_factory, study_configs, study_name):
    config = study_configs.get(study_name)

    result = study_factory.make_study(config)
    assert result is not None
    return result


@pytest.fixture(scope='module')
def inheritance_trio(study_factory, study_configs):
    return load_study(study_factory, study_configs, 'inheritance_trio')


@pytest.fixture(scope='module')
def quads_f1(study_factory, study_configs):
    return load_study(study_factory, study_configs, 'quads_f1')


@pytest.fixture(scope='module')
def quads_f2(study_factory, study_configs):
    return load_study(study_factory, study_configs, 'quads_f2')


@pytest.fixture(scope='module')
def quads_variant_types(study_factory, study_configs):
    return load_study(study_factory, study_configs, 'quads_variant_types')


@pytest.fixture(scope='module')
def quads_two_families(study_factory, study_configs):
    return load_study(study_factory, study_configs, 'quads_two_families')


@pytest.fixture(scope='module')
def quads_in_child(study_factory, study_configs):
    return load_study(study_factory, study_configs, 'quads_in_child')


@pytest.fixture(scope='module')
def quads_in_parent(study_factory, study_configs):
    return load_study(study_factory, study_configs, 'quads_in_parent')


@pytest.fixture(scope='module')
def inheritance_trio_wrapper(inheritance_trio, pheno_factory):
    return StudyWrapper(inheritance_trio, pheno_factory)


@pytest.fixture(scope='module')
def quads_f1_wrapper(quads_f1, pheno_factory):
    return StudyWrapper(quads_f1, pheno_factory)


@pytest.fixture(scope='module')
def quads_f2_wrapper(quads_f2, pheno_factory):
    return StudyWrapper(quads_f2, pheno_factory)


@pytest.fixture(scope='module')
def quads_variant_types_wrapper(quads_variant_types, pheno_factory):
    return StudyWrapper(quads_variant_types, pheno_factory)


@pytest.fixture(scope='module')
def quads_two_families_wrapper(quads_two_families, pheno_factory):
    return StudyWrapper(quads_two_families, pheno_factory)


@pytest.fixture(scope='module')
def quads_in_child_wrapper(quads_in_child, pheno_factory):
    return StudyWrapper(quads_in_child, pheno_factory)


@pytest.fixture(scope='module')
def quads_in_parent_wrapper(quads_in_parent, pheno_factory):
    return StudyWrapper(quads_in_parent, pheno_factory)


@pytest.fixture(scope='module')
def pheno_factory(dae_config_fixture):
    return PhenoFactory(dae_config_fixture)


@pytest.fixture(scope='module')
def gene_info_config(dae_config_fixture):
    gene_info_config = GeneInfoConfigParser.read_file_configuration(
        dae_config_fixture.gene_info_conf, dae_config_fixture.dae_data_dir)
    gene_info_config = GeneInfoConfigParser.parse(gene_info_config)
    return gene_info_config


@pytest.fixture(scope='module')
def weights_loader(gene_info_config):
    return WeightsLoader(config=gene_info_config.gene_weights)


@pytest.fixture(scope='module')
def dataset_configs(dae_config_fixture):
    dataset_configs = DatasetConfigParser.read_directory_configurations(
        datasets_dir(),
        fixtures_dir(),
        default_conf=dae_config_fixture.default_configuration_conf,
        fail_silently=True
    )
    return {
        dc[DatasetConfigParser.SECTION].id: dc for dc in dataset_configs
    }


@pytest.fixture(scope='module')
def dataset_facade(dataset_configs, dataset_factory, pheno_factory):
    return DatasetFacade(
        dataset_configs.values(), dataset_factory, pheno_factory)


@pytest.fixture(scope='module')
def quads_composite_dataset_config(dataset_facade):
    return dataset_facade.get_dataset_config('quads_composite_ds')


@pytest.fixture(scope='module')
def composite_dataset_config(dataset_facade):
    return dataset_facade.get_dataset_config('composite_dataset_ds')


@pytest.fixture(scope='module')
def dataset_factory(study_facade):
    return DatasetFactory(study_facade=study_facade)


def load_dataset(dataset_factory, dataset_configs, dataset_name):
    config = dataset_configs.get(dataset_name)
    assert config is not None, dataset_name

    result = dataset_factory.make_dataset(config)
    assert result is not None
    return result


@pytest.fixture(scope='module')
def inheritance_trio_dataset(dataset_factory, dataset_configs):
    return load_dataset(
        dataset_factory, dataset_configs, 'inheritance_trio_ds')


@pytest.fixture(scope='module')
def inheritance_trio_dataset_wrapper(inheritance_trio_dataset, pheno_factory):
    return StudyWrapper(inheritance_trio_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_two_families_dataset(dataset_factory, dataset_configs):
    return load_dataset(
        dataset_factory, dataset_configs, 'quads_two_families_ds')


@pytest.fixture(scope='module')
def quads_two_families_dataset_wrapper(quads_two_families_dataset):
    return StudyWrapper(quads_two_families_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_f1_dataset(dataset_factory, dataset_configs):
    return load_dataset(
        dataset_factory, dataset_configs, 'quads_f1_ds')


@pytest.fixture(scope='module')
def quads_f1_dataset_wrapper(quads_f1_dataset, pheno_factory):
    return StudyWrapper(quads_f1_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_f2_dataset(dataset_factory, dataset_configs):
    return load_dataset(
        dataset_factory, dataset_configs, 'quads_f2_ds')


@pytest.fixture(scope='module')
def quads_f2_dataset_wrapper(quads_f2_dataset, pheno_factory):
    return StudyWrapper(quads_f2_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_variant_types_dataset(dataset_factory, dataset_configs):
    return load_dataset(
        dataset_factory, dataset_configs, 'quads_variant_types_ds')


@pytest.fixture(scope='module')
def quads_variant_types_dataset_wrapper(
        quads_variant_types_dataset, pheno_factory):
    return StudyWrapper(quads_variant_types_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_in_child_dataset(dataset_factory, dataset_configs):
    return load_dataset(
        dataset_factory, dataset_configs, 'quads_in_child_ds')


@pytest.fixture(scope='module')
def quads_in_child_dataset_wrapper(quads_in_child_dataset, pheno_factory):
    return StudyWrapper(quads_in_child_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_in_parent_dataset(dataset_factory, dataset_configs):
    return load_dataset(
        dataset_factory, dataset_configs, 'quads_in_parent_ds')


@pytest.fixture(scope='module')
def quads_in_parent_dataset_wrapper(quads_in_parent_dataset, pheno_factory):
    return StudyWrapper(quads_in_parent_dataset, pheno_factory)


@pytest.fixture(scope='module')
def composite_dataset(dataset_factory, dataset_configs):
    return load_dataset(
        dataset_factory, dataset_configs, 'composite_dataset_ds')


@pytest.fixture(scope='module')
def composite_dataset_wrapper(composite_dataset, pheno_factory):
    return StudyWrapper(composite_dataset, pheno_factory)


@pytest.fixture(scope='module')
def variants_db_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb
