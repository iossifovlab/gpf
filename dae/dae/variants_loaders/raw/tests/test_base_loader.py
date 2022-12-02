from dae.variants_loaders.raw.loader import CLILoader, CLIArgument


class TestLoader(CLILoader):  # pylint: disable=missing-class-docstring
    @classmethod
    def _arguments(cls):
        arguments = []
        arguments.append(CLIArgument(
            "positional",
            value_type=str,
            metavar="<positional>",
            help_text="Some positional argument",
        ))
        arguments.append(CLIArgument(
            "--kwarg1",
            default_value=1,
            help_text="First kwarg",
        ))
        arguments.append(CLIArgument(
            "--kwarg2",
            default_value=2,
            help_text="Second kwarg",
        ))
        return arguments


def test_cli_defaults_does_not_include_positionals():
    """
    Test for a bug where positionals were included in cli_defaults.

    Positional arguments have no destination and were mapped to None
    in the output.
    """
    loader = TestLoader()
    defaults = loader.cli_defaults()
    assert set(defaults.keys()) == set(["kwarg1", "kwarg2"])
