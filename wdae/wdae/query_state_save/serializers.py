from rest_framework import serializers

from .models import QueryState


class QueryStateSerializer(serializers.ModelSerializer):

    data = serializers.DictField()

    class Meta:
        model = QueryState
        fields = ("data", "page")
