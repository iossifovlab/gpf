from dae.backends.impala.rsync_helpers import RsyncHelpers


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
    assert cmd.endswith("/mnt/hdfs2nfs/")


def test_copy_to_remote_ssh_dir(temp_dirname, mocker):
    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:/mnt/hdfs2nfs")
    mocker.patch("os.path.isdir", return_value=True)

    cmd = helpers._copy_to_remote_cmd(temp_dirname)

    print(temp_dirname, cmd)
    assert cmd.endswith("/mnt/hdfs2nfs/")
    assert f"{temp_dirname}/" in cmd


def test_rsync_helpers_ssh_port2022(temp_dirname, mocker):
    mocker.patch("os.path.isdir", return_value=True)

    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:2022/mnt/hdfs2nfs")
    assert helpers is not None

    assert helpers.rsync_remote == "root@seqclust0.seqpipe.org:/mnt/hdfs2nfs/"
    assert helpers.rsync_remote_shell == "ssh -p 2022"

    cmd = helpers._copy_to_remote_cmd(temp_dirname)

    print(temp_dirname, cmd)

    assert '-e "ssh -p 2022"' in cmd


def test_exclude_options(temp_dirname):
    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:/mnt/hdfs2nfs")
    assert helpers._exclude_options([]) == ""
    assert helpers._exclude_options(None) == ""
    assert helpers._exclude_options("") == ""

    cmd = helpers._copy_to_remote_cmd(temp_dirname, exclude=[".git", ".dvc"])
    print(cmd)
    assert "--exclude .git" in cmd
    assert "--exclude .dvc" in cmd


def test_rsync_remote_subdir(temp_dirname):
    helpers = RsyncHelpers("ssh://root@seqclust0.seqpipe.org:/mnt/hdfs2nfs")
    assert helpers is not None

    assert helpers.rsync_remote == "root@seqclust0.seqpipe.org:/mnt/hdfs2nfs/"

    cmd = helpers._copy_to_remote_cmd(
        temp_dirname, remote_subdir="/user/data-hg19-test/studies/")

    print(cmd)
