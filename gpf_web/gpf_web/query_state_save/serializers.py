from rest_framework import serializers

from .models import QueryState


class QueryStateSerializer(serializers.ModelSerializer):
    """Serializer for query state save/load."""

    data = serializers.DictField()  # pyright: ignore

    class Meta:
        # pylint: disable=too-few-public-methods
        model = QueryState
        fields = ("data", "page", "origin")
