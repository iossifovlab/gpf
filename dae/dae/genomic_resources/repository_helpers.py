import os
import logging

import yaml

from .dir_repository import GenomicResourceDirRepo
from .repository import GenomicResource, Manifest, ManifestEntry

logger = logging.getLogger(__name__)


class RepositoryWorkflowHelper:
    """Helper class to support genomic resources management workflow."""

    def __init__(self, repo: GenomicResourceDirRepo):
        self.repo: GenomicResourceDirRepo = repo

    def check_manifest_timestamps(self, resource: GenomicResource) -> bool:
        """
        Checks if resource manifest needs update using timestamps.

        The check is done using resoruce files timestamps. If all the
        timestamps match, returns True. Otherwise returns False.
        """
        current_manifest = self.repo.load_manifest(resource)
        new_manifest = Manifest()
        for fname, fsize, ftime in sorted(
                self.repo.collect_resource_files(resource)):
            md5 = None
            if fname in current_manifest:
                entry = current_manifest[fname]
                if entry.size == fsize and entry.time == ftime:
                    md5 = entry.md5
            new_manifest.add(ManifestEntry(fname, fsize, ftime, md5))
        if current_manifest != new_manifest:
            logger.warning(
                "resource %s needs manifest update", resource.resource_id)
            return False
        logger.info(
            "manifest timestamps are OK for <%s>", resource.resource_id)
        return True

    def check_manifest_md5sums(self, resource):
        """
        Checks if md5 sums of resource's files match the manifest's md5 sums.
        """
        current_manifest = self.repo.load_manifest(resource)

        diff = []
        for fname, _fsize, _ftime in sorted(
                self.repo.collect_resource_files(resource)):
            manifest_md5 = None
            if fname in current_manifest:
                entry = current_manifest[fname]
                manifest_md5 = entry.md5
            computed_md5 = self.repo.compute_md5_sum(resource, fname)
            if manifest_md5 != computed_md5:
                diff.append((fname, manifest_md5, computed_md5))
        if diff:
            for fname, manifest_md5, computed_md5 in diff:
                logger.warning(
                    "resource (%s) file %s manifest md5 %s does not match "
                    "computed md5 %s",
                    resource.get_id(), fname, manifest_md5, computed_md5)
            return False
        return True

    def _precheck_checkout_manifest_timestamps(self, resource):
        current_manifest = self.repo.load_manifest(resource)
        manifest_files = {
            fname
            for fname, _, _ in current_manifest.get_files()
        }
        resource_files = {
            fname
            for fname, _, _ in self.repo.collect_resource_files(resource)
        }

        new_files = resource_files.difference(manifest_files)
        if new_files:
            logger.error(
                "new files %s found in resource <%s>",
                new_files, resource.resource_id)
        deleted_files = manifest_files.difference(resource_files)
        if deleted_files:
            logger.error(
                "files %s deleted from resource <%s>",
                deleted_files, resource.resource_id)
        if new_files or deleted_files:
            return False
        assert manifest_files == resource_files

        diff = []
        for entry in current_manifest:
            computed_md5 = self.repo.compute_md5_sum(resource, entry.name)
            if entry.md5 != computed_md5:
                diff.append((entry.name, entry.md5, computed_md5))
        if diff:
            for fname, manifest_md5, computed_md5 in diff:
                logger.warning(
                    "resource (%s) file %s manifest md5 %s does not match "
                    "computed md5 %s",
                    resource.get_id(), fname, manifest_md5, computed_md5)
            return False

        return True

    def checkout_manifest_timestamps(self, resource, dry_run=False):
        """
        Gets timestamps from manifest and sets them to resource's files.
        """
        if not self._precheck_checkout_manifest_timestamps(resource):
            return False

        current_manifest = resource.get_manifest()

        for fname, _fsize, ftime in self.repo.collect_resource_files(resource):
            entry = current_manifest[fname]
            if ftime == entry.time:
                logger.info(
                    "file %s from resource %s timestamp is OK",
                    entry.name, resource.resource_id)
            else:
                logger.warning(
                    "updating timestamp of file %s from resource %s to %s",
                    entry.name, resource.resource_id, entry.time)
                if not dry_run:
                    filepath = self.repo.get_filepath(resource, entry.name)
                    timestamp = entry.get_timestamp()
                    os.utime(filepath, (timestamp, timestamp))
        return True

    def build_repo_content(self):
        """Builds the content of the .CONTENTS file."""
        content = [
            {
                "id": gr.resource_id,
                "version": gr.get_version_str(),
                "config": gr.get_config(),
                "manifest": gr.get_manifest().to_manifest_entries()
            }
            for gr in self.repo.get_all_resources()]
        content = sorted(content, key=lambda x: x["id"])
        return content

    def update_repository_content_file(self):
        """Creates or updates the content file for the repository."""
        content_filepath = self.repo.get_content_filepath()
        old_content = None
        if content_filepath.exists():
            with content_filepath.open("rt", encoding="utf8") as infile:
                old_content = yaml.safe_load(infile.read())

        content = self.build_repo_content()
        if content == old_content:
            logger.info("repository content file is up-to-date")
        else:
            logger.info("saving contents file %s", content_filepath)
            with content_filepath.open("wt", encoding="utf8") as outfile:
                yaml.dump(content, outfile)

    def check_repository_content_file(self):
        """Checks if the repository's content file is up-to-date."""
        content_filepath = self.repo.get_content_filepath()
        old_content = None
        if content_filepath.exists():
            with content_filepath.open("rt", encoding="utf8") as infile:
                old_content = yaml.safe_load(infile.read())

        content = self.build_repo_content()
        if content == old_content:
            logger.info("repository content file is up-to-date")
            return True
        else:
            logger.info("repository content file needs updating.")
            return False

    def update_manifest(self, resource):
        """Updates resource manifest and stores it."""
        try:
            current_manifest = self.repo.load_manifest(resource)
            new_manifest = Manifest()
            for fname, fsize, ftime in sorted(
                    self.repo.collect_resource_files(resource)):
                md5 = None
                if fname in current_manifest:
                    entry = current_manifest[fname]
                    if entry.size == fsize and entry.time == ftime:
                        md5 = entry.md5
                    else:
                        logger.debug(
                            "md5 sum for file %s for resource %s needs update",
                            fname, resource.resource_id)
                else:
                    logger.debug(
                        "found a new file %s for resource %s",
                        fname, resource.resource_id)
                if md5 is None:
                    md5 = self.repo.compute_md5_sum(resource, fname)
                new_manifest.add(
                    ManifestEntry(fname, fsize, ftime, md5))

            if new_manifest == current_manifest:
                logger.debug("manifest OK for %s", resource.resource_id)
            else:
                logger.debug("manifest updated for %s", resource.resource_id)
                self.repo.save_manifest(resource, new_manifest)
        except IOError:
            logger.info(
                "building a new manifest for resource %s",
                resource.resource_id, exc_info=True)
            manifest = self.repo.build_manifest(resource)
            self.repo.save_manifest(resource, manifest)
