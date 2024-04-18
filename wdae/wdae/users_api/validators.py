from typing import Any, List, Union

from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import WdaeUser


class SomeSuperuserLeftValidator:
    """Validates that at least one superuser is left in the system."""

    def __init__(self) -> None:
        self.is_update = False
        self.user_instance = None

    def __call__(self, value: List[Union[Any, Group]]) -> None:
        if not self.is_update:
            return

        group_names = list(map(str, value))
        has_superuser = WdaeUser.SUPERUSER_GROUP in group_names
        try:
            superuser_group = Group.objects.get(name=WdaeUser.SUPERUSER_GROUP)
        except Group.DoesNotExist:
            return

        superusers = superuser_group.user_set.all()  # type: ignore
        assert self.user_instance is not None

        if (
            len(superusers) == 1
            and superusers[0].pk == self.user_instance.pk
            and not has_superuser
        ):
            raise serializers.ValidationError(
                f"The group {WdaeUser.SUPERUSER_GROUP} cannot be removed. "
                f"No superuser will be left if that is done.",
            )

    def set_context(self, serializer_field: Any) -> None:
        """Set the context for the validator."""
        current = serializer_field
        while hasattr(current, "parent") and current.parent is not None:
            current = current.parent

        instance = current.instance

        self.is_update = instance is not None
        self.user_instance = instance
