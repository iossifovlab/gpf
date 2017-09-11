from rest_framework import serializers
from django.contrib.auth import get_user_model
from groups_api.serializers import GroupSerializer
from django.contrib.auth.models import Group
from django.db import transaction


from users_api.models import WdaeUser


class UserSerializer(serializers.ModelSerializer):

    name = serializers.CharField(required=False)

    groups = GroupSerializer(many=True, partial=True)

    hasPassword = serializers.BooleanField(source='is_active', read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'name', 'hasPassword', 'groups')

    def validate(self, data):
        unknown_keys = set(self.initial_data.keys()) - set(self.fields.keys())
        if unknown_keys:
            raise serializers.ValidationError(
                "Got unknown fields: {}".format(unknown_keys))
        
        return super(UserSerializer, self).validate(data)

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


class UserWithoutEmailSerializer(UserSerializer):

    class Meta:
        model = get_user_model()
        fields = tuple(x for x in UserSerializer.Meta.fields if x != 'email')
