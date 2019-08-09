from django.db import models
from django.contrib.auth import get_user_model
from query_state_save.models import QueryState


class UserQuery(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    query = models.ForeignKey(QueryState, on_delete=models.CASCADE)
    name = models.CharField(blank=False, null=False, max_length=256)
    description = models.CharField(max_length=1024)
