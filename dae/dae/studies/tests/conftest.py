import os
import pytest

from dae.pheno.pheno_factory import PhenoFactory
from dae.studies.study_wrapper import StudyWrapper
from dae.studies.study_config_parser import StudyConfigParser
from dae.studies.dataset_config_parser import DatasetConfigParser
from dae.studies.variants_db import VariantsDb

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.weights import WeightsLoader

from dae.configuration.dae_config_parser import DAEConfigParser


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
    dae_config = DAEConfigParser.read_and_parse_file_configuration(
        work_dir=fixtures_dir())
    return dae_config


@pytest.fixture(scope='module')
def variants_db_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb


@pytest.fixture(scope='module')
def study_configs(dae_config_fixture):
    study_configs = StudyConfigParser.read_and_parse_directory_configurations(
        dae_config_fixture.studies_db.dir,
        dae_config_fixture.dae_data_dir,
        defaults={'conf': dae_config_fixture.default_configuration.conf_file}
    )
    return {sc.id: sc for sc in study_configs}


@pytest.fixture(scope='module')
def quads_f1_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f1')


@pytest.fixture(scope='module')
def quads_f2_config(variants_db_fixture):
    return variants_db_fixture.get_study_config('quads_f2')


def load_study(variants_db_fixture, study_configs, study_name):
    config = study_configs.get(study_name)

    result = variants_db_fixture.make_study(config)
    assert result is not None
    return result


@pytest.fixture(scope='module')
def inheritance_trio(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'inheritance_trio')


@pytest.fixture(scope='module')
def quads_f1(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_f1')


@pytest.fixture(scope='module')
def quads_f2(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_f2')


@pytest.fixture(scope='module')
def quads_variant_types(variants_db_fixture, study_configs):
    return load_study(
        variants_db_fixture, study_configs, 'quads_variant_types')


@pytest.fixture(scope='module')
def quads_two_families(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_two_families')


@pytest.fixture(scope='module')
def quads_in_child(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_in_child')


@pytest.fixture(scope='module')
def quads_in_parent(variants_db_fixture, study_configs):
    return load_study(variants_db_fixture, study_configs, 'quads_in_parent')


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
    gene_info_config = GeneInfoConfigParser.read_and_parse_file_configuration(
        dae_config_fixture.gene_info_db.conf_file,
        dae_config_fixture.dae_data_dir
    )
    return gene_info_config


@pytest.fixture(scope='module')
def weights_loader(gene_info_config):
    return WeightsLoader(config=gene_info_config.gene_weights)


@pytest.fixture(scope='module')
def dataset_configs(dae_config_fixture):
    dataset_configs = DatasetConfigParser.read_directory_configurations(
        datasets_dir(),
        fixtures_dir(),
        defaults={'conf': dae_config_fixture.default_configuration.conf_file},
        fail_silently=True
    )
    return {
        dc[DatasetConfigParser.SECTION].id: dc for dc in dataset_configs
    }


@pytest.fixture(scope='module')
def quads_composite_dataset_config(variants_db_fixture):
    return variants_db_fixture.get_dataset_config('quads_composite_ds')


@pytest.fixture(scope='module')
def composite_dataset_config(variants_db_fixture):
    return variants_db_fixture.get_dataset_config('composite_dataset_ds')


def load_dataset(variants_db_fixture, dataset_configs, dataset_name):
    config = dataset_configs.get(dataset_name)
    assert config is not None, dataset_name

    result = variants_db_fixture.make_dataset(config)
    assert result is not None
    return result


@pytest.fixture(scope='module')
def inheritance_trio_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'inheritance_trio_ds')


@pytest.fixture(scope='module')
def inheritance_trio_dataset_wrapper(inheritance_trio_dataset, pheno_factory):
    return StudyWrapper(inheritance_trio_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_two_families_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'quads_two_families_ds')


@pytest.fixture(scope='module')
def quads_two_families_dataset_wrapper(quads_two_families_dataset):
    return StudyWrapper(quads_two_families_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_f1_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(variants_db_fixture, dataset_configs, 'quads_f1_ds')


@pytest.fixture(scope='module')
def quads_f1_dataset_wrapper(quads_f1_dataset, pheno_factory):
    return StudyWrapper(quads_f1_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_f2_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(variants_db_fixture, dataset_configs, 'quads_f2_ds')


@pytest.fixture(scope='module')
def quads_f2_dataset_wrapper(quads_f2_dataset, pheno_factory):
    return StudyWrapper(quads_f2_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_variant_types_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'quads_variant_types_ds')


@pytest.fixture(scope='module')
def quads_variant_types_dataset_wrapper(
        quads_variant_types_dataset, pheno_factory):
    return StudyWrapper(quads_variant_types_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_in_child_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'quads_in_child_ds')


@pytest.fixture(scope='module')
def quads_in_child_dataset_wrapper(quads_in_child_dataset, pheno_factory):
    return StudyWrapper(quads_in_child_dataset, pheno_factory)


@pytest.fixture(scope='module')
def quads_in_parent_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'quads_in_parent_ds')


@pytest.fixture(scope='module')
def quads_in_parent_dataset_wrapper(quads_in_parent_dataset, pheno_factory):
    return StudyWrapper(quads_in_parent_dataset, pheno_factory)


@pytest.fixture(scope='module')
def composite_dataset(variants_db_fixture, dataset_configs):
    return load_dataset(
        variants_db_fixture, dataset_configs, 'composite_dataset_ds')


@pytest.fixture(scope='module')
def composite_dataset_wrapper(composite_dataset, pheno_factory):
    return StudyWrapper(composite_dataset, pheno_factory)
