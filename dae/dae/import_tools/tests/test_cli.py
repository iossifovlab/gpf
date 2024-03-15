# pylint: disable=W0621,C0114,C0116,W0212,W0613

import shutil
import pathlib
import yaml

import pytest
import pytest_mock

from dae.import_tools import import_tools, cli
from dae.testing.alla_import import alla_gpf
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture()
def gpf_instance(tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp(__name__)
    return alla_gpf(root_path)


@pytest.fixture()
def simple_study_dir(
    tmp_path: pathlib.Path, gpf_instance: GPFInstance,
    mocker: pytest_mock.MockerFixture,
    resources_dir: pathlib.Path
) -> pathlib.Path:
    shutil.copytree(
        resources_dir / "vcf_import", tmp_path, dirs_exist_ok=True
    )

    # copyint to hdfs and impala is too slow so we remove that step
    config_fn = str(tmp_path / "import_config.yaml")
    with open(config_fn, "rt") as file:
        config = yaml.safe_load(file.read())
    config["destination"] = {
        "id": "genotype_inmemory",
        "storage_type": "inmemory",
        "dir": str(tmp_path),
    }  # don't import into impala
    with open(config_fn, "wt") as file:
        yaml.safe_dump(config, file)

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance)
    mocker.patch.object(import_tools.ImportProject, "work_dir",
                        new=str(tmp_path))
    return tmp_path


def test_run(simple_study_dir: pathlib.Path) -> None:
    import_config_fn = str(simple_study_dir / "import_config.yaml")
    assert cli.main([import_config_fn, "-j", "1"]) == 0


def test_list(simple_study_dir: pathlib.Path) -> None:
    import_config_fn = str(simple_study_dir / "import_config.yaml")
    assert cli.main([import_config_fn, "list"]) == 0
    assert cli.main([import_config_fn, "-j", "1"]) == 0
    assert cli.main([import_config_fn, "list"]) == 0
    assert cli.main([import_config_fn, "list", "--verbose"]) == 0
