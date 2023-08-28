# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0115
from dae.variants_loaders.raw.loader import CLILoader, CLIArgument


def test_cli_defaults_does_not_include_positionals() -> None:
    """
    Test for a bug where positionals were included in cli_defaults.

    Positional arguments have no destination and were mapped to None
    in the output.
    """
    class TestLoader(CLILoader):
        @classmethod
        def _arguments(cls) -> list[CLIArgument]:
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

    loader = TestLoader()
    defaults = loader.cli_defaults()
    assert set(defaults.keys()) == set(["kwarg1", "kwarg2"])
