from __future__ import unicode_literals
from builtins import object
from rest_framework import serializers
from query_state_save.models import QueryState


class QueryStateSerializer(serializers.ModelSerializer):

    data = serializers.DictField()

    class Meta(object):
        model = QueryState
        fields = ("data", "page")
