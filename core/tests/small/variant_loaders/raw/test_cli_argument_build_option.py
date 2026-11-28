# pylint: disable=C0114,C0116
from gpf.variants_loaders.raw.loader import CLIArgument


def test_positional_argument_builds_no_option() -> None:
    argument = CLIArgument("positional", value_type=str)

    result = argument.build_option({"positional": "value"})

    assert result is None


def test_missing_destination_builds_no_option() -> None:
    argument = CLIArgument("--name")

    result = argument.build_option({"other": "value"})

    assert result is None


def test_empty_params_build_no_option() -> None:
    argument = CLIArgument("--name")

    result = argument.build_option({})

    assert result is None


def test_value_builds_quoted_option() -> None:
    argument = CLIArgument("--some-name")

    result = argument.build_option({"some_name": "value"})

    assert result == '--some-name "value"'


def test_explicit_destination_is_the_params_key() -> None:
    argument = CLIArgument("--name", destination="dest")

    result = argument.build_option({"name": "x", "dest": "value"})

    assert result == '--name "value"'


def test_value_equal_to_default_builds_no_option() -> None:
    argument = CLIArgument("--name", default_value="default")

    result = argument.build_option({"name": "default"})

    assert result is None


def test_value_equal_to_default_with_use_defaults_builds_no_option() -> None:
    argument = CLIArgument("--name", default_value="default")

    result = argument.build_option({"name": "default"}, use_defaults=True)

    assert result is None


def test_value_other_than_default_builds_option() -> None:
    argument = CLIArgument("--name", default_value="default")

    result = argument.build_option({"name": "other"})

    assert result == '--name "other"'


def test_raw_value_escapes_control_characters() -> None:
    argument = CLIArgument("--sep", raw=True)

    result = argument.build_option({"sep": "\t"})

    assert result == '--sep "\\t"'


def test_raw_value_keeps_a_single_backslash() -> None:
    argument = CLIArgument("--sep", raw=True)

    result = argument.build_option({"sep": "\\t"})

    assert result == '--sep "\\t"'


def test_value_without_raw_is_not_escaped() -> None:
    argument = CLIArgument("--sep")

    result = argument.build_option({"sep": "\t"})

    assert result == '--sep "\t"'


def test_none_value_builds_no_option() -> None:
    argument = CLIArgument("--name", default_value="default")

    result = argument.build_option({"name": None})  # type: ignore[dict-item]

    assert result is None


def test_none_value_with_use_defaults_builds_default_option() -> None:
    argument = CLIArgument("--name", default_value=5)

    result = argument.build_option(
        {"name": None},  # type: ignore[dict-item]
        use_defaults=True,
    )

    assert result == '--name "5"'


def test_none_value_with_use_defaults_and_no_default_builds_no_option(
) -> None:
    argument = CLIArgument("--name")

    result = argument.build_option(
        {"name": None},  # type: ignore[dict-item]
        use_defaults=True,
    )

    assert result is None


def test_none_value_with_use_defaults_escapes_raw_default() -> None:
    argument = CLIArgument("--sep", default_value="\t", raw=True)

    result = argument.build_option(
        {"sep": None},  # type: ignore[dict-item]
        use_defaults=True,
    )

    assert result == '--sep "\\t"'


def test_none_value_with_use_defaults_keeps_default_without_raw() -> None:
    argument = CLIArgument("--sep", default_value="\t")

    result = argument.build_option(
        {"sep": None},  # type: ignore[dict-item]
        use_defaults=True,
    )

    assert result == '--sep "\t"'


def test_flag_builds_bare_option() -> None:
    argument = CLIArgument("--flag", has_value=False, action="store_true")

    result = argument.build_option({"flag": True})  # type: ignore[dict-item]

    assert result == "--flag"


def test_flag_with_false_value_still_builds_bare_option() -> None:
    argument = CLIArgument("--flag", has_value=False, action="store_true")

    result = argument.build_option({"flag": False})  # type: ignore[dict-item]

    assert result == "--flag"


def test_flag_with_none_value_still_builds_bare_option() -> None:
    argument = CLIArgument("--flag", has_value=False, action="store_true")

    result = argument.build_option({"flag": None})  # type: ignore[dict-item]

    assert result == "--flag"


def test_absent_flag_builds_no_option() -> None:
    argument = CLIArgument("--flag", has_value=False, action="store_true")

    result = argument.build_option({"other": True})  # type: ignore[dict-item]

    assert result is None
