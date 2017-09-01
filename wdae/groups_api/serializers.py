from rest_framework import serializers
from django.contrib.auth.models import Group


class GroupListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data):
        print(instance)
        print(validated_data)
        return instance


class GroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(validators=[])

    class Meta:
        model = Group
        fields = ('id', 'name',)
        list_serializer_class = GroupListSerializer
