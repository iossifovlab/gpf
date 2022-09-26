# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.impala_storage.rsync_helpers import RsyncHelpers


def test_rsync_helpers_ssh():
    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:/mnt/hdfs2nfs")
    assert helpers is not None

    assert helpers.rsync_remote == "root@seqclust0.seqpipe.org:/mnt/hdfs2nfs/"


def test_rsync_helpers_local():
    helpers = RsyncHelpers("/mnt/hdfs2nfs")
    assert helpers is not None

    assert helpers.rsync_remote == "/mnt/hdfs2nfs/"


def test_copy_to_remote_ssh_file(temp_filename, mocker):
    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:/mnt/hdfs2nfs")
    mocker.patch("os.path.isfile", return_value=True)

    cmd = helpers._copy_to_remote_cmd(temp_filename)

    print(cmd)
    assert cmd[0][-1].endswith("/mnt/hdfs2nfs/")


def test_copy_to_remote_ssh_dir(temp_dirname, mocker):
    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:/mnt/hdfs2nfs")
    mocker.patch("os.path.isdir", return_value=True)

    cmd = helpers._copy_to_remote_cmd(temp_dirname)

    print(temp_dirname, cmd)
    assert cmd[0][-1].endswith("/mnt/hdfs2nfs/")
    assert f"{temp_dirname}/" in cmd[0]


def test_rsync_helpers_ssh_port2022(temp_dirname, mocker):
    mocker.patch("os.path.isdir", return_value=True)

    helpers = RsyncHelpers(
        "ssh://root@seqclust0.seqpipe.org:2022/mnt/hdfs2nfs")
    assert helpers is not None

    assert helpers.rsync_remote == "root@seqclust0.seqpipe.org:/mnt/hdfs2nfs/"
    assert helpers.rsync_remote_shell == "ssh -p 2022"

    cmd = helpers._copy_to_remote_cmd(temp_dirname)

    print(temp_dirname, cmd)

    assert "ssh -p 2022" in cmd[0]
    assert "-e" in cmd[0]


def test_exclude_options(temp_dirname):
    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:/mnt/hdfs2nfs")
    assert not helpers._exclude_options([])
    assert not helpers._exclude_options(None)
    assert not helpers._exclude_options("")

    cmds = helpers._copy_to_remote_cmd(temp_dirname, exclude=[".git", ".dvc"])
    print(cmds)
    rsync_cmd = cmds[0]
    assert "--exclude" in rsync_cmd
    assert ".git" in rsync_cmd
    assert ".dvc" in rsync_cmd


def test_rsync_remote_subdir(temp_dirname):
    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:/mnt/hdfs2nfs")
    assert helpers is not None

    assert helpers.rsync_remote == "root@seqclust0.seqpipe.org:/mnt/hdfs2nfs/"

    cmd = helpers._copy_to_remote_cmd(
        temp_dirname, remote_subdir="/user/data-hg19-test/studies/")

    print(cmd)


@pytest.mark.parametrize(
    "location,expected", [
        (
            "ssh://root@seqclust0.seqpipe.org/mnt/hdfs2nfs",
            "ssh://root@seqclust0.seqpipe.org"),
        (
            "//seqclust0.seqpipe.org/mnt/hdfs2nfs",
            "//seqclust0.seqpipe.org"),
        (
            "/mnt/hdfs2nfs",
            ""),
    ],
)
def test_rsync_build_location_base(location, expected):
    helpers = RsyncHelpers(location)
    assert helpers.hosturl() == expected
