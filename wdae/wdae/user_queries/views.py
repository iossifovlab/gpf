import logging

from query_state_save.models import QueryState
from rest_framework import status, views
from rest_framework.request import Request
from rest_framework.response import Response
from utils.logger import request_logging

from user_queries.models import UserQuery

logger = logging.getLogger(__name__)


class UserQuerySaveView(views.APIView):
    """User query save view."""

    @request_logging(logger)
    def post(self, request: Request) -> Response:
        """Save user query."""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            saved_query = QueryState.objects.get(
                uuid=request.data["query_uuid"],
            )
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except QueryState.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except QueryState.MultipleObjectsReturned:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if "name" not in request.data or (not request.data["name"]):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        UserQuery.objects.create(
            user=request.user,
            query=saved_query,
            name=request.data["name"],
            description=request.data.get("description", ""),
        )

        return Response(
            {"uuid": request.data["query_uuid"]},
            status=status.HTTP_201_CREATED,
        )


class UserQueryCollectView(views.APIView):
    """User query collect view."""

    @request_logging(logger)
    def get(self, request: Request) -> Response:
        """Get user queries."""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        stored_queries = UserQuery.objects.filter(user=request.user)

        return Response(
            {
                "queries": list(
                    map(
                        lambda q: {
                            "query_uuid": q.query.uuid,
                            "name": q.name,
                            "description": q.description,
                            "page": q.query.page,
                        },
                        stored_queries,
                    ),
                ),
            },
            status=status.HTTP_200_OK,
        )
