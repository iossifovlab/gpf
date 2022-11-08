# pylint: disable=W0621,C0114,C0116,W0212,W0613
import cloudpickle  # type: ignore
from dae.import_tools.import_tools import ImportProject


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
