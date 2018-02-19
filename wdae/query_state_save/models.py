import uuid
from django.db import models

PAGE_TYPES = [
    ("genotype", "Genotype browser"),
    ("phenotype", "Phenotype browser"),
    ("enrichment", "Enrichment tool"),
    ("phenotool", "Phenotype tool")
]

PAGE_TYPE_OPTIONS = map(lambda x: x[0], PAGE_TYPES)


class QueryState(models.Model):

    data = models.TextField(null=False, blank=False)
    page = models.CharField(
        blank=False, null=False, max_length=10,
        choices=PAGE_TYPES)
    uuid = models.UUIDField(default=uuid.uuid4)

