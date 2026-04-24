# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np
from gain.annotation.annotate_utils import build_output_path, stringify


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
    ) == "input_file_annotated.csv"


def test_build_output_path_none_given_explicitly_remove_gz() -> None:
    assert build_output_path(
        "some/directory/input_file.csv.gz",
        None,
    ) == "input_file_annotated.csv"


def test_build_output_path_none_given_explicitly_no_extension() -> None:
    assert build_output_path(
        "some/directory/input_file",
        None,
    ) == "input_file_annotated"


def test_build_output_path_none_given_explicitly_multiple_extensions() -> None:
    assert build_output_path(
        "some/directory/input_file.txt.csv",
        None,
    ) == "input_file.txt_annotated.csv"


def test_build_output_path_none_given_explicitly_hidden_file() -> None:
    assert build_output_path(
        "some/directory/.input_file.csv",
        None,
    ) == ".input_file_annotated.csv"


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


def test_stringify_gene_rank_score_values() -> None:
    assert stringify(12345.5, vcf=False) == "12345.5"
    assert stringify(1234.5, vcf=False) == "1234.5"
    assert stringify(123.5, vcf=False) == "123.5"
    assert stringify(12345, vcf=False) == "12345"
    assert stringify(1234, vcf=False) == "1234"
    assert stringify(123, vcf=False) == "123"
    assert stringify(12345., vcf=False) == "12345"
    assert stringify(1234., vcf=False) == "1234"
    assert stringify(123., vcf=False) == "123"


def test_stringify_list_notvcf() -> None:
    assert stringify([1, 2, 3], vcf=False) == "1,2,3"
    assert stringify(["a", "b", "c"], vcf=False) == "a,b,c"
    assert stringify([1.5, 123.5, 123456.7], vcf=False) == "1.5,123.5,1.23e+05"
    assert stringify([None, "", True], vcf=False) == ",,yes"
    assert stringify([], vcf=False) == ""


def test_stringify_list_vcf() -> None:
    assert stringify([1, 2, 3], vcf=True) == "1,2,3"
    assert stringify(["a", "b", "c"], vcf=True) == "a,b,c"
    assert stringify([None, "", True], vcf=True) == ".,.,yes"
    assert stringify([], vcf=True) == ""


def test_stringify_tuple_notvcf() -> None:
    assert stringify((1, 2, 3), vcf=False) == "1,2,3"
    assert stringify(("a", "b"), vcf=False) == "a,b"
    assert stringify((None, True, "x"), vcf=False) == ",yes,x"
    assert stringify((), vcf=False) == ""


def test_stringify_tuple_vcf() -> None:
    assert stringify((1, 2, 3), vcf=True) == "1,2,3"
    assert stringify((None, True, "x"), vcf=True) == ".,yes,x"
    assert stringify((), vcf=True) == ""


def test_stringify_dict_notvcf() -> None:
    assert stringify({"a": 1, "b": 2}, vcf=False) == "a:1;b:2"
    assert stringify({"key": None}, vcf=False) == "key:"
    assert stringify({"x": True, "y": False}, vcf=False) == "x:yes;y:"
    assert stringify({}, vcf=False) == ""


def test_stringify_dict_vcf() -> None:
    assert stringify({"a": 1, "b": 2}, vcf=True) == "a:1;b:2"
    assert stringify({"key": None}, vcf=True) == "key:."
    assert stringify({"x": True, "y": False}, vcf=True) == "x:yes;y:."
    assert stringify({}, vcf=True) == ""


def test_stringify_nested_structures() -> None:
    assert stringify([[1, 2], [3, 4]], vcf=False) == "1,2,3,4"
    assert stringify([{"a": 1}, {"b": 2}], vcf=False) == "a:1,b:2"
    assert stringify({"a": [1, 2], "b": 3.5}, vcf=False) == "a:1,2;b:3.5"
    assert stringify({"outer": {"inner": 1}}, vcf=False) == "outer:inner:1"
