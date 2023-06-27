import sys
import re
import logging
from datetime import datetime

from packaging.version import Version
from bumpversion.cli import main as bumpversion
from git import Repo
from invoke import task

logger = logging.getLogger("invoke tasks")


# Our CalVer pattern which works until year 2200, up to 100 releases a
# month (purposefully excludes builds)
VERSION_REGEX = re.compile(
    r"v?(?P<year>2[0-1]\d{2})\.(?P<month>\d\d?)\.(?P<minor>\d+)"
    r"((?P<modifier>(dev|rc))(?P<micro>\d+))?")


def git_repo():
    return Repo(".")


def now():
    year_month = datetime.now()
    return year_month.year, year_month.month


@task
def release_version(context):  # pylint: disable=unused-argument
    """Make a release version tag of GPF."""
    repo = git_repo()
    if repo.head.is_detached:
        logger.error("In detached HEAD state, refusing to release")
        sys.exit(1)
    elif repo.active_branch.name != "master":
        logger.error("Not on the master branch, refusing to release")
        sys.exit(1)

    # Get the current date info
    date_info = now()

    # Identify and set the increment
    for tag in reversed(repo.tags):
        if VERSION_REGEX.fullmatch(tag.name):
            latest_version = Version(tag.name)
            break
    else:
        latest_version = None

    if latest_version and date_info[0] == latest_version.major \
            and date_info[1] == latest_version.minor:
        if latest_version.dev is not None or latest_version.pre is not None:
            micro = latest_version.micro
        else:
            micro = latest_version.micro + 1
    else:
        micro = 0

    new_version = Version(f"{date_info[0]}.{date_info[1]}.{micro}")
    logger.error("new version %s", new_version)
    bumpversion(["--new-version", str(new_version), "unusedpart"])


@task
def dev_version(context):  # pylint: disable=unused-argument
    """Make a dev version tag of GPF."""
    repo = git_repo()
    if repo.head.is_detached:
        logger.error("In detached HEAD state, refusing to release")
        sys.exit(1)
    elif repo.active_branch.name not in {"master", "production"}:
        logger.error("Not on the master branch, refusing to release")
        sys.exit(1)

    # Get the current date info
    date_info = now()

    # Identify and set the increment
    for tag in reversed(repo.tags):
        if VERSION_REGEX.fullmatch(tag.name):
            latest_version = Version(tag.name)
            break
    else:
        latest_version = None

    if latest_version:
        if latest_version.dev is not None:
            new_version = Version(
                f"{latest_version.major}.{latest_version.minor}."
                f"{latest_version.micro}.dev{latest_version.dev + 1}")
        elif latest_version.major == date_info[0] \
                and latest_version.minor == date_info[1]:
            new_version = Version(
                f"{latest_version.major}.{latest_version.minor}."
                f"{latest_version.micro + 1}.dev0")
    else:
        new_version = Version(
            f"{date_info[0]}.{date_info[1]}.0.dev0")

    logger.error("new version %s", new_version)
    bumpversion(["--new-version", str(new_version), "unusedpart"])


@task
def rc_version(context):  # pylint: disable=unused-argument
    """Make a new release candidate version tag of GPF."""
    repo = git_repo()
    if repo.head.is_detached:
        logger.error("In detached HEAD state, refusing to release")
        sys.exit(1)
    elif repo.active_branch.name not in {"master", "staging"}:
        logger.error("Not on the master branch, refusing to release")
        sys.exit(1)

    # Get the current date info
    date_info = now()

    # Identify and set the increment
    for tag in reversed(repo.tags):
        if VERSION_REGEX.fullmatch(tag.name):
            latest_version = Version(tag.name)
            break
    else:
        latest_version = None

    if latest_version:
        if latest_version.major == date_info[0] \
                and latest_version.minor == date_info[1]:
            if latest_version.pre is not None:
                new_version = Version(
                    f"{latest_version.major}.{latest_version.minor}."
                    f"{latest_version.micro}rc{latest_version.pre[1] + 1}")
            elif latest_version.dev is not None:
                new_version = Version(
                    f"{latest_version.major}.{latest_version.minor}."
                    f"{latest_version.micro}rc0")
            else:
                new_version = Version(
                    f"{latest_version.major}.{latest_version.minor}."
                    f"{latest_version.micro + 1}rc0")
        else:
            new_version = Version(
                f"{date_info[0]}.{date_info[1]}.0rc0")
    else:
        new_version = Version(
            f"{date_info[0]}.{date_info[1]}.0rc0")

    logger.error("new version %s", new_version)
    bumpversion(["--new-version", str(new_version), "unusedpart"])
