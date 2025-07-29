# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np
from dae.annotation.annotate_utils import build_output_path, stringify


def test_build_output_path_explicit() -> None:
    assert build_output_path(
        "some/directory/input_file.csv",
        "some/directory/explicit_output_file.csv",
    ) == "some/directory/explicit_output_file.csv"


def test_build_output_path_explicit_remove_gz() -> None:
    assert build_output_path(
        "some/directory/input_file.csv",
        "some/directory/explicit_output_file.csv.gz",
    ) == "some/directory/explicit_output_file.csv"


def test_build_output_path_none_given_explicitly() -> None:
    assert build_output_path(
        "some/directory/input_file.csv",
        None,
    ) == "some/directory/input_file_annotated.csv"


def test_build_output_path_none_given_explicitly_remove_gz() -> None:
    assert build_output_path(
        "some/directory/input_file.csv.gz",
        None,
    ) == "some/directory/input_file_annotated.csv"


def test_build_output_path_none_given_explicitly_no_extension() -> None:
    assert build_output_path(
        "some/directory/input_file",
        None,
    ) == "some/directory/input_file_annotated"


def test_build_output_path_none_given_explicitly_multiple_extensions() -> None:
    assert build_output_path(
        "some/directory/input_file.txt.csv",
        None,
    ) == "some/directory/input_file_annotated.txt.csv"


def test_build_output_path_none_given_explicitly_hidden_file() -> None:
    assert build_output_path(
        "some/directory/.input_file.csv",
        None,
    ) == "some/directory/.input_file_annotated.csv"


def test_stringify_string_notvcf() -> None:
    assert stringify("blabla", vcf=False) == "blabla"
    assert stringify("", vcf=False) == ""


def test_stringify_string_vcf() -> None:
    assert stringify("blabla", vcf=True) == "blabla"
    assert stringify("", vcf=True) == "."


def test_stringify_none_notvcf() -> None:
    assert stringify(None, vcf=False) == ""


def test_stringify_none_vcf() -> None:
    assert stringify(None, vcf=True) == "."


def test_stringify_bool_notvcf() -> None:
    assert stringify(True, vcf=False) == "yes"  # noqa: FBT003
    assert stringify(False, vcf=False) == ""  # noqa: FBT003


def test_stringify_bool_vcf() -> None:
    assert stringify(True, vcf=True) == "yes"  # noqa: FBT003
    assert stringify(False, vcf=True) == "."  # noqa: FBT003


def test_stringify_float() -> None:
    assert stringify(0.123456, vcf=False) == "0.123"
    assert stringify(0.123456, vcf=True) == "0.123"
    assert stringify(123456.123456, vcf=False) == "1.23e+05"
    assert stringify(123456.123456, vcf=True) == "1.23e+05"


def test_stringify_np_floating() -> None:
    assert stringify(np.float64(0.123456), vcf=False) == "0.123"
    assert stringify(np.float64(0.123456), vcf=True) == "0.123"
    assert stringify(np.float64(123456.123456), vcf=False) == "1.23e+05"
    assert stringify(np.float64(123456.123456), vcf=True) == "1.23e+05"
