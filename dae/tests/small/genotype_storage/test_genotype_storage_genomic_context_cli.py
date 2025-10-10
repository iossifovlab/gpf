# pylint: disable=W0621,C0114,C0116,W0212,W0613
import argparse
import pathlib
import textwrap

import pytest
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
    register_context,
    register_context_provider,
)
from dae.genomic_resources.genomic_context_base import (
    SimpleGenomicContext,
)
from dae.genotype_storage.genotype_storage_genomic_context_cli import (
    GC_GENOTYPE_STORAGES_KEY,
    CLIGenotypeStorageContextProvider,
    get_context_genotype_storages,
)
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)

pytestmark = pytest.mark.usefixtures("clean_genomic_context_providers")


@pytest.fixture
def storage_config(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a sample genotype storage configuration file."""
    config_file = tmp_path / "genotype_storage.yaml"
    config_file.write_text(textwrap.dedent(f"""
        id: test_storage
        storage_type: inmemory
        dir: {tmp_path / "data"}
    """))
    return config_file


def test_cli_genotype_storage_context_provider_init_without_config() -> None:
    """Test provider returns None when no config is provided."""
    # Given
    provider = CLIGenotypeStorageContextProvider()

    # When
    context = provider.init()

    # Then
    assert context is None


def test_cli_genotype_storage_context_provider_init_with_config(
    storage_config: pathlib.Path,
) -> None:
    """Test provider creates context when config file is provided."""
    # Given
    provider = CLIGenotypeStorageContextProvider()

    # When
    context = provider.init(**{GC_GENOTYPE_STORAGES_KEY: str(storage_config)})

    # Then
    assert context is not None
    assert context.get_source() == "CLIGenotypeStorageContextProvider"
    assert GC_GENOTYPE_STORAGES_KEY in context.get_context_keys()

    registry = context.get_context_object(GC_GENOTYPE_STORAGES_KEY)
    assert isinstance(registry, GenotypeStorageRegistry)


def test_cli_genotype_storage_context_provider_full_workflow(
    storage_config: pathlib.Path,
) -> None:
    """Test full workflow with argument parsing."""
    # Given
    parser = argparse.ArgumentParser()
    provider = CLIGenotypeStorageContextProvider()
    provider.add_argparser_arguments(parser)

    argv = ["--genotype-storage-config", str(storage_config)]

    # When
    args = parser.parse_args(argv)
    context = provider.init(**vars(args))

    # Then
    assert context is not None
    registry = context.get_context_object(GC_GENOTYPE_STORAGES_KEY)
    assert isinstance(registry, GenotypeStorageRegistry)


def test_cli_genotype_storage_context_provider_short_flag(
    storage_config: pathlib.Path,
) -> None:
    """Test that short --gsf flag works."""
    # Given
    parser = argparse.ArgumentParser()
    provider = CLIGenotypeStorageContextProvider()
    provider.add_argparser_arguments(parser)

    argv = ["--gsf", str(storage_config)]

    # When
    args = parser.parse_args(argv)
    context = provider.init(**vars(args))

    # Then
    assert context is not None
    assert GC_GENOTYPE_STORAGES_KEY in context.get_context_keys()


def test_cli_genotype_storage_with_context_providers(
    storage_config: pathlib.Path,
) -> None:
    """Test integration with full genomic context system."""
    # Given
    register_context_provider(CLIGenotypeStorageContextProvider())

    parser = argparse.ArgumentParser()
    context_providers_add_argparser_arguments(parser)

    argv = ["--genotype-storage-config", str(storage_config)]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None
    assert GC_GENOTYPE_STORAGES_KEY in context.get_context_keys()

    registry = get_context_genotype_storages(context)
    assert registry is not None
    assert isinstance(registry, GenotypeStorageRegistry)


def test_get_context_genotype_storages_returns_none() -> None:
    """Test helper returns None when registry is absent."""
    # Given
    context = SimpleGenomicContext({}, source="empty_context")

    # When
    registry = get_context_genotype_storages(context)

    # Then
    assert registry is None


def test_get_context_genotype_storages_validates_type() -> None:
    """Test helper raises TypeError for wrong object type."""
    # Given
    context = SimpleGenomicContext(
        {GC_GENOTYPE_STORAGES_KEY: "not_a_registry"},
        source="bad_context",
    )

    # When / Then
    with pytest.raises(
        TypeError,
        match="The genotype storage registry from the genomic context "
        "is not an GenotypeStorageRegistry",
    ):
        get_context_genotype_storages(context)


def test_get_context_genotype_storages_success() -> None:
    """Test helper successfully retrieves valid registry."""
    # Given
    registry = GenotypeStorageRegistry()
    context = SimpleGenomicContext(
        {GC_GENOTYPE_STORAGES_KEY: registry},
        source="test_context",
    )

    # When
    retrieved_registry = get_context_genotype_storages(context)

    # Then
    assert retrieved_registry is not None
    assert retrieved_registry is registry
    assert isinstance(retrieved_registry, GenotypeStorageRegistry)


def test_cli_genotype_storage_context_provider_no_config_full_context(
) -> None:
    """Test provider abstains when no config in full context."""
    # Given
    register_context_provider(CLIGenotypeStorageContextProvider())

    parser = argparse.ArgumentParser()
    context_providers_add_argparser_arguments(parser)

    argv: list[str] = []  # No genotype storage config

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None
    # Provider should have abstained, so key should not be present
    # unless another provider added it
    registry = get_context_genotype_storages(context)
    assert registry is None


def test_multiple_storages_in_config(tmp_path: pathlib.Path) -> None:
    """Test configuration with multiple storage definitions."""
    # Given
    config_file = tmp_path / "multi_storage.yaml"
    config_file.write_text(textwrap.dedent(f"""
        storages:
        - id: storage1
          storage_type: inmemory
          dir: {tmp_path / "data1"}
        - id: storage2
          storage_type: inmemory
          dir: {tmp_path / "data2"}
    """))

    provider = CLIGenotypeStorageContextProvider()

    # When
    context = provider.init(**{GC_GENOTYPE_STORAGES_KEY: str(config_file)})

    # Then
    assert context is not None
    registry = get_context_genotype_storages(context)
    assert registry is not None


def test_provider_registered_context() -> None:
    """Test that provider can work with register_context."""
    # Given
    registry = GenotypeStorageRegistry()
    context = SimpleGenomicContext(
        {GC_GENOTYPE_STORAGES_KEY: registry},
        source="manual_context",
    )

    # When
    register_context(context)
    genomic_context = get_genomic_context()

    # Then
    retrieved_registry = get_context_genotype_storages(genomic_context)
    assert retrieved_registry is registry


def test_cli_genotype_storage_context_provider_bad_config(
    tmp_path: pathlib.Path,
) -> None:
    """Test provider raises ValueError for invalid configuration format."""
    # Given
    bad_config_file = tmp_path / "bad_storage.yaml"
    bad_config_file.write_text(textwrap.dedent("""
        # Missing required fields - not a valid storage config
        some_field: value
        another_field: 123
    """))

    provider = CLIGenotypeStorageContextProvider()

    # When / Then
    with pytest.raises(
        ValueError,
        match="Unexpected format of genotype storage configuration",
    ):
        provider.init(**{GC_GENOTYPE_STORAGES_KEY: str(bad_config_file)})
