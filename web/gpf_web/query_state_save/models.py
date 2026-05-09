import uuid

from django.db import models

ORIGIN = [
    ("saved", "saved"),
    ("user", "user"),
    ("system", "system"),
]

PAGE_TYPES = [
    ("genotype", "Genotype browser"),
    ("phenotype", "Phenotype browser"),
    ("enrichment", "Enrichment tool"),
    ("phenotool", "Phenotype tool"),
]

PAGE_TYPE_OPTIONS = [x[0] for x in PAGE_TYPES]


class QueryState(models.Model):
    """Model for saved queries, shared queries and system generated queries."""
    data: models.TextField = models.TextField(
        null=False, blank=False)
    page: models.CharField = models.CharField(
        blank=False, null=False, max_length=10, choices=PAGE_TYPES)
    uuid = models.UUIDField(default=uuid.uuid4)
    timestamp: models.DateField = models.DateField(
        null=True,
        default=None,
    )
    origin: models.CharField = models.CharField(
        blank=True,
        max_length=10,
        choices=ORIGIN,
        null=True,
        default=None,
    )
