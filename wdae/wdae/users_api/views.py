from __future__ import annotations

import base64
import json
import logging
from collections.abc import Generator, Iterator
from typing import Any, Tuple, Type, cast

import django.contrib.auth
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, models
from django.db.models import Q
from django.http.response import (
    HttpResponse,
    HttpResponseRedirect,
    StreamingHttpResponse,
)
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from gpf_instance.gpf_instance import permission_update
from oauth2_provider.models import get_application_model
from rest_framework import filters, permissions, status, views, viewsets
from rest_framework.decorators import action, api_view, authentication_classes
from rest_framework.request import Request
from rest_framework.response import Response
from utils.authentication import (
    GPFOAuth2Authentication,
    SessionAuthenticationWithoutCSRF,
)
from utils.email_regex import is_email_valid
from utils.logger import (
    log_filter,
    request_logging,
    request_logging_function_view,
)
from utils.password_requirements import is_password_valid
from utils.streaming_response_util import convert

from .forms import (
    WdaeLoginForm,
    WdaePasswordForgottenForm,
    WdaeRegisterPasswordForm,
    WdaeResetPasswordForm,
)
from .models import (
    AuthenticationLog,
    GpUserState,
    ResetPasswordCode,
    SetPasswordCode,
    WdaeUser,
    csrf_clear,
    get_default_application,
)
from .serializers import UserSerializer, UserWithoutEmailSerializer

logger = logging.getLogger(__name__)


def iterator_to_json(users: Iterator[WdaeUser]) -> Generator[str, None, int]:
    """Wrap an iterator over WdaeUser models to produce json objects."""
    yield "["
    curr = next(users, None)
    post = next(users, None)
    while curr is not None:
        if curr.email:
            serializer = UserSerializer
        else:
            serializer = UserWithoutEmailSerializer
        yieldval = json.dumps(serializer(curr).data, default=convert)
        if post is None:
            yield yieldval
            break
        yield yieldval + ","

        curr = post
        post = next(users, None)
    yield "]"
    return 0


class UserViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API endpoint that allows users to be viewed or edited."""

    authentication_classes = [
        SessionAuthenticationWithoutCSRF, GPFOAuth2Authentication]
    serializer_class = UserSerializer
    queryset = get_user_model().objects.order_by("email").all()
    permission_classes = (permissions.IsAdminUser,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("email", "name", "groups__name")

    @request_logging(logger)
    def list(
        self, request: Request,
        *args: Any, **kwargs: Any,
    ) -> Response:
        return super().list(request)

    @request_logging(logger)
    @permission_update
    def create(
        self, request: Request,
        *args: Any, **kwargs: Any,
    ) -> Response:
        response = super().create(request)
        return response

    @request_logging(logger)
    def retrieve(
        self, request: Request,
        *args: Any, pk: int | None = None, **kwargs: Any,
    ) -> Response:
        if pk is not None:
            pk = int(pk)
        return super().retrieve(request, pk=pk)

    @request_logging(logger)
    @permission_update
    def update(
        self, request: Request,
        *args: Any, pk: int | None = None, **kwargs: Any,
    ) -> Response:
        if pk is not None:
            pk = int(pk)
        if (
            request.user.pk == pk
            and request.user.is_staff
            and "admin" not in request.data["groups"]
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, pk=pk, *args, **kwargs)

    @request_logging(logger)
    @permission_update
    def partial_update(
        self, request: Request,
        *args: Any, pk: int | None = None, **kwargs: Any,
    ) -> Response:
        if pk is not None:
            pk = int(pk)
        if (
            request.user.pk == pk
            and request.user.is_staff
            and "admin" not in request.data["groups"]
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, pk=pk)

    @request_logging(logger)
    @permission_update
    def destroy(
        self, request: Request,
        *args: Any, pk: int | None = None, **kwargs: Any,
    ) -> Response:
        if pk is not None:
            pk = int(pk)
        if request.user.pk == pk:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, pk=pk)

    def get_serializer_class(
        self,
    ) -> Type[UserWithoutEmailSerializer] | Type[UserSerializer]:
        serializer_class = self.serializer_class

        if self.action in {"update", "partial_update"}:
            serializer_class = UserWithoutEmailSerializer

        return serializer_class

    @request_logging(logger)
    @action(detail=False, methods=["get"])
    def streaming_search(self, request: Request) -> StreamingHttpResponse:
        """Search for users and stream the results."""
        self.check_permissions(request)
        queryset = get_user_model().objects.all()
        search_param = request.GET.get("search", None)
        if search_param:
            queryset = queryset.filter(
                Q(name__icontains=search_param)
                | Q(email__icontains=search_param),
            )
        return StreamingHttpResponse(
            iterator_to_json(queryset.iterator()),
            status=status.HTTP_200_OK,
            content_type="text/event-stream",
        )

    @request_logging(logger)
    @action(detail=True, methods=["get", "post"])
    def password_reset(self, request: Request, pk: int) -> Response:
        """Reset the password for a user."""
        self.check_permissions(request)
        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=pk)
            user.reset_password()
            user.deauthenticate()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except user_model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ForgotPassword(views.APIView):
    """View for forgotten password."""

    @request_logging(logger)
    def get(self, request: Request) -> HttpResponse:
        form = WdaePasswordForgottenForm()
        return render(
            request,
            "users_api/registration/forgotten-password.html",
            {"form": form, "show_form": True},
        )

    @request_logging(logger)
    def post(self, request: Request) -> HttpResponse:
        """Send a reset password email to the user."""
        form = WdaePasswordForgottenForm(request.data)
        is_valid = form.is_valid()
        if not is_valid:
            return render(
                request,
                "users_api/registration/forgotten-password.html",
                {
                    "form": form,
                    "message": "Invalid email",
                    "message_type": "warn",
                    "show_form": True,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = form.data["email"]
        user_model = get_user_model()
        message = (
            f"An e-mail has been sent to {email}"
            " containing the reset link"
        )
        try:
            user = user_model.objects.get(email=email)
            user.reset_password()
            user.deauthenticate()

            return render(
                request,
                "users_api/registration/forgotten-password.html",
                {
                    "form": form,
                    "message": message,
                    "message_type": "success",
                    "show_form": False,
                },
            )
        except user_model.DoesNotExist:
            return render(
                request,
                "users_api/registration/forgotten-password.html",
                {
                    "form": form,
                    "message": message,
                    "message_type": "success",
                    "show_form": False,
                },
            )


class BasePasswordView(views.APIView):
    """Base class for set/reset password views."""

    verification_code_model: models.Model | None = None
    template: str | None = None
    form: forms.Form | None = None
    code_type: str | None = None

    def _check_request_verification_path(
        self, request: Request,
    ) -> Tuple[ResetPasswordCode | None | SetPasswordCode, str | None]:
        """
        Check, validate and return a verification path from a request.

        Returns a tuple of the model instance and the error message if any.
        When the instance is not found, None is returned.
        """
        verification_path = request.GET.get("code")
        if verification_path is None:
            verification_path = request.session.get(f"{self.code_type}_code")
        if verification_path is None:
            return None, f"No {self.code_type} code provided"
        try:
            assert verification_path is not None
            assert self.verification_code_model is not None
            verif_code = \
                self.verification_code_model.objects.get(  # type: ignore
                    path=verification_path)
        except ObjectDoesNotExist:
            return None, f"Invalid {self.code_type} code"

        is_valid = verif_code.validate()

        if not is_valid:
            return verif_code, f"Expired {self.code_type} code"

        return verif_code, None

    @request_logging(logger)
    def get(self, request: Request) -> HttpResponse:
        """Render the password reset form."""
        verif_code, msg = \
            self._check_request_verification_path(request)

        if msg is not None:
            if verif_code is not None:
                verif_code.delete()
            assert self.template is not None
            return render(
                request,
                self.template,
                {"message": msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assert verif_code is not None
        user = verif_code.user

        assert self.form is not None
        # pylint: disable=not-callable
        form = self.form(user)  # type: ignore
        request.session[f"{self.code_type}_code"] = verif_code.path
        request.path = request.path[:request.path.find("?")]
        assert self.template is not None
        return render(
            request,
            self.template,
            {"form": form},
        )

    @request_logging(logger)
    def post(self, request: Request) -> HttpResponse:
        """Handle the password reset form."""
        verif_code, msg = \
            self._check_request_verification_path(request)
        assert self.template is not None
        if msg is not None:
            if verif_code is not None:
                verif_code.delete()
            return render(
                request,
                self.template,
                {"message": msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assert verif_code is not None
        user = verif_code.user
        # pylint: disable=not-callable
        form = self.form(user, data=request.data)  # type: ignore
        is_valid = form.is_valid()
        if not is_valid:
            return render(
                request,
                self.template,
                {
                    "form": form,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = form.cleaned_data["new_password1"]
        user.change_password(verif_code, new_password)
        del request.session[f"{self.code_type}_code"]
        application = get_default_application()
        redirect_uri = application.redirect_uris.split(" ")[0]
        return HttpResponseRedirect(redirect_uri)


class ResetPassword(BasePasswordView):
    verification_code_model = cast(models.Model, ResetPasswordCode)
    template = "users_api/registration/reset-password.html"
    form = cast(forms.Form, WdaeResetPasswordForm)
    code_type = "reset"


class SetPassword(BasePasswordView):
    verification_code_model = cast(models.Model, SetPasswordCode)
    template = "users_api/registration/set-password.html"
    form = cast(forms.Form, WdaeRegisterPasswordForm)
    code_type = "set"


class RESTLoginView(views.APIView):
    """View for REST session bases logging in."""

    @request_logging(logger)
    def post(self, request: Request) -> Response:
        """Supports a REST login endpoint."""
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            username=username, password=password,
        )
        if user is None:
            AuthenticationLog.log_authentication_attempt(
                username, failed=True,
            )
            if AuthenticationLog.is_user_locked_out(username):
                return Response(
                    AuthenticationLog.get_locked_out_error(username),
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        logger.info(log_filter(request, "login success: " + str(username)))
        AuthenticationLog.log_authentication_attempt(username, failed=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WdaeLoginView(views.APIView):
    """View for logging in."""

    @request_logging(logger)
    def get(self, request: Request) -> HttpResponse:
        """Render the login form."""
        next_uri = request.GET.get("next")
        if next_uri is None:
            next_uri = get_default_application().redirect_uris.split(" ")[0]
        form = WdaeLoginForm()

        return render(
            request,
            "users_api/registration/login.html",
            {
                "form": form,
                "next": next_uri,
            },
        )

    @request_logging(logger)
    def post(self, request: Request) -> Response | HttpResponse:
        """Handle the login form."""
        data = request.data
        next_uri = data.get("next")
        if next_uri is None:
            next_uri = get_default_application().redirect_uris.split(" ")[0]

        response_status = status.HTTP_200_OK
        form = WdaeLoginForm(request, data=data)

        if form.is_valid():
            return redirect(next_uri)
        response_status = form.status_code

        return render(
            request,
            "users_api/registration/login.html",
            {
                "form": form,
                "next": next_uri,
                "show_errors": True,
            },
            status=response_status,
        )


@request_logging_function_view(logger)
@api_view(["POST"])
def change_password(request: Request) -> Response:
    """Change the password for a user."""
    password = request.data["password"]
    verif_code = request.data["verifPath"]

    if not is_password_valid(password):
        logger.error(log_filter(
            request,
            "Password change failed: Invalid password: '%s'",
            str(password),
        ))
        return Response(
            {"error_msg": ("Invalid password entered. Password is either too"
                           " short (<10 symbols) or too weak.")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    get_user_model().change_password(verif_code, password)
    return Response({}, status.HTTP_201_CREATED)


@request_logging_function_view(logger)
@api_view(["POST"])
def register(request: Request) -> Response:
    """Register a new user."""
    user_model = get_user_model()

    try:
        email = BaseUserManager.normalize_email(request.data["email"])
        if not is_email_valid(email):
            raise ValueError

        if settings.OPEN_REGISTRATION:
            preexisting_user, _ = user_model.objects.get_or_create(email=email)
        else:
            preexisting_user = user_model.objects.get(
                email__iexact=email,
            )

        preexisting_user.register_preexisting_user(request.data.get("name"))
        logger.info(
            log_filter(
                request,
                "registration succeeded; email: '%s'",
                str(email),
            ),
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except IntegrityError:
        logger.error(
            log_filter(
                request,
                "Registration failed: IntegrityError; email: '%s'",
                str(email),
            ),
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except user_model.DoesNotExist:
        logger.error(
            log_filter(
                request,
                "Registration failed: Email or Researcher Id not found; "
                "email: '%s'",
                str(email),
            ),
        )
        return Response(
            {"error_msg": ("Registration is closed."
                           " Please contact an administrator.")},
            status=status.HTTP_403_FORBIDDEN,
        )
    except KeyError:
        logger.error(
            log_filter(
                request,
                "Registration failed: KeyError; %s",
                str(request.data),
            ),
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except ValueError:
        logger.error(
            log_filter(
                request,
                "Registration failed: Invalid email; email: '%s'",
                str(email),
            ),
        )
        return Response(
            {"error_msg": ("Invalid email address entered."
                           " Please use a valid email address.")},
            status=status.HTTP_400_BAD_REQUEST,
        )


@request_logging_function_view(logger)
@csrf_clear
@api_view(["POST"])
@authentication_classes(
    (GPFOAuth2Authentication, SessionAuthenticationWithoutCSRF))
def logout(request: Request) -> Response:
    """Log out the currently logged-in user."""
    django.contrib.auth.logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@request_logging_function_view(logger)
@ensure_csrf_cookie
@api_view(["GET"])
@authentication_classes(
    (GPFOAuth2Authentication, ))
def get_user_info(request: Request) -> Response:
    """Get user info for currently logged-in user."""
    user = request.user
    if user.is_authenticated:
        return Response(
            {
                "loggedIn": True,
                "email": user.email,
                "isAdministrator":
                    settings.DISABLE_PERMISSIONS or user.is_staff,
            },
            status.HTTP_200_OK,
        )
    return Response(
        {
            "loggedIn": False,
            "email": None,
            "isAdministrator": settings.DISABLE_PERMISSIONS,
        },
        status.HTTP_200_OK,
    )


@request_logging_function_view(logger)
@api_view(["POST"])
def check_verif_code(request: Request) -> Response:
    """Check if a verification code is valid."""
    verif_code = request.data["verifPath"]
    try:
        ResetPasswordCode.objects.get(path=verif_code)
        return Response({}, status=status.HTTP_200_OK)
    except ObjectDoesNotExist:
        return Response(
            {"errors": "Verification path does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class FederationCredentials(views.APIView):
    """API for handling federation credentials/applications."""

    authentication_classes = (GPFOAuth2Authentication,)

    @request_logging(logger)
    def get(self, request: Request) -> Response:
        """List all federation apps for a user."""
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        apps = get_application_model().objects.filter(
            user_id=user.id,
            authorization_grant_type="client-credentials",
            client_type="confidential",
        )
        res = []
        for app in apps:
            res.append({
                "name": app.name,
            })
        return Response(res, status=status.HTTP_200_OK)

    @request_logging(logger)
    def post(self, request: Request) -> Response:
        """Create a new federation application and return its credentials."""
        user = request.user

        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        application = get_application_model()
        if application.objects.filter(name=request.data["name"]).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        new_application = application(name=request.data["name"], user_id=user.id, client_type="confidential", authorization_grant_type="client-credentials")

        new_application.full_clean()
        cleartext_secret = new_application.client_secret
        new_application.save()

        credentials = base64.b64encode(
            f"{new_application.client_id}:{cleartext_secret}".encode(),
        )
        return Response(
            {"credentials": credentials,
             "client_secret": cleartext_secret,
             "client_id": new_application.client_id},
            status=status.HTTP_200_OK,
        )

    @request_logging(logger)
    def delete(self, request: Request) -> Response:
        """Delete a given federation app."""
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if not get_application_model() \
                .objects \
                .filter(name=request.data["name"]) \
                .exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        app = get_application_model().objects.get(
            name=request.data["name"],
        )
        if user.id != app.user_id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        app.delete()
        return Response(status=status.HTTP_200_OK)

    @request_logging(logger)
    def put(self, request: Request) -> Response:
        """Update a given federation token's name."""
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if "name" not in request.data or \
                "new_name" not in request.data or \
                request.data["name"] is None or \
                request.data["new_name"] is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not get_application_model() \
                .objects \
                .filter(name=request.data["name"]) \
                .exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if get_application_model() \
                .objects \
                .filter(name=request.data["new_name"]) \
                .exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        app = get_application_model().objects.get(
            name=request.data["name"],
        )
        if user.id != app.user_id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        app.name = request.data["new_name"]
        app.save()
        return Response(
            {"new_name": app.name},
            status=status.HTTP_200_OK,
        )


class UserGpStateView(views.APIView):
    """User's gene profiles state view."""

    @request_logging(logger)
    def get(self, request: Request) -> Response:
        """Get user's ggene profiles state."""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            gp_state = GpUserState.objects.get(user=request.user)
            res = Response(
                json.loads(gp_state.data),
                status=status.HTTP_200_OK,
            )
        except GpUserState.DoesNotExist:
            res = Response(
                status=status.HTTP_204_NO_CONTENT,
            )

        return res

    @request_logging(logger)
    def post(self, request: Request) -> Response:
        """Save user's gene profiles state."""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        state, _ = GpUserState.objects.get_or_create(
            user=request.user,
        )

        new_state = json.dumps(request.data)

        state.data = new_state
        state.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
