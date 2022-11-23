"""Provides common configuration for loggers verbosity."""
import argparse
import logging


class VerbosityConfiguration:
    """Defines common configuration of verbosity for loggers."""

    @staticmethod
    def set_argumnets(parser: argparse.ArgumentParser) -> None:
        """Add verbosity arguments to argument parser."""
        parser.add_argument("--verbose", "-v", "-V", action="count", default=0)

    @staticmethod
    def set(args) -> None:
        """Read verbosity settings from parsed arguments and sets logger."""
        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)
        logging.getLogger("impala").setLevel(logging.WARNING)
