from rest_framework import serializers
from .models import WdaeUser
from django.contrib.auth.models import Group


class ProtectedGroupsValidator(object):
    def __init__(self):
        self.is_update = False
        self.user_instance = None

    def __call__(self, value):
        if not self.is_update:
            return

        group_names = list(map(str, value))
        missing_groups = []
        for group in self.user_instance.get_protected_group_names():
            if group not in group_names:
                message = "The group {} cannot be removed.".format(group)
                missing_groups.append(message)

        if len(missing_groups) > 0:
            raise serializers.ValidationError(missing_groups)

    def set_context(self, serializer_field):
        current = serializer_field
        while hasattr(current, "parent") and current.parent is not None:
            current = current.parent

        instance = current.instance

        self.is_update = instance is not None
        self.user_instance = instance


class SomeSuperuserLeftValidator(object):
    def __init__(self):
        self.is_update = False
        self.user_instance = None

    def __call__(self, value):
        if not self.is_update:
            return

        group_names = list(map(str, value))
        has_superuser = WdaeUser.SUPERUSER_GROUP in group_names
        try:
            superuser_group = Group.objects.get(name=WdaeUser.SUPERUSER_GROUP)
        except Group.DoesNotExist:
            return

        superusers = superuser_group.user_set.all()
        if (
            len(superusers) == 1
            and superusers[0].pk == self.user_instance.pk
            and not has_superuser
        ):
            raise serializers.ValidationError(
                "The group {} cannot be removed. No superuser will be left if "
                "that is done.".format(WdaeUser.SUPERUSER_GROUP)
            )

    def set_context(self, serializer_field):
        current = serializer_field
        while hasattr(current, "parent") and current.parent is not None:
            current = current.parent

        instance = current.instance

        self.is_update = instance is not None
        self.user_instance = instance
