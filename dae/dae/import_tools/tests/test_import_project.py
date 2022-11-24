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
