from rest_framework import serializers
from query_state_save.models import QueryState


class QueryStateSerializer(serializers.ModelSerializer):

    data = serializers.DictField()

    class Meta:
        model = QueryState
        fields = ("data", "page")
