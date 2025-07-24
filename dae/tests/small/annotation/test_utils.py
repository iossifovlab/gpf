# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.annotation.annotate_utils import build_output_path


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
