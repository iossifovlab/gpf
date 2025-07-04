# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import pytest_mock
from dae.testing.import_helpers import setup_dataset_config
from gpf_instance.gpf_instance import WGPFInstance, reload_datasets
from utils.testing import setup_wgpf_instance


@pytest.fixture(scope="module")
def custom_wgpf_module(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("t4c8_wgpf_module")
    gpf_instance = setup_wgpf_instance(root_path)
    setup_dataset_config(gpf_instance, "dataset_1", ["t4c8_study_1"])
    setup_dataset_config(gpf_instance, "dataset_2", ["t4c8_study_2"])
    setup_dataset_config(gpf_instance, "omni_dataset", ["dataset_1",
                                                        "dataset_2"])
    return gpf_instance


@pytest.fixture
def custom_wgpf(
    custom_wgpf_module: WGPFInstance,
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    reload_datasets(custom_wgpf_module)
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=custom_wgpf_module,
    )
    mocker.patch(
        "datasets_api.permissions.get_wgpf_instance",
        return_value=custom_wgpf_module,
    )
    mocker.patch(
        "query_base.query_base.get_wgpf_instance",
        return_value=custom_wgpf_module,
    )
    return custom_wgpf_module
