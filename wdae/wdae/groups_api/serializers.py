from builtins import object
from rest_framework import serializers
from django.contrib.auth.models import Group
from datasets_api.permissions import get_dataset_info


class GroupCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(validators=[])

    class Meta(object):
        model = Group
        fields = ("id", "name")

    def create(self, validated_data):
        group = Group.objects.create(name=validated_data["name"])
        return group


class GroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(validators=[])

    class Meta(object):
        model = Group
        fields = ("id", "name")


class GroupRetrieveSerializer(GroupSerializer):
    users = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="email", source="user_set"
    )

    datasets = serializers.SerializerMethodField()

    class Meta(object):
        model = Group
        fields = ("id", "name", "users", "datasets")

    def get_datasets(self, group):
        return [
            get_dataset_info(d.dataset_id) for d in group.dataset_set.all()
        ]
