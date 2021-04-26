import logging

from django.db.models import Q
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from datasets_api.models import Dataset

from .dataset_mixin import DatasetBaseMixin


logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    help = "clean up groups that are not in use"

    def __init__(self, **kwargs):
        DatasetBaseMixin.__init__(self)
        BaseCommand.__init__(self, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", "-n", action="store_true")

    def cleanup_wdae_datasets(self, dry_run):
        dataset_ids = set(self.gpf_instance.get_genotype_data_ids())

        datasets = list(Dataset.objects.all())
        for dataset in datasets:
            logger.debug(f"checking wdae dataset: {dataset.dataset_id}")
            if dataset.dataset_id not in dataset_ids:
                logger.info(f"removing dataset {dataset.dataset_id}")
                if not dry_run:
                    dataset.delete()

    def cleanup_groups(self, dry_run):
        groups = list(Group.objects.filter(
            Q(groupobjectpermission__permission__codename="view")).distinct())

        for group in groups:
            logger.debug(
                f"checking group: {group.name} ({group.id})")
            users = list(group.user_set.all())
            if users:
                logger.debug(
                    f"group {group.name} has users {len(users)}; keeping...")
                logger.debug(f"{[user.email for user in users]}")
                continue
            logger.debug(f"group {group.name} has no attached users")

            permissions = list(group.groupobjectpermission_set.all())
            logger.debug(f"clean up permissions: {permissions};")
            for permission in permissions:
                if permission.content_object is None:
                    logger.debug(f"removing permission: {permission}")
                    if not dry_run:
                        permission.delete()
            permissions = list(group.groupobjectpermission_set.all())
            logger.debug(f"permissions: {permissions};")
            if not permissions:
                logger.info(f"removing group {group.name}")
                if not dry_run:
                    group.delete()

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        self.cleanup_wdae_datasets(dry_run)
        self.cleanup_groups(dry_run)
