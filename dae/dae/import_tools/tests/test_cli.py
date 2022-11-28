# pylint: disable=W0621,C0114,C0116,W0212,W0613

import shutil
import yaml
import pytest
from dae.import_tools import import_tools, cli


@pytest.fixture()
def simple_study_dir(tmpdir, gpf_instance_grch38, mocker, resources_dir):
    shutil.copytree(
        resources_dir / "vcf_import", tmpdir, dirs_exist_ok=True
    )

    # copyint to hdfs and impala is too slow so we remove that step
    config_fn = str(tmpdir / "import_config.yaml")
    with open(config_fn, "rt") as file:
        config = yaml.safe_load(file.read())
    del config["destination"]
    with open(config_fn, "wt") as file:
        yaml.safe_dump(config, file)

    mocker.patch.object(import_tools.ImportProject, "get_gpf_instance",
                        return_value=gpf_instance_grch38)
    mocker.patch.object(import_tools.ImportProject, "work_dir",
                        new=str(tmpdir))
    return tmpdir


def test_run(simple_study_dir):
    cli.main([str(simple_study_dir / "import_config.yaml"), "-j", "1"])


def test_list(simple_study_dir):
    cli.main([str(simple_study_dir / "import_config.yaml"), "list"])
    cli.main([str(simple_study_dir / "import_config.yaml"), "-j", "1"])
    cli.main([str(simple_study_dir / "import_config.yaml"), "list"])
