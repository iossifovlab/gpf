# pylint: disable=C0114,C0116
from collections import UserDict, UserList

import pytest

from gpf.configuration.study_config_builder import TOMLDict, TOMLList

BOOL_STRINGS = [(True, "true"), (False, "false")]
OTHER_VALUES = ["text", 3, 2.5, None, (1, 2)]
USER_CONTAINERS = [
    TOMLDict({"b": True}),
    TOMLList([True]),
    UserDict({"b": True}),
    UserList([True]),
]


def test_from_dict_of_empty_dict_is_empty_toml_dict() -> None:
    result = TOMLDict.from_dict({})

    assert isinstance(result, TOMLDict)
    assert len(result) == 0


def test_from_dict_converts_nested_dict_to_toml_dict() -> None:
    result = TOMLDict.from_dict({"a": {"b": True, "c": [False]}})

    inner = result["a"]
    assert isinstance(inner, TOMLDict)
    assert inner["b"] == "true"
    assert isinstance(inner["c"], TOMLList)
    assert inner["c"][0] == "false"


def test_from_dict_converts_nested_list_to_toml_list() -> None:
    result = TOMLDict.from_dict({"a": [False, [True]]})

    inner = result["a"]
    assert isinstance(inner, TOMLList)
    assert inner[0] == "false"
    assert isinstance(inner[1], TOMLList)
    assert inner[1][0] == "true"


@pytest.mark.parametrize(("value", "expected"), BOOL_STRINGS)
def test_from_dict_converts_bool_value_to_string(
    value: bool, expected: str,
) -> None:
    result = TOMLDict.from_dict({"a": value})

    assert isinstance(result["a"], str)
    assert result["a"] == expected


@pytest.mark.parametrize("value", OTHER_VALUES)
def test_from_dict_keeps_other_values(value: object) -> None:
    result = TOMLDict.from_dict({"a": value})

    assert result["a"] is value


def test_from_dict_converts_dict_inside_list_value() -> None:
    result = TOMLDict.from_dict({"a": [{"b": True}]})

    inner = result["a"][0]
    assert isinstance(inner, TOMLDict)
    assert inner["b"] == "true"


@pytest.mark.parametrize("value", USER_CONTAINERS)
def test_from_dict_keeps_user_dict_and_user_list_values(
    value: object,
) -> None:
    result = TOMLDict.from_dict({"a": value})

    assert result["a"] is value


def test_from_dict_does_not_change_input() -> None:
    nested_dict = {"b": True}
    nested_list = [False]
    input_dict = {"d": nested_dict, "l": nested_list, "f": True}

    result = TOMLDict.from_dict(input_dict)

    assert input_dict["d"] is nested_dict
    assert input_dict["l"] is nested_list
    assert input_dict["f"] is True
    assert nested_dict == {"b": True}
    assert nested_list == [False]
    assert result.data is not input_dict


def test_str_of_from_dict_quotes_converted_bool() -> None:
    assert str(TOMLDict.from_dict({"a": True})) == '{ a = "true" }'
    assert str(TOMLDict({"a": True})) == "{ a = true }"


def test_from_list_of_empty_list_is_empty_toml_list() -> None:
    result = TOMLList.from_list([])

    assert isinstance(result, TOMLList)
    assert len(result) == 0


def test_from_list_converts_nested_dict_to_toml_dict() -> None:
    result = TOMLList.from_list([{"b": False, "c": {"d": True}}])

    inner = result[0]
    assert isinstance(inner, TOMLDict)
    assert inner["b"] == "false"
    assert isinstance(inner["c"], TOMLDict)
    assert inner["c"]["d"] == "true"


def test_from_list_converts_nested_list_to_toml_list() -> None:
    result = TOMLList.from_list([[True, {"x": False}]])

    inner = result[0]
    assert isinstance(inner, TOMLList)
    assert inner[0] == "true"
    assert isinstance(inner[1], TOMLDict)
    assert inner[1]["x"] == "false"


@pytest.mark.parametrize(("value", "expected"), BOOL_STRINGS)
def test_from_list_converts_bool_element_to_string(
    value: bool, expected: str,
) -> None:
    result = TOMLList.from_list([value])

    assert isinstance(result[0], str)
    assert result[0] == expected


@pytest.mark.parametrize("value", OTHER_VALUES)
def test_from_list_keeps_other_elements(value: object) -> None:
    result = TOMLList.from_list([value])

    assert result[0] is value


def test_from_list_converts_list_inside_dict_element() -> None:
    result = TOMLList.from_list([{"b": [False]}])

    inner = result[0]["b"]
    assert isinstance(inner, TOMLList)
    assert inner[0] == "false"


@pytest.mark.parametrize("value", USER_CONTAINERS)
def test_from_list_keeps_user_dict_and_user_list_elements(
    value: object,
) -> None:
    result = TOMLList.from_list([value])

    assert result[0] is value


def test_from_list_does_not_change_input() -> None:
    nested_dict = {"b": True}
    nested_list = [False]
    input_list = [nested_dict, nested_list, True]

    result = TOMLList.from_list(input_list)

    assert input_list[0] is nested_dict
    assert input_list[1] is nested_list
    assert input_list[2] is True
    assert nested_dict == {"b": True}
    assert nested_list == [False]
    assert result.data is not input_list


def test_str_of_from_list_quotes_converted_bool() -> None:
    assert str(TOMLList.from_list([True])) == '["true"]'
    assert str(TOMLList([True])) == "[true]"
