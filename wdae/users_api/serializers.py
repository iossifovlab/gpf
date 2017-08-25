from rest_framework import serializers
from django.contrib.auth import get_user_model
from groups_api.serializers import GroupSerializer


class UserSerializer(serializers.ModelSerializer):

    groups = GroupSerializer(many=True, read_only=True)
    researcherId = serializers.CharField(source='researcher_id', required=False)

    active = serializers.BooleanField(source='is_active')
    staff = serializers.BooleanField(source='is_staff')
    superuser = serializers.BooleanField(source='is_superuser')
    researcher = serializers.BooleanField(source='is_researcher',
                                          read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'staff', 'superuser', 'active',
                  'groups', 'researcher', 'researcherId')
