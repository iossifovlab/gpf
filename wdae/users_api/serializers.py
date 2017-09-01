from rest_framework import serializers
from django.contrib.auth import get_user_model
from groups_api.serializers import GroupSerializer
from django.contrib.auth.models import Group
from django.db import transaction


from users_api.models import WdaeUser


class UserSerializer(serializers.ModelSerializer):

    groups = GroupSerializer(many=True, partial=True)
    researcherId = serializers.CharField(source='researcher_id', required=False,
                                         allow_null=True)

    active = serializers.BooleanField(source='is_active')
    staff = serializers.BooleanField(source='is_staff')
    superuser = serializers.BooleanField(source='is_superuser')
    researcher = serializers.BooleanField(source='is_researcher',
                                          read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'staff', 'superuser', 'active',
                  'groups', 'researcher', 'researcherId')

    @staticmethod
    def _check_groups_exist(groups):
        if groups:
            group_ids = map(lambda x: x['id'], groups)
            db_groups_count = Group.objects.filter(id__in=group_ids).count()
            assert db_groups_count == len(group_ids), 'Not all groups exists..'

    @staticmethod
    def _update_groups(user, new_groups):
        with transaction.atomic():
            to_add = []
            old_ids = set(map(lambda x: x.id, user.groups.all()))

            for group in new_groups:
                if group.id in old_ids:
                    old_ids.remove(group.id)
                else:
                    to_add.append(group.id)

            user.groups.add(*to_add)
            user.groups.remove(*old_ids)

    def update(self, instance, validated_data):
        groups = validated_data.pop('groups', None)
        researcher = validated_data.pop('researcher_id', None)

        self._check_groups_exist(groups)

        with transaction.atomic():
            super(UserSerializer, self).update(instance, validated_data)

            if groups:
                group_ids = map(lambda x: x['id'], groups)
                db_groups = Group.objects.filter(id__in=group_ids).all()
                self._update_groups(instance, db_groups)

            if researcher:
                instance.groups.create(
                    name=WdaeUser.get_group_name_for_researcher_id(researcher))

        return instance

    def create(self, validated_data):
        groups = validated_data.pop('groups', None)
        researcher = validated_data.pop('researcher_id', None)

        self._check_groups_exist(groups)

        with transaction.atomic():
            instance = super(UserSerializer, self).create(validated_data)

            if groups:
                group_ids = map(lambda x: x['id'], groups)
                db_groups = Group.objects.filter(id__in=group_ids).all()
                self._update_groups(instance, db_groups)

            if researcher:
                instance.groups.create(
                    name=WdaeUser.get_group_name_for_researcher_id(researcher))

        return instance
