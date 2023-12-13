import os
import subprocess
import logging

from urllib.parse import urlparse, urlunparse
from typing import List, Optional, Union


logger = logging.getLogger(__name__)


class RsyncHelpers:
    """A class containing helper funcs for working with rsync."""

    def __init__(self, remote: str) -> None:
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

        logger.debug("parsed_remote: %s", parsed_remote)

    def hosturl(self) -> str:
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

    @staticmethod
    def _exclude_options(
        exclude: Optional[Union[str, List[str]]] = None
    ) -> List[str]:
        if exclude is None:
            return []
        result = []
        for ex in exclude:
            if not ex:
                continue

            result.extend(["--exclude", f"{ex}"])
        return result

    def _copy_to_remote_cmd(
        self, local_path: str, remote_subdir: Optional[str] = None,
        exclude: Optional[List[str]] = None,
        ignore_existing: bool = False,
        clear_remote: bool = True
    ) -> List[List[str]]:
        # pylint: disable=too-many-branches
        exclude = exclude if exclude is not None else []
        logger.debug("rsync remote: %s", self.rsync_remote)
        logger.debug("rsync hosturl: %s", self.hosturl())

        cmds = []

        if os.path.isdir(local_path):
            local_dir = local_path
            if not local_path.endswith("/"):
                local_path += "/"
        else:
            local_dir = os.path.dirname(local_path)
        if not local_dir.endswith("/"):
            local_dir += "/"

        logger.debug("rsync remote: <%s>", self.rsync_remote)

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
        logger.debug("rsync command: %s", rsync_cmd)
        cmds.append(rsync_cmd)

        return cmds

    def _copy_to_local_cmd(
        self, local_path: str,
        remote_subdir: Optional[str] = None,
        exclude: Optional[list[str]] = None
    ) -> list[list[str]]:
        exclude = exclude if exclude is not None else []
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

    @staticmethod
    def _cmd_execute(commands: list[list[str]]) -> None:
        for cmd in commands:
            logger.info("executing command: %s", cmd)
            logger.debug("executing command: %s", cmd)

            with subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True) as proc:

                while True:
                    assert proc.stdout is not None
                    line = proc.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    logger.debug(line)

            logger.debug("command %s finished", cmd)
            if proc.returncode:
                logger.error("command %s finished with %s",
                             cmd, proc.returncode)
                raise ValueError(f"error in {cmd}")

    def clear_remote(self, remote_subdir: str) -> None:
        """Clear the remote directory."""
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
        self, local_path: str,
        remote_subdir: Optional[str] = None,
        exclude: Optional[list[str]] = None,
        clear_remote: bool = True
    ) -> None:
        """Copy from a local dir to a remote one."""
        logger.debug("copying %s to %s", local_path, remote_subdir)

        cmd = self._copy_to_remote_cmd(
            local_path, remote_subdir=remote_subdir, exclude=exclude,
            clear_remote=clear_remote)

        self._cmd_execute(cmd)

    def copy_to_local(
        self, local_path: str,
        remote_subdir: Optional[str] = None,
        exclude: Optional[list[str]] = None
    ) -> None:
        """Copy files from remote server to local machine.

        Args:
            local_path (str): The local directory where the files will be
                copied to.
            remote_subdir (Optional[str], optional): The remote subdirectory
                to copy files from. Defaults to None.
            exclude (Optional[list[str]], optional): List of patterns to
                exclude from the copy. Defaults to None.
        """
        cmd = self._copy_to_local_cmd(
            local_path, remote_subdir=remote_subdir, exclude=exclude)
        self._cmd_execute(cmd)
