from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from .models import WdaeUser


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


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """Tries to get related field and creates it if it does not exist.
    Used for the 'groups' field in the user serializer - if a new group is
    given to a user, it will be created and then attached to the user.
    """
    def to_internal_value(self, data):
        try:
            return self.get_queryset().get_or_create(
                **{self.slug_field: data}
            )[0]
        except serializers.ObjectDoesNotExist:
            self.fail("does_not_exist", slug_name=self.slug_field, value=data)
        except (TypeError, ValueError):
            self.fail("invalid")


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    groups = serializers.ListSerializer(
        child=CreatableSlugRelatedField(
            slug_field="name", queryset=Group.objects.all()
        ),
        validators=[SomeSuperuserLeftValidator()],
        default=[],
    )
    hasPassword = serializers.BooleanField(source="is_active", read_only=True)
    allowedDatasets = serializers.ListSerializer(
        required=False,
        read_only=True,
        source="allowed_datasets",
        child=serializers.CharField()
    )

    class Meta(object):
        model = get_user_model()
        fields = (
            "id", "email", "name", "hasPassword", "groups", "allowedDatasets"
        )

    @staticmethod
    def _check_groups_exist(groups):
        if groups:
            db_groups_count = Group.objects.filter(name__in=groups).count()
            assert db_groups_count == len(groups), "Not all groups exist!"

    @staticmethod
    def _update_groups(user, new_groups):
        with transaction.atomic():
            to_remove = set()
            for group in user.groups.all():
                to_remove.add(group.id)

            to_add = set()
            for group in new_groups:
                if group.id in to_remove:
                    to_remove.remove(group.id)
                else:
                    to_add.add(group.id)

            user.groups.add(*to_add)
            user.groups.remove(*to_remove)

    def update(self, instance, validated_data):
        groups = validated_data.pop("groups", None)
        self._check_groups_exist(groups)

        with transaction.atomic():
            super(UserSerializer, self).update(instance, validated_data)
            if groups:
                db_groups = Group.objects.filter(name__in=groups)
                self._update_groups(instance, db_groups)

        return instance

    def create(self, validated_data):
        groups = validated_data.pop("groups", None)
        self._check_groups_exist(groups)

        with transaction.atomic():
            instance = super(UserSerializer, self).create(validated_data)
            if groups:
                db_groups = Group.objects.filter(name__in=groups)
                self._update_groups(instance, db_groups)

        return instance


class UserWithoutEmailSerializer(UserSerializer):
    class Meta(object):
        model = get_user_model()
        fields = tuple(x for x in UserSerializer.Meta.fields if x != "email")
