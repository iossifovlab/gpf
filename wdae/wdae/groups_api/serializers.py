from builtins import object
from rest_framework import serializers
from django.contrib.auth.models import Group
from guardian import shortcuts
from datasets_api.models import Dataset
from users_api.serializers import CreatableSlugRelatedField


class GroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(validators=[])

    class Meta(object):
        model = Group
        fields = ('id', 'name',)


class GroupRetrieveSerializer(GroupSerializer):

    users = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='email', source='user_set')

    datasets = serializers.SerializerMethodField()

    class Meta(object):
        model = Group
        fields = ('id', 'name', 'users', 'datasets')

    def get_datasets(self, group):
        datasets = shortcuts.get_objects_for_group(
            group, 'view', klass=Dataset)
        return [d.dataset_id for d in datasets]


class PermissionChangeSerializer(serializers.Serializer):

    groupName = CreatableSlugRelatedField(
        slug_field='name', queryset=Group.objects.all(), read_only=False
    )

    datasetId = serializers.SlugRelatedField(
        queryset=Dataset.objects.all(),
        # read_only=True,
        slug_field='dataset_id'

    )


class PermissionRevokeSerializer(serializers.Serializer):

    groupId = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    datasetId = serializers.SlugRelatedField(
        queryset=Dataset.objects.all(),
        # read_only=True,
        slug_field='dataset_id'

    )

class GroupUserPermissionSerializer(serializers.Serializer):

    groupId = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    userId = serializers.PrimaryKeyRelatedField(
        queryset=Dataset.objects.all()
    )


class GroupDatasetPermissionSerializer(serializers.Serializer):

    groupId = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    datasetId = serializers.PrimaryKeyRelatedField(
        queryset=Dataset.objects.all(),
    )
