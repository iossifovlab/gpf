import uuid

from django.db import models

PAGE_TYPES = [
    ("genotype", "Genotype browser"),
    ("phenotype", "Phenotype browser"),
    ("enrichment", "Enrichment tool"),
    ("phenotool", "Phenotype tool"),
]

PAGE_TYPE_OPTIONS = [x[0] for x in PAGE_TYPES]


class QueryState(models.Model):

    data: models.TextField = models.TextField(
        null=False, blank=False)
    page: models.CharField = models.CharField(
        blank=False, null=False, max_length=10, choices=PAGE_TYPES)
    uuid = models.UUIDField(default=uuid.uuid4)  # type: ignore
