# pylint: disable=C0114,C0116
import argparse
import logging

import pytest

from gpf.variants_loaders.dae.loader import DenovoLoader

LOCATION_ERROR = (
    "--denovo-location and (--denovo-chrom, --denovo-pos) "
    "are mutually exclusive"
)
VARIANT_ERROR = (
    "--denovo-variant and (denovo-ref, denovo-alt) are mutually exclusive"
)
PERSON_ERROR = (
    "--denovo-person-id and (denovo-family-id, denovo-best-state) "
    "are mutually exclusive"
)


def _parse(*args: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    DenovoLoader.cli_arguments(parser)
    return parser.parse_args(["denovo.tsv", *args])


def test_no_options_fill_in_all_default_column_names() -> None:
    argv = _parse()

    filename, params = DenovoLoader.parse_cli_arguments(argv)

    denovo_file: object = filename
    assert denovo_file == "denovo.tsv"
    assert params == {
        "denovo_location": None,
        "denovo_variant": None,
        "denovo_chrom": "chrom",
        "denovo_pos": "pos",
        "denovo_ref": "ref",
        "denovo_alt": "alt",
        "denovo_person_id": "person_id",
        "denovo_family_id": None,
        "denovo_best_state": None,
        "denovo_genotype": None,
        "add_chrom_prefix": None,
        "del_chrom_prefix": None,
        "denovo_sep": "\t",
    }


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (
            ["--denovo-location", "loc", "--denovo-chrom", "c"],
            LOCATION_ERROR,
        ),
        (
            ["--denovo-location", "loc", "--denovo-pos", "p"],
            LOCATION_ERROR,
        ),
        (
            ["--denovo-variant", "var", "--denovo-ref", "r"],
            VARIANT_ERROR,
        ),
        (
            ["--denovo-variant", "var", "--denovo-alt", "a"],
            VARIANT_ERROR,
        ),
        (
            ["--denovo-person-id", "pid", "--denovo-family-id", "fid"],
            PERSON_ERROR,
        ),
        (
            ["--denovo-person-id", "pid", "--denovo-best-state", "bs"],
            PERSON_ERROR,
        ),
    ],
)
def test_exclusive_options_log_an_error_and_raise_a_bare_value_error(
    args: list[str], message: str, caplog: pytest.LogCaptureFixture,
) -> None:
    argv = _parse(*args)

    with caplog.at_level(logging.ERROR), \
            pytest.raises(ValueError, match=r"^$") as excinfo:
        DenovoLoader.parse_cli_arguments(argv)

    assert excinfo.value.args == ()
    assert [r.getMessage() for r in caplog.records
            if r.levelno == logging.ERROR] == [message]


def test_location_keeps_chrom_and_pos_none() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-location", "loc"))

    assert params["denovo_location"] == "loc"
    assert params["denovo_chrom"] is None
    assert params["denovo_pos"] is None


def test_chrom_and_pos_together_are_kept() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-chrom", "c", "--denovo-pos", "p"))

    assert (params["denovo_chrom"], params["denovo_pos"]) == ("c", "p")


@pytest.mark.parametrize(
    "args", [["--denovo-chrom", "c"], ["--denovo-pos", "p"]])
def test_lone_chrom_or_pos_is_overwritten_with_the_defaults(
    args: list[str],
) -> None:
    _, params = DenovoLoader.parse_cli_arguments(_parse(*args))

    assert (params["denovo_chrom"], params["denovo_pos"]) == ("chrom", "pos")


def test_variant_keeps_ref_and_alt_none() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-variant", "var"))

    assert params["denovo_variant"] == "var"
    assert params["denovo_ref"] is None
    assert params["denovo_alt"] is None


def test_ref_and_alt_together_are_kept() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-ref", "r", "--denovo-alt", "a"))

    assert (params["denovo_ref"], params["denovo_alt"]) == ("r", "a")


@pytest.mark.parametrize(
    "args", [["--denovo-ref", "r"], ["--denovo-alt", "a"]])
def test_lone_ref_or_alt_is_overwritten_with_the_defaults(
    args: list[str],
) -> None:
    _, params = DenovoLoader.parse_cli_arguments(_parse(*args))

    assert (params["denovo_ref"], params["denovo_alt"]) == ("ref", "alt")


