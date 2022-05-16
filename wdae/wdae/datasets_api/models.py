from django.db import models
from django.contrib.auth.models import Group


class Dataset(models.Model):
    dataset_id: models.TextField = models.TextField()
    groups = models.ManyToManyField(Group)

    @property
    def default_groups(self):
        return ["any_dataset", self.dataset_id]

    @classmethod
    def recreate_dataset_perm(cls, dataset_id):
        dataset_object, _ = cls.objects.get_or_create(dataset_id=dataset_id)
        for group_name in dataset_object.default_groups:
            group, _created = Group.objects.get_or_create(name=group_name)
            dataset_object.groups.add(group)
