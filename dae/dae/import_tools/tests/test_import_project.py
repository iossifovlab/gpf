# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pytest
import cloudpickle  # type: ignore
from dae.import_tools.import_tools import ImportProject
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture
def fixture_gpf_instance(fixture_dirname):
    gpf_instance = GPFInstance.build(
        os.path.join(fixture_dirname(""), "gpf_instance.yaml"))
    return gpf_instance


def test_import_project_is_cpickle_serializable(fixture_dirname):
    import_config = dict(
        input={},
        gpf_instance={
            "path": fixture_dirname("")
        }
    )
    project = ImportProject.build_from_config(import_config)
    _ = cloudpickle.dumps(project)

    _ = project.get_import_storage()
    _ = cloudpickle.dumps(project)


def test_project_is_serializable_after_loader_reference_genome(
        resources_dir, fixture_gpf_instance):
    config_fn = str(resources_dir / "vcf_import" / "import_config.yaml")
    project = ImportProject.build_from_file(config_fn, fixture_gpf_instance)
    assert project.get_gpf_instance().reference_genome is not None
    pickled = cloudpickle.dumps(project)
    unpickled_project = cloudpickle.loads(pickled)
    assert unpickled_project.get_gpf_instance().reference_genome is not None


def test_project_is_serializable_instance_dir(
        resources_dir, fixture_gpf_instance):
    config_fn = str(resources_dir / "vcf_import" / "import_config.yaml")
    project = ImportProject.build_from_file(config_fn, fixture_gpf_instance)
    assert project.get_gpf_instance().dae_dir is not None
    pickled = cloudpickle.dumps(project)
    unpickled_project = cloudpickle.loads(pickled)
    assert unpickled_project.get_gpf_instance().dae_dir is not None


def test_config_filenames_just_one_config(resources_dir):
    config_fn = str(resources_dir / "vcf_import" / "import_config.yaml")
    project = ImportProject.build_from_file(config_fn)
    assert project.config_filenames == [config_fn]


def test_config_filenames_one_external(resources_dir):
    config_fn = str(resources_dir / "external_input" / "import_config.yaml")
    project = ImportProject.build_from_file(config_fn)
    assert project.config_filenames == [
        config_fn,
        str(resources_dir / "external_input/files/input.yaml")
    ]


def test_config_filenames_embedded_config():
    import_config = dict(
        input={},
    )
    project = ImportProject.build_from_config(import_config)
    assert len(project.config_filenames) == 0


def test_config_filenames_external_input_and_annotation():
    import_config = dict(
        input={},
        annotation=dict(
            file="annotation.yaml"
        )
    )
    project = ImportProject.build_from_config(import_config)
    assert project.config_filenames == ["annotation.yaml"]


def test_tags_on_by_default(resources_dir):
    config_fn = str(resources_dir / "vcf_import" / "import_config.yaml")
    project = ImportProject.build_from_file(config_fn)
    _, params = project.get_pedigree_params()
    assert "ped_tags" in params
    assert params["ped_tags"] is True


@pytest.mark.parametrize("import_config, expected", [
    ({"input": {}}, True),
    ({
        "input": {},
        "destination": {}
    }, True),
    ({
        "input": {},
        "destination": {"storage_id": "storage"}
    }, True),
    ({
        "input": {},
        "destination": {
            "storage_type": "schema2",
            "hdfs": {},
        },
    }, True),
    ({
        "input": {},
        "destination": {"storage_type": "schema2"}
    }, False),
])
def test_has_genotype_storage(import_config, expected):
    project = ImportProject.build_from_config(import_config)
    assert project.has_genotype_storage() == expected
