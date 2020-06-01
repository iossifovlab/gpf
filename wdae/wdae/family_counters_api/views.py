import logging

from rest_framework import status
from rest_framework.response import Response

from query_base.query_base import QueryBaseView


LOGGER = logging.getLogger(__name__)


class FamilyCounters(QueryBaseView):
    def __init__(self):
        super(FamilyCounters, self).__init__()

    def post(self, request):
        # TODO Reimplement
        return Response([], status=status.HTTP_200_OK)
