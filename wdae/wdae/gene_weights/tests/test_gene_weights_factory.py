import pytest

from datasets_api.studies_manager import get_studies_manager

pytestmark = pytest.mark.usefixtures("mock_studies_manager")


def test_get_gene_weights_factory(db):
    weights_factory = get_studies_manager().get_weights_factory()

    assert weights_factory is not None

    assert len(weights_factory) == 5
