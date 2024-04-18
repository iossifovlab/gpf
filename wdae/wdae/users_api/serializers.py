from collections.abc import Iterable
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework import serializers

from .models import WdaeUser
from .validators import SomeSuperuserLeftValidator


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """
    Try to get and return related field and create it if it does not exist.

    Used for the 'groups' field in the user serializer - if a new group is
    given to a user, it will be created and then attached to the user.
    """

    def to_internal_value(self, data: dict) -> Any:
        try:
            return self.get_queryset().get_or_create(
                **{self.slug_field: data},
            )[0]
        except serializers.ObjectDoesNotExist:
            self.fail("does_not_exist", slug_name=self.slug_field, value=data)
        except (TypeError, ValueError):
            self.fail("invalid")
        return None


class DatasetSerializer(serializers.BaseSerializer):
    """Dataset serializer."""

    def to_representation(self, instance: Any) -> Any:

        return instance

    def to_internal_value(self, data: Any) -> Any:
        """Do nothing, method is for DB objects only."""
        return

    def create(self, validated_data: Any) -> Any:
        """Do nothing, method is for DB objects only."""
        return

    def update(self, instance: Any, validated_data: Any) -> Any:
        """Do nothing, method is for DB objects only."""
        return


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""

    name = serializers.CharField(required=False, allow_blank=True)

    groups = serializers.ListSerializer(
        child=CreatableSlugRelatedField(
            slug_field="name", queryset=Group.objects.all(),
        ),
        validators=[SomeSuperuserLeftValidator()],
        default=[],
    )

    hasPassword = serializers.BooleanField(source="is_active", read_only=True)

    allowedDatasets = serializers.ListSerializer(
        required=False,
        read_only=True,
        source="allowed_datasets",
        child=DatasetSerializer(),
    )

    class Meta:  # pylint: disable=too-few-public-methods
        model = get_user_model()
        fields = (
            "id", "email", "name",
            "hasPassword", "groups", "allowedDatasets")

    def run_validation(self, data: dict) -> Any:  # type: ignore
        # pylint: disable=signature-differs
        """Normalize email before validation."""
        email = data.get("email")
        if email:
            email = get_user_model().objects.normalize_email(email).lower()
            data["email"] = email

        return super().run_validation(data=data)

    def validate(self, attrs: dict) -> Any:
        """Validate that no unknown fields are given."""
        unknown_keys = set(self.initial_data.keys()) - set(self.fields.keys())
        if unknown_keys:
            raise serializers.ValidationError(
                f"Got unknown fields: {unknown_keys}",
            )

        return super().validate(attrs)

    @staticmethod
    def _check_groups_exist(groups: Optional[str]) -> None:
        if groups:
            db_groups_count = Group.objects.filter(name__in=groups).count()
            assert db_groups_count == len(groups), "Not all groups exist."

    @staticmethod
    def _update_groups(user: WdaeUser, new_groups: Iterable[Group]) -> None:
        with transaction.atomic():
            to_remove = set()
            to_remove.update(group.id for group in user.groups.all())

            to_add = set()
            for group in new_groups:
                if group.id in to_remove:
                    to_remove.remove(group.id)
                else:
                    to_add.add(group.id)

            user.groups.add(*to_add)
            user.groups.remove(*to_remove)

    def update(self, instance: WdaeUser, validated_data: dict) -> WdaeUser:
        groups = validated_data.pop("groups", None)

        self._check_groups_exist(groups)

        with transaction.atomic():
            super().update(instance, validated_data)

            if groups is not None:
                db_groups = Group.objects.filter(name__in=groups)
                self._update_groups(instance, db_groups)

        return instance

    def create(self, validated_data: dict) -> Any:
        groups = validated_data.pop("groups", None)
        self._check_groups_exist(groups)

        with transaction.atomic():
            instance = super().create(validated_data)

            if groups:
                db_groups = Group.objects.filter(name__in=groups)
                self._update_groups(instance, db_groups)

        return instance

    def to_representation(self, instance: WdaeUser) -> Any:
        response = super().to_representation(instance)
        response["groups"] = sorted(
            response["groups"],
            key=lambda grp: "" if grp in ["admin", "any_user"] else grp,
        )
        return response


class UserWithoutEmailSerializer(UserSerializer):
    class Meta:  # pylint: disable=too-few-public-methods
        model = get_user_model()
        fields = tuple(x for x in UserSerializer.Meta.fields if x != "email")
