from typing import cast

from rest_framework import serializers
from django.contrib.auth.models import Group
from datasets_api.permissions import get_dataset_info


class GroupCreateSerializer(serializers.ModelSerializer):
    """Serializer used for group creation."""

    name = serializers.CharField(validators=[])

    class Meta:  # pylint: disable=too-few-public-methods
        model = Group
        fields = ("id", "name")

    def create(self, validated_data: dict[str, str]) -> Group:
        group = Group.objects.create(name=validated_data["name"])
        return group


class GroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(validators=[])

    class Meta:  # pylint: disable=too-few-public-methods
        model = Group
        fields = ("id", "name")


class GroupRetrieveSerializer(GroupSerializer):
    """Serializer used for group listing."""

    users = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="email", source="user_set"
    )

    datasets = serializers.SerializerMethodField()

    class Meta:  # pylint: disable=too-few-public-methods
        model = Group
        fields = ("id", "name", "users", "datasets")

    def get_datasets(self, group: Group) -> list[dict]:
        return sorted(filter(None, [
            get_dataset_info(d.dataset_id) for d in group.dataset_set.all()
        ]), key=lambda d: d["datasetName"].lower())

    def to_representation(self, instance: Group) -> dict:
        response = super().to_representation(instance)
        response["users"] = sorted(response["users"])
        return cast(dict, response)
