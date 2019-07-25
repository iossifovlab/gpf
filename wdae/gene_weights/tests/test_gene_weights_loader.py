import pytest

from datasets_api.studies_manager import get_studies_manager

pytestmark = pytest.mark.usefixtures("mock_studies_manager")


def test_get_gene_weights_loader(db):
    weights_loader = get_studies_manager().get_weights_loader()

    assert weights_loader is not None

    assert len(weights_loader) == 5
