# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Callable

import pytest
import pytest_mock

from dae.genomic_resources.genomic_context import GenomicContext
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.gpf_instance_plugin.gpf_instance_context_plugin import \
    init_test_gpf_instance_genomic_context_plugin
from dae.genomic_resources.genomic_context import get_genomic_context


@pytest.fixture
def gpf_instance_genomic_context_fixture(
    mocker: pytest_mock.MockerFixture
) -> Callable[[GPFInstance], GenomicContext]:

    def builder(gpf_instance: GPFInstance) -> GenomicContext:
        mocker.patch(
            "dae.genomic_resources.genomic_context."
            "_REGISTERED_CONTEXT_PROVIDERS",
            [])
        mocker.patch(
            "dae.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
            [])

        init_test_gpf_instance_genomic_context_plugin(gpf_instance)
        context = get_genomic_context()
        assert context is not None

        return context

    return builder
