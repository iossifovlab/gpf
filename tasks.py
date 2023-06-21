import sys
import re
import logging
from datetime import datetime

from bumpversion.cli import main as bumpversion
from git import Repo
from invoke import task

logger = logging.getLogger("invoke tasks")


@task
def release(context):  # pylint: disable=unused-argument
    """Make a new release version tag of GPF."""
    repo = Repo(".")
    if repo.head.is_detached:
        logger.error("In detached HEAD state, refusing to release")
        sys.exit(1)
    # elif repo.active_branch.name != "master":
    #     logger.error("Not on the master branch, refusing to release")
    #     sys.exit(1)
    # Get the current date info
    date_info = datetime.now().strftime("%Y.%m")

    # Our CalVer pattern which works until year 2200, up to 100 releases a
    # month (purposefully excludes builds)
    pattern = re.compile(r"v2[0-1][0-9]{2}.(0[0-9]|1[0-2]).[0-9]{2}")

    # Identify and set the increment
    for tag in reversed(repo.tags):
        if pattern.fullmatch(tag.name):
            latest_release = tag.name
            break
    else:
        latest_release = None

    if latest_release and date_info == latest_release[:7]:
        increment = str(int(latest_release[8:]) + 1).zfill(2)
    else:
        increment = "01"

    new_version = date_info + "." + increment
    logger.error("new version %s", new_version)
    bumpversion(["--new-version", new_version, "unusedpart"])
