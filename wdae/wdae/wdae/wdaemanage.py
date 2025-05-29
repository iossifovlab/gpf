import logging
import os
import sys

from django.core.management import execute_from_command_line

logger = logging.getLogger("wdaemanage")


def main() -> None:
    """Entry point for wdaemanage when invoked as a cli tool."""

    argv = sys.argv
    if not argv[0].endswith("wdaemanage"):
        logger.warning(
            "%s tool is deprecated! Use 'wdaemanage' instead.",
            os.path.basename(argv[0]),
        )

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wdae.settings")
    execute_from_command_line(sys.argv)
