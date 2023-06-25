# pylint: disable=W0621,C0114,C0116,W0212,W0613
from packaging.version import Version

import pytest
from invoke.context import Context

from tasks import VERSION_REGEX, release_version, dev_version, rc_version


@pytest.mark.parametrize("version, expected", [
    ("2023.6.0", ("2023", "6", "0", None, None)),
    ("2023.6.0dev0", ("2023", "6", "0", "dev", "0")),
    ("2023.6.0dev99", ("2023", "6", "0", "dev", "99")),
    ("2023.6.0dev9999", ("2023", "6", "0", "dev", "9999")),
    ("2023.6.1rc0", ("2023", "6", "1", "rc", "0")),
    ("2023.6.1", ("2023", "6", "1", None, None)),
])
def test_version_regex_match(version, expected):
    py_version = Version(version)
    assert py_version

    match = VERSION_REGEX.fullmatch(version)
    assert match is not None
    assert tuple(match.groupdict().values()) == expected


def test_release_detached_head(mocker):
    mock_repo = mocker.Mock()
    mock_repo.head = mocker.Mock()
    mock_repo.head.is_detached = True

    mocker.patch("tasks.git_repo", return_value=mock_repo)
    with pytest.raises(SystemExit):
        release_version(Context(None))


def test_release_not_master_branch(mocker):
    mock_repo = mocker.Mock()
    mock_repo.head = mocker.Mock()
    mock_repo.head.is_detached = False
    mock_repo.active_branch = mocker.Mock()
    mock_repo.active_branch.name = "test-branch"

    mocker.patch("tasks.git_repo", return_value=mock_repo)
    with pytest.raises(SystemExit):
        release_version(Context(None))


@pytest.mark.parametrize("prev_version, now, new_version", [
    ("2023.6.0dev0", (2023, 6), "2023.6.0"),
    ("2023.6.0dev1", (2023, 6), "2023.6.0"),
    ("2023.6.0rc99", (2023, 6), "2023.6.0"),
    ("2023.6.0rc99", (2023, 7), "2023.7.0"),
    ("2023.6.0.dev99", (2023, 7), "2023.7.0"),
])
def test_release_version_available_latest_release(
        mocker, prev_version, now, new_version):
    mock_repo = mocker.Mock()
    mock_repo.head = mocker.Mock()
    mock_repo.head.is_detached = False
    mock_repo.active_branch = mocker.Mock()
    mock_repo.active_branch.name = "master"

    mock_tag = mocker.Mock()
    mock_tag.name = prev_version

    mock_repo.tags = [mock_tag]

    mocker.patch("tasks.git_repo", return_value=mock_repo)
    mocker.patch("tasks.now", return_value=now)

    mock_bumper = mocker.patch("tasks.bumpversion", autospec=True)

    release_version(Context(None))

    mock_bumper.assert_called_once_with([
        "--new-version", new_version, "unusedpart"
    ])


@pytest.mark.parametrize("prev_version, now, new_version", [
    ("2023.6.0dev0", (2023, 6), "2023.6.0.dev1"),
    ("2023.6.0dev0", (2023, 7), "2023.6.0.dev1"),
    ("2023.6.0", (2023, 6), "2023.6.1.dev0"),
    ("2023.6.1", (2023, 6), "2023.6.2.dev0"),
])
def test_dev_version_available_latest_release(
        mocker, prev_version, now, new_version):
    mock_repo = mocker.Mock()
    mock_repo.head = mocker.Mock()
    mock_repo.head.is_detached = False
    mock_repo.active_branch = mocker.Mock()
    mock_repo.active_branch.name = "master"

    mock_tag = mocker.Mock()
    mock_tag.name = prev_version

    mock_repo.tags = [mock_tag]

    mocker.patch("tasks.git_repo", return_value=mock_repo)
    mocker.patch("tasks.now", return_value=now)

    mock_bumper = mocker.patch("tasks.bumpversion", autospec=True)

    dev_version(Context(None))

    mock_bumper.assert_called_once_with([
        "--new-version", new_version, "unusedpart"
    ])


@pytest.mark.parametrize("prev_version, now, new_version", [
    ("foobar", (2023, 6), "2023.6.0rc0"),
    ("2023.6.0dev1", (2023, 6), "2023.6.0rc0"),
    ("2023.6.0rc0", (2023, 6), "2023.6.0rc1"),
    ("2023.6.0", (2023, 6), "2023.6.1rc0"),
    ("2023.6.0", (2023, 7), "2023.7.0rc0"),
    ("2023.6.1", (2023, 7), "2023.7.0rc0"),
    ("2023.6.1.dev1", (2023, 7), "2023.7.0rc0"),
    ("2023.6.1.rc1", (2023, 7), "2023.7.0rc0"),
])
def test_rc_version_available_latest_release(
        mocker, prev_version, now, new_version):
    mock_repo = mocker.Mock()
    mock_repo.head = mocker.Mock()
    mock_repo.head.is_detached = False
    mock_repo.active_branch = mocker.Mock()
    mock_repo.active_branch.name = "master"

    mock_tag = mocker.Mock()
    mock_tag.name = prev_version

    mock_repo.tags = [mock_tag]

    mocker.patch("tasks.git_repo", return_value=mock_repo)
    mocker.patch("tasks.now", return_value=now)

    mock_bumper = mocker.patch("tasks.bumpversion", autospec=True)

    rc_version(Context(None))

    mock_bumper.assert_called_once_with([
        "--new-version", new_version, "unusedpart"
    ])
