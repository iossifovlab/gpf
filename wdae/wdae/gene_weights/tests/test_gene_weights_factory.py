import pytest

from gpf_instance.gpf_instance import get_gpf_instance

pytestmark = pytest.mark.usefixtures('mock_gpf_instance')


def test_get_gene_weights_factory(db):
    weights_factory = get_gpf_instance().weights_factory

    assert weights_factory is not None

    assert len(weights_factory) == 5
