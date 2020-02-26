from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from .validators import ProtectedGroupsValidator
from .validators import SomeSuperuserLeftValidator


class CreatableSlugRelatedField(serializers.SlugRelatedField):

    def to_internal_value(self, data):
        try:
            return self.get_queryset() \
                .get_or_create(**{self.slug_field: data})[0]
        except serializers.ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=data)
        except (TypeError, ValueError):
            self.fail('invalid')


class UserSerializer(serializers.ModelSerializer):

    name = serializers.CharField(required=False, allow_blank=True)

    groups = serializers.ListSerializer(
        child=CreatableSlugRelatedField(
            slug_field='name', queryset=Group.objects.all()),
        validators=[ProtectedGroupsValidator(), SomeSuperuserLeftValidator()],
        default=[])

    hasPassword = serializers.BooleanField(source='is_active', read_only=True)

    class Meta(object):
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
            db_groups_count = Group.objects.filter(name__in=groups).count()
            assert db_groups_count == len(groups), 'Not all groups exists..'

    @staticmethod
    def _update_groups(user, new_groups):
        with transaction.atomic():
            to_add = []
            old_ids = set([x.id for x in user.groups.all()])

            for group in new_groups:
                if group.id in old_ids:
                    old_ids.remove(group.id)
                else:
                    to_add.append(group.id)

            user.groups.add(*to_add)
            user.groups.remove(*old_ids)

    def update(self, instance, validated_data):
        groups = validated_data.pop('groups', None)

        self._check_groups_exist(groups)

        with transaction.atomic():
            super(UserSerializer, self).update(instance, validated_data)

            if groups:
                db_groups = Group.objects.filter(name__in=groups)
                self._update_groups(instance, db_groups)

        return instance

    def create(self, validated_data):
        groups = validated_data.pop('groups', None)

        self._check_groups_exist(groups)

        with transaction.atomic():
            instance = super(UserSerializer, self).create(validated_data)

            if groups:
                db_groups = Group.objects.filter(name__in=groups)
                self._update_groups(instance, db_groups)

        return instance


class UserWithoutEmailSerializer(UserSerializer):

    class Meta(object):
        model = get_user_model()
        fields = tuple(x for x in UserSerializer.Meta.fields if x != 'email')


class BulkGroupOperationSerializer(serializers.Serializer):

    userIds = serializers.ListSerializer(child=serializers.IntegerField())
    group = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError()

    def to_representation(self, instance):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()

    def to_internal_value(self, data):
        return super(BulkGroupOperationSerializer, self).\
            to_internal_value(data)
