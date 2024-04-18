from django.contrib.auth import get_user_model
from django.db import models
from query_state_save.models import QueryState


class UserQuery(models.Model):
    """Represents users management queries."""

    user: models.ForeignKey = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE)
    query: models.ForeignKey = models.ForeignKey(
        QueryState, on_delete=models.CASCADE)
    name: models.CharField = models.CharField(
        blank=False, null=False, max_length=256)
    description: models.CharField = models.CharField(
        max_length=1024)
