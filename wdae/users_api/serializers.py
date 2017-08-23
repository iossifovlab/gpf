from rest_framework import serializers
from django.contrib.auth import get_user_model
from groups_api.serializers import GroupSerializer


class UserSerializer(serializers.ModelSerializer):

    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'is_staff', 'is_superuser', 'is_active',
                  'groups')
