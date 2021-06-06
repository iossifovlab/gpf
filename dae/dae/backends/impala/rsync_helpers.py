import os
import subprocess
import logging

from urllib.parse import urlparse, urlunparse


logger = logging.getLogger(__name__)


class RsyncHelpers:

    def __init__(self, remote):
        if not remote.endswith("/"):
            remote += "/"
        self.remote = remote

        parsed_remote = urlparse(remote)
        self.parsed_remote = parsed_remote
        if parsed_remote.scheme:
            assert parsed_remote.scheme == "ssh"

        self.rsync_remote = remote
        if parsed_remote.hostname:
            self.rsync_remote = \
                f"{parsed_remote.hostname}:{parsed_remote.path}"
            if parsed_remote.username:
                self.rsync_remote = \
                    f"{parsed_remote.username}@{self.rsync_remote}"

        self.rsync_remote_shell = None
        if parsed_remote.port and parsed_remote.port != 22:
            self.rsync_remote_shell = f"ssh -p {parsed_remote.port}"

        logger.debug(f"parsed_remote: {parsed_remote}")

    def hosturl(self):
        logger.debug(self.parsed_remote)

        return urlunparse(
            (
                self.parsed_remote.scheme,
                self.parsed_remote.netloc,
                "",  # path
                "",  # params
                "",  # query
                "",  # fragment identifier
            ))

    def _exclude_options(self, exclude=[]):
        if not exclude:
            return []
        result = []
        for ex in exclude:
            if not ex:
                continue

            result.extend(["--exclude", f"{ex}"])
        return result

    def _copy_to_remote_cmd(
            self, local_path, remote_subdir=None,
            exclude=[],
            ignore_existing=False,
            clear_remote=True):

        logger.debug(f"rsync remote: {self.rsync_remote}")
        logger.debug(f"rsync hosturl: {self.hosturl()}")

        cmds = []

        if os.path.isdir(local_path):
            local_dir = local_path
            if not local_path.endswith("/"):
                local_path += "/"
        else:
            local_dir = os.path.dirname(local_path)
        if not local_dir.endswith("/"):
            local_dir += "/"

        logger.debug(f"rsync remote: <{self.rsync_remote}>")

        rsync_path = ""
        rsync_remote = self.rsync_remote

        if remote_subdir is not None:
            if remote_subdir.startswith("/"):
                remote_subdir = remote_subdir[1:]
            rsync_path = os.path.join(self.parsed_remote.path, remote_subdir)
            rsync_remote = os.path.join(self.rsync_remote, remote_subdir)

            if clear_remote:
                if self.hosturl():
                    cmds.append(
                        [
                            "ssh", f"{self.parsed_remote.netloc}",
                            f"rm -rf {rsync_path}"
                        ])
                else:
                    cmds.append(["rm", "-rf", "{rsync_path}"])

            if self.hosturl():
                cmds.append(
                    [
                        "ssh", f"{self.parsed_remote.netloc}",
                        f"mkdir -p {rsync_path}"
                    ])
            else:
                cmds.append(["mkdir", "-p", f"{rsync_path}"])

        rsync_cmd = ["/usr/bin/rsync", "-avPHt"]
        exclude_options = self._exclude_options(exclude)
        rsync_cmd.extend(exclude_options)

        if ignore_existing:
            rsync_cmd.append("--ignore-existing")
        if self.rsync_remote_shell:
            rsync_cmd.extend(["-e", self.rsync_remote_shell])
        rsync_cmd.extend([local_path, rsync_remote])
        logger.debug(f"rsync command: {rsync_cmd}")
        cmds.append(rsync_cmd)

        return cmds

    def _copy_to_local_cmd(self, local_path, remote_subdir=None, exclude=[]):
        os.makedirs(local_path, exist_ok=True)
        cmds = []

        if not local_path.endswith("/"):
            local_path += "/"

        rsync_remote = self.rsync_remote
        if remote_subdir is not None:
            if remote_subdir.startswith("/"):
                remote_subdir = remote_subdir[1:]
            rsync_remote = os.path.join(self.rsync_remote, remote_subdir)

        rsync_cmd = ["/usr/bin/rsync", "-avPHt"]
        if self.rsync_remote_shell:
            rsync_cmd.extend(["-e", self.rsync_remote_shell])
        exclude_options = self._exclude_options(exclude)
        rsync_cmd.extend(exclude_options)
        rsync_cmd.extend([rsync_remote, local_path])
        cmds.append(rsync_cmd)

        return cmds

    def _cmd_execute(self, commands):
        for cmd in commands:
            logger.info(f"executing command: {cmd}")
            # argv = [c.strip() for c in cmd.split(" ")]
            # argv = list(filter(lambda c: len(c) > 0, argv))
            logger.debug(f"executing command: {cmd}")

            with subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True) as proc:

                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    logger.debug(line)

            logger.debug(f"command {cmd} finished")
            if proc.returncode:
                logger.error(f"command {cmd} finished with {proc.returncode}")
                raise ValueError(f"error in {cmd}")

    def clear_remote(self, remote_subdir):
        cmds = []
        rsync_path = ""
        assert remote_subdir is not None

        if remote_subdir.startswith("/"):
            remote_subdir = remote_subdir[1:]
        rsync_path = os.path.join(self.parsed_remote.path, remote_subdir)

        if self.hosturl():
            cmds.append(
                [
                    "ssh", f"{self.parsed_remote.netloc}",
                    f"rm -rf {rsync_path}"
                ])
            cmds.append(
                [
                    "ssh", f"{self.parsed_remote.netloc}",
                    f"mkdir -p {rsync_path}"
                ])
        else:
            cmds.append(["rm", "-rf", f"{rsync_path}"])
            cmds.append(["mkdir", "-p", f"{rsync_path}"])
        self._cmd_execute(cmds)

    def copy_to_remote(
            self, local_path, remote_subdir=None, exclude=[],
            clear_remote=True):
        logger.debug(
            f"copying {local_path} to {remote_subdir}")

        cmd = self._copy_to_remote_cmd(
            local_path, remote_subdir=remote_subdir, exclude=exclude,
            clear_remote=clear_remote)

        self._cmd_execute(cmd)

    def copy_to_local(self, local_path, remote_subdir=None, exclude=[]):
        cmd = self._copy_to_local_cmd(
            local_path, remote_subdir=remote_subdir, exclude=exclude)
        self._cmd_execute(cmd)
