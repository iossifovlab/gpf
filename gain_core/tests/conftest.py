# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
import pytest_mock
from gain.genomic_resources.genomic_context import (
    get_genomic_context,
)
from gain.genomic_resources.genomic_context_base import GenomicContext


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--enable-http-testing", "--http",
        dest="enable_http",
        action="store_true",
        default=False,
        help="enable HTTP unit testing")

    parser.addoption(
        "--enable-s3-testing", "--s3",
        dest="enable_s3",
        action="store_true",
        default=False,
        help="enable S3 unit testing")

    parser.addoption(
        "--enable-process-pool", "--pp",
        dest="enable_pp",
        action="store_true",
        default=False,
        help="enable process pool unit testing")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "grr_scheme" in metafunc.fixturenames:
        _generate_grr_schemes_fixtures(metafunc)


def _generate_grr_schemes_fixtures(metafunc: pytest.Metafunc) -> None:
    schemes = {"inmemory", "file"}
    if metafunc.config.getoption("enable_s3"):
        schemes.add("s3")
    if metafunc.config.getoption("enable_http"):
        schemes.add("http")

    if hasattr(metafunc, "function"):
        marked_schemes = set()
        for mark in getattr(metafunc.function, "pytestmark", []):
            if mark.name.startswith("grr_"):
                marked_schemes.add(mark.name[4:])
        if "rw" in marked_schemes:
            marked_schemes.add("file")
            marked_schemes.add("s3")
            marked_schemes.add("inmemory")
        if "full" in marked_schemes:
            marked_schemes.add("file")
            marked_schemes.add("s3")
        if "tabix" in marked_schemes:
            marked_schemes.add("file")
            marked_schemes.add("s3")
            marked_schemes.add("http")

        marked_schemes = marked_schemes & {
            "file", "inmemory", "http", "s3"}
        if marked_schemes:
            schemes = schemes & marked_schemes
    metafunc.parametrize(
        "grr_scheme",
        schemes,
        scope="module")


@pytest.fixture(autouse=True)
def clean_genomic_context(
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch(
        "gain.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
        [])


@pytest.fixture
def clean_genomic_context_providers(
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocker.patch(
        "gain.genomic_resources.genomic_context._REGISTERED_CONTEXT_PROVIDERS",
        [])


@pytest.fixture
def context_fixture(
    mocker: pytest_mock.MockerFixture,
) -> GenomicContext:
    mocker.patch(
        "gain.genomic_resources.genomic_context._REGISTERED_CONTEXT_PROVIDERS",
        [])
    mocker.patch(
        "gain.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
        [])
    context = get_genomic_context()
    assert context is not None
    return context
