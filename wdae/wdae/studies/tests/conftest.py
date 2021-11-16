import pytest
import toml
from pathlib import Path
from studies.study_wrapper import RemoteStudyWrapper, StudyWrapper
from studies.remote_study import RemoteGenotypeData
from dae.studies.study import GenotypeDataStudy
from dae.configuration.gpf_config_parser import FrozenBox
from dae.utils.dict_utils import recursive_dict_update
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture(scope="session")
def remote_dir():
    return Path(__file__).parents[4].joinpath("data/data-hg19-remote")


@pytest.fixture(scope="session")
def remote_studies_dir(remote_dir):
    return remote_dir.joinpath("studies")


@pytest.fixture(scope="session")
def local_gpf_instance(remote_dir):
    return GPFInstance(work_dir=remote_dir)


@pytest.fixture(scope="session")
def iossifov_2014_local_config(remote_studies_dir, remote_dir):
    study_dir = remote_studies_dir.joinpath("iossifov_2014")
    filename = study_dir.joinpath("iossifov_2014.conf")
    file_content = ""

    with open(filename, "r") as infile:
        file_content = infile.read()

    config = toml.loads(file_content)

    files = config["genotype_storage"]["files"]
    files["pedigree"]["path"] = str(
        study_dir.joinpath("data", "iossifov2014_families.ped")
    )
    files["variants"][0]["path"] = str(
        study_dir.joinpath("data", "iossifov2014.txt")
    )

    default_config_filename = remote_dir.joinpath("defaultConfiguration.conf")
    with open(default_config_filename, "r") as infile:
        file_content = infile.read()

    default_config = toml.loads(file_content)

    config = recursive_dict_update(default_config, config)

    return FrozenBox(config)


@pytest.fixture(scope="session")
def iossifov_2014_local(
        local_gpf_instance, remote_studies_dir, iossifov_2014_local_config):
    assert remote_studies_dir.exists()

    storage_db = local_gpf_instance.genotype_storage_db
    genotype_storage = storage_db.get_genotype_storage(
        iossifov_2014_local_config.genotype_storage.id
    )

    variants = genotype_storage.build_backend(
        iossifov_2014_local_config, local_gpf_instance.genomes_db)

    data_study = GenotypeDataStudy(
        iossifov_2014_local_config, variants)

    return StudyWrapper(
        data_study,
        local_gpf_instance._pheno_db,
        local_gpf_instance.gene_weights_db
    )


@pytest.fixture(scope="function")
def iossifov_2014_remote(rest_client):
    return RemoteStudyWrapper(
        RemoteGenotypeData("iossifov_2014", rest_client)
    )


@pytest.fixture(scope="function")
def iossifov_2014_wrappers(iossifov_2014_local, iossifov_2014_remote):
    return {
        "local": iossifov_2014_local,
        "remote": iossifov_2014_remote
    }
