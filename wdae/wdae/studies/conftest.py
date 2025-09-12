# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import pytest_mock
from dae.testing.import_helpers import setup_dataset_config
from gpf_instance.gpf_instance import WGPFInstance, reload_datasets
from utils.testing import setup_wgpf_instance

from studies.query_transformer import QueryTransformer
from studies.response_transformer import ResponseTransformer


@pytest.fixture(scope="module")
def custom_wgpf_module(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("custom_wgpf_module_studies")
    gpf_instance = setup_wgpf_instance(root_path)
    setup_dataset_config(gpf_instance, "dataset_1", ["t4c8_study_1"])
    setup_dataset_config(gpf_instance, "dataset_2", ["t4c8_study_2"])
    setup_dataset_config(gpf_instance, "omni_dataset", ["dataset_1",
                                                        "dataset_2"])
    gpf_instance.reload()
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


@pytest.fixture
def custom_query_transformer(
    custom_wgpf: WGPFInstance,
) -> QueryTransformer:
    return QueryTransformer(
        custom_wgpf.gene_scores_db,
        custom_wgpf.reference_genome.chromosomes,
        custom_wgpf.reference_genome.chrom_prefix,
    )


@pytest.fixture
def custom_response_transformer(
    custom_wgpf: WGPFInstance,
) -> ResponseTransformer:
    return ResponseTransformer(
        custom_wgpf.gene_scores_db,
    )