def test_person_id_is_kept() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-person-id", "pid"))

    assert params["denovo_person_id"] == "pid"


def test_person_id_with_genotype_is_accepted() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-person-id", "pid", "--denovo-genotype", "gt"))

    assert params["denovo_person_id"] == "pid"
    assert params["denovo_genotype"] == "gt"


@pytest.mark.parametrize(
    ("args", "key", "value"),
    [
        (["--denovo-best-state", "bs"], "denovo_best_state", "bs"),
        (["--denovo-genotype", "gt"], "denovo_genotype", "gt"),
    ],
)
def test_family_id_with_best_state_or_genotype_sets_no_person_id(
    args: list[str], key: str, value: str,
) -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-family-id", "fid", *args))

    assert params["denovo_person_id"] is None
    assert params["denovo_family_id"] == "fid"
    assert params[key] == value


@pytest.mark.parametrize(
    ("args", "key", "value"),
    [
        (["--denovo-family-id", "fid"], "denovo_family_id", "fid"),
        (["--denovo-best-state", "bs"], "denovo_best_state", "bs"),
        (["--denovo-genotype", "gt"], "denovo_genotype", "gt"),
    ],
)
def test_lone_family_option_adds_the_default_person_id(
    args: list[str], key: str, value: str,
) -> None:
    _, params = DenovoLoader.parse_cli_arguments(_parse(*args))

    assert params["denovo_person_id"] == "person_id"
    assert params[key] == value


def test_best_state_with_genotype_raises_an_assertion_error() -> None:
    argv = _parse(
        "--denovo-family-id", "fid",
        "--denovo-best-state", "bs", "--denovo-genotype", "gt")

    with pytest.raises(AssertionError):
        DenovoLoader.parse_cli_arguments(argv)


def test_empty_string_counts_as_absent() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-location", "", "--denovo-chrom", "c"))

    assert (params["denovo_chrom"], params["denovo_pos"]) == ("chrom", "pos")


def test_custom_separator_is_kept() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--denovo-sep", ","))

    assert params["denovo_sep"] == ","


def test_none_separator_becomes_a_tab() -> None:
    argv = _parse()
    argv.denovo_sep = None

    _, params = DenovoLoader.parse_cli_arguments(argv)

    assert params["denovo_sep"] == "\t"


def test_chrom_prefix_options_go_into_the_result() -> None:
    _, params = DenovoLoader.parse_cli_arguments(
        _parse("--add-chrom-prefix", "chr", "--del-chrom-prefix", "x"))

    assert params["add_chrom_prefix"] == "chr"
    assert params["del_chrom_prefix"] == "x"


def test_result_has_no_chrom_mapping_key() -> None:
    _, params = DenovoLoader.parse_cli_arguments(_parse())

    assert "chrom_mapping" not in params


def test_first_element_of_the_result_is_the_denovo_file_string() -> None:
    filename, _ = DenovoLoader.parse_cli_arguments(_parse())

    # The annotation says list[str], but the value is the string.
    denovo_file: object = filename
    assert denovo_file == "denovo.tsv"


def test_defaults_are_written_back_into_argv() -> None:
    argv = _parse()

    DenovoLoader.parse_cli_arguments(argv)

    assert (argv.denovo_chrom, argv.denovo_pos) == ("chrom", "pos")
    assert (argv.denovo_ref, argv.denovo_alt) == ("ref", "alt")
    assert argv.denovo_person_id == "person_id"


def test_use_defaults_is_ignored() -> None:
    _, with_defaults = DenovoLoader.parse_cli_arguments(
        _parse(), use_defaults=True)
    _, without_defaults = DenovoLoader.parse_cli_arguments(_parse())

    assert with_defaults == without_defaults


def test_namespace_without_chrom_prefix_options_raises_attribute_error(
) -> None:
    argv = argparse.Namespace(
        denovo_file="denovo.tsv",
        denovo_location=None, denovo_variant=None,
        denovo_chrom=None, denovo_pos=None,
        denovo_ref=None, denovo_alt=None,
        denovo_person_id=None, denovo_family_id=None,
        denovo_best_state=None, denovo_genotype=None,
        denovo_sep="\t",
    )

    with pytest.raises(AttributeError, match="add_chrom_prefix"):
        DenovoLoader.parse_cli_arguments(argv)
