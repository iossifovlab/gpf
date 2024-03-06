"""Provides common configuration for loggers verbosity."""
import argparse
import logging


class VerbosityConfiguration:
    """Defines common configuration of verbosity for loggers."""

    @staticmethod
    def set_arguments(parser: argparse.ArgumentParser) -> None:
        """Add verbosity arguments to argument parser."""
        parser.add_argument("--verbose", "-v", "-V", action="count", default=0)

    @staticmethod
    def set(args: argparse.Namespace) -> None:
        """Read verbosity settings from parsed arguments and sets logger."""
        VerbosityConfiguration.set_verbosity(args.verbose)

    @staticmethod
    def set_verbosity(verbose: int) -> None:
        """Set logging level according to the verbosity specified."""
        if verbose == 1:
            loglevel = logging.INFO
            logging.basicConfig(level=logging.INFO)
        elif verbose >= 2:
            loglevel = logging.DEBUG
            logging.basicConfig(level=logging.DEBUG)
        else:
            loglevel = logging.WARNING
            logging.basicConfig(level=logging.WARNING)

        logging.getLogger("dae.effect_annotation").setLevel(
            max(loglevel, logging.INFO))

        logging.getLogger("impala").setLevel(logging.WARNING)
        logging.getLogger("distributed").setLevel(logging.WARNING)
        logging.getLogger("bokeh").setLevel(logging.ERROR)
        logging.getLogger("fsspec").setLevel(max(loglevel, logging.INFO))
        logging.getLogger("matplotlib").setLevel(max(loglevel, logging.INFO))
        logging.getLogger("botocore").setLevel(max(loglevel, logging.INFO))
        logging.getLogger("s3fs").setLevel(max(loglevel, logging.INFO))
