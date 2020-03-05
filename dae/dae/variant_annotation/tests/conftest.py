import pytest

from .mocks import ExonMock
from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock


@pytest.fixture(scope="session")
def annotator():
    return AnnotatorMock(ReferenceGenomeMock())


@pytest.fixture(scope="session")
def exons():
    return [ExonMock(60, 70, 0), ExonMock(80, 90, 1), ExonMock(100, 110, 2)]


@pytest.fixture(scope="session")
def coding():
    return [ExonMock(65, 70, 0), ExonMock(80, 90, 1), ExonMock(100, 110, 2)]
