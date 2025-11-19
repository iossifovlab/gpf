# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pathlib

import pytest
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    build_inmemory_test_resource,
    setup_directories,
)
from dae.genomic_resources.utils import build_chrom_mapping


def test_build_chrom_mapping_no_config() -> None:
    """Test build_chrom_mapping returns None when no chrom_mapping config."""
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    result = build_chrom_mapping(res)
    assert result is None


def test_build_chrom_mapping_with_filename(tmp_path: pathlib.Path) -> None:
    """Test build_chrom_mapping with mapping file."""
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    filename: chrom_map.txt
        """,
        "chrom_map.txt": """chr1\t1
chr2\t2
chrX\tX
chrM\tMT
""",
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    res = build_filesystem_test_resource(tmp_path)
    # Note: build_chrom_mapping expects the table config, not the root config
    table_config = res.get_config()["table"]
    mapping_func = build_chrom_mapping(res, config=table_config)

    assert mapping_func is not None
    assert mapping_func("chr1") == "1"
    assert mapping_func("chr2") == "2"
    assert mapping_func("chrX") == "X"
    assert mapping_func("chrM") == "MT"
    assert mapping_func("chr3") is None
    assert mapping_func("Y") is None


def test_build_chrom_mapping_with_add_prefix() -> None:
    """Test build_chrom_mapping with add_prefix."""
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    add_prefix: chr
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    mapping_func = build_chrom_mapping(res, config=table_config)

    assert mapping_func is not None
    assert mapping_func("1") == "chr1"
    assert mapping_func("2") == "chr2"
    assert mapping_func("X") == "chrX"
    assert mapping_func("MT") == "chrMT"


def test_build_chrom_mapping_with_del_prefix() -> None:
    """Test build_chrom_mapping with del_prefix."""
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    del_prefix: chr
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    mapping_func = build_chrom_mapping(res, config=table_config)

    assert mapping_func is not None
    assert mapping_func("chr1") == "1"
    assert mapping_func("chr2") == "2"
    assert mapping_func("chrX") == "X"
    assert mapping_func("chrMT") == "MT"
    # Should return unchanged if prefix not present
    assert mapping_func("1") == "1"
    assert mapping_func("X") == "X"


def test_build_chrom_mapping_empty_config_raises_error() -> None:
    """Test build_chrom_mapping with empty chrom_mapping config.

    When chrom_mapping is present but empty (no filename, add_prefix, or
    del_prefix), it should raise a ValueError.
    """
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping: {}
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    with pytest.raises(ValueError, match="Invalid chrom_mapping configuration"):
        build_chrom_mapping(res, config=table_config)


def test_build_chrom_mapping_filename_with_extra_columns(
    tmp_path: pathlib.Path,
) -> None:
    """Test build_chrom_mapping with mapping file containing extra columns."""
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    filename: chrom_map.txt
        """,
        "chrom_map.txt": """chr1\t1\textra_column_ignored
chr2\t2\tanother_extra
chrX\tX\tyet_another
""",
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    res = build_filesystem_test_resource(tmp_path)
    table_config = res.get_config()["table"]
    mapping_func = build_chrom_mapping(res, config=table_config)

    assert mapping_func is not None
    # Only first two columns should be used
    assert mapping_func("chr1") == "1"
    assert mapping_func("chr2") == "2"
    assert mapping_func("chrX") == "X"


def test_build_chrom_mapping_del_prefix_multiple_occurrences() -> None:
    """Test del_prefix only removes from the start, not all occurrences."""
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    del_prefix: chr
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    mapping_func = build_chrom_mapping(res, config=table_config)

    assert mapping_func is not None
    # Only prefix should be removed
    assert mapping_func("chrchr1") == "chr1"
    assert mapping_func("chr_chr_1") == "_chr_1"


def test_build_chrom_mapping_add_prefix_empty_string() -> None:
    """Test add_prefix with empty string raises ValueError.

    Empty string is falsy, so it doesn't match the 'if add_prefix:' condition
    and will fall through to raise ValueError.
    """
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    add_prefix: ""
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    with pytest.raises(ValueError, match="Invalid chrom_mapping configuration"):
        build_chrom_mapping(res, config=table_config)


def test_build_chrom_mapping_del_prefix_empty_string() -> None:
    """Test del_prefix with empty string raises ValueError.

    Empty string is falsy, so it doesn't match the 'if del_prefix:' condition
    and will fall through to raise ValueError.
    """
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    del_prefix: ""
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    with pytest.raises(ValueError, match="Invalid chrom_mapping configuration"):
        build_chrom_mapping(res, config=table_config)


def test_build_chrom_mapping_filename_returns_none_for_missing() -> None:
    """Test that filename mapping returns None for unmapped chromosomes."""
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    filename: chrom_map.txt
        """,
        "chrom_map.txt": """1\tchr1
2\tchr2
""",
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    mapping_func = build_chrom_mapping(res, config=table_config)

    assert mapping_func is not None
    assert mapping_func("1") == "chr1"
    assert mapping_func("2") == "chr2"
    # Unmapped chromosomes should return None
    assert mapping_func("3") is None
    assert mapping_func("X") is None
    assert mapping_func("chr1") is None


@pytest.mark.parametrize("chrom,expected", [
    ("1", "chr1"),
    ("2", "chr2"),
    ("X", "chrX"),
    ("Y", "chrY"),
    ("MT", "chrMT"),
])
def test_build_chrom_mapping_add_prefix_parametrized(
    chrom: str,
    expected: str,
) -> None:
    """Test add_prefix mapping with various chromosome names."""
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    add_prefix: chr
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    mapping_func = build_chrom_mapping(res, config=table_config)
    assert mapping_func is not None
    assert mapping_func(chrom) == expected


@pytest.mark.parametrize("chrom,expected", [
    ("chr1", "1"),
    ("chr2", "2"),
    ("chrX", "X"),
    ("chrY", "Y"),
    ("chrMT", "MT"),
    ("1", "1"),  # No prefix to remove
    ("X", "X"),  # No prefix to remove
])
def test_build_chrom_mapping_del_prefix_parametrized(
    chrom: str,
    expected: str,
) -> None:
    """Test del_prefix mapping with various chromosome names."""
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": """
            type: position_score
            table:
                filename: data.mem
                chrom_mapping:
                    del_prefix: chr
        """,
        "data.mem": """
            chrom pos_begin c2
            1     10        0.1
        """,
    })

    table_config = res.get_config()["table"]
    mapping_func = build_chrom_mapping(res, config=table_config)
    assert mapping_func is not None
    assert mapping_func(chrom) == expected
