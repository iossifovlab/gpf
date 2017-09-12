from rest_framework import serializers
from django.contrib.auth.models import Group
from guardian import shortcuts
from datasets_api.models import Dataset


class GroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(validators=[])

    class Meta:
        model = Group
        fields = ('id', 'name',)


class GroupRetrieveSerializer(GroupSerializer):

    users = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='email', source='user_set')

    datasets = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'name', 'users', 'datasets')

    def get_datasets(self, group):
        datasets = shortcuts.get_objects_for_group(group, 'view', klass=Dataset)
        # print(datasets)
        # if len(datasets) > 0:
        #     print(type(datasets[0]))

        return map(lambda d: d.dataset_id, datasets)
