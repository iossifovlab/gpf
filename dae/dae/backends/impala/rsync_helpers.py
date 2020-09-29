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
            return ""
        result = [f"--exclude {ex}" for ex in exclude if ex]
        if not result:
            return ""
        return " ".join(result)

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

        exclude_options = self._exclude_options(exclude)
        logger.debug(f"rsync remote: {self.rsync_remote}")

        rsync_remote = self.rsync_remote
        rsync_path = ""
        if remote_subdir is not None:
            if remote_subdir.startswith("/"):
                remote_subdir = remote_subdir[1:]
            rsync_remote = os.path.join(self.rsync_remote, remote_subdir)
            rsync_path = os.path.join(self.parsed_remote.path, remote_subdir)

            clear_remote_option = ""
            if clear_remote:
                clear_remote_option = f"rm -rf {rsync_path} && "

            if self.hosturl():
                cmds.append(
                    f'ssh {self.rsync_remote} "{clear_remote_option}'
                    f'mkdir -p {rsync_path} && rsync"')
            else:
                cmds.append(
                    f'{clear_remote_option} mkdir -p {rsync_path}')

        ignore_existing_option = ""
        if ignore_existing:
            ignore_existing_option = "--ignore-existing"

        if self.rsync_remote_shell is None:
            cmds.append(
                f"rsync -avPHt {exclude_options} "
                f"{ignore_existing_option} "
                f"{local_path} {rsync_remote}")
        else:
            cmds.append(
                f'rsync -e "{self.rsync_remote_shell}" '
                f'-avPHt {exclude_options} '
                f"{ignore_existing_option} "
                f'{local_path} {rsync_remote}')
        return cmds

    def _copy_to_local_cmd(self, local_path, remote_subdir=None, exclude=[]):
        os.makedirs(local_path, exist_ok=True)
        exclude_options = self._exclude_options(exclude)

        if not local_path.endswith("/"):
            local_path += "/"

        rsync_remote = self.rsync_remote
        if remote_subdir is not None:
            if remote_subdir.startswith("/"):
                remote_subdir = remote_subdir[1:]
            rsync_remote = os.path.join(self.rsync_remote, remote_subdir)

        if self.rsync_remote_shell is None:
            return f"rsync -avPHt {exclude_options} " \
                f"{rsync_remote} {local_path}"
        else:
            return f'rsync -e "{self.rsync_remote_shell}" '\
                f'-avPHt {exclude_options} {local_path}'

    def _cmd_execute(self, commands):
        for cmd in commands:
            logger.info(f"executing command: {cmd}")
            result = subprocess.run(
                cmd, shell=True, text=True, capture_output=True)

            assert result.returncode == 0, result

    def copy_to_remote(self, local_path, remote_subdir=None, exclude=[]):
        cmd = self._copy_to_remote_cmd(
            local_path, remote_subdir=remote_subdir, exclude=exclude)
        self._cmd_execute(cmd)

    def copy_to_local(self, local_path, remote_subdir=None, exclude=[]):
        cmd = self._copy_to_local_cmd(
            local_path, remote_subdir=remote_subdir, exclude=exclude)
        self._cmd_execute(cmd)
