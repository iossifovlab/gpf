"""Provides common configuration for loggers verbosity."""
import argparse
import logging


class VerbosityConfiguration:
    """Defines common configuration of verbosity for loggers."""

    @staticmethod
    def set_arguments(parser: argparse.ArgumentParser) -> None:
        """Add verbosity arguments to argument parser."""
        parser.add_argument("--verbose", "-v", "-V", action="count", default=0)
        parser.add_argument(
            "--logfile", type=str, default=None,
            help="File to log output to. If not set, logs to console.",
        )

    @staticmethod
    def set(args: argparse.Namespace | dict[str, str]) -> None:
        """Read verbosity settings from parsed arguments and sets logger."""
        if isinstance(args, argparse.Namespace):
            args = vars(args)
        verbosity = int(args.get("verbose", 0))
        loglevel = VerbosityConfiguration.verbosity(verbosity)
        logging.basicConfig(
            filename=args["logfile"],
            encoding="utf-8",
            level=loglevel,
        )
        VerbosityConfiguration.adjust_verbosity(loglevel)

    @staticmethod
    def verbosity(verbosity: int) -> int:
        """Get verbosity level from loglevel."""
        if verbosity == 1:
            loglevel = logging.INFO
        elif verbosity >= 2:
            loglevel = logging.DEBUG
        else:
            loglevel = logging.WARNING
        return loglevel

    @staticmethod
    def adjust_verbosity(loglevel: int) -> None:
        """Set logging level according to the verbosity specified."""
        logging.getLogger("dae.effect_annotation").setLevel(
            max(loglevel, logging.INFO))

        logging.getLogger("impala").setLevel(logging.WARNING)
        logging.getLogger("distributed").setLevel(logging.WARNING)
        logging.getLogger("bokeh").setLevel(logging.ERROR)
        logging.getLogger("fsspec").setLevel(max(loglevel, logging.INFO))
        logging.getLogger("matplotlib").setLevel(max(loglevel, logging.INFO))
        logging.getLogger("botocore").setLevel(max(loglevel, logging.INFO))
        logging.getLogger("s3fs").setLevel(max(loglevel, logging.INFO))
