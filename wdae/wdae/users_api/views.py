import json
import base64
from typing import Optional, cast
import django.contrib.auth
from django import forms
from django.db import IntegrityError, models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.http.response import StreamingHttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.shortcuts import redirect, render
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.decorators import action, api_view, authentication_classes
from rest_framework import status, viewsets, permissions, filters, views
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from oauth2_provider.contrib.rest_framework \
    import OAuth2Authentication  # type: ignore
from oauth2_provider.models import get_application_model  # type: ignore

from utils.logger import log_filter, LOGGER, request_logging, \
    request_logging_function_view
from utils.email_regex import is_email_valid
from utils.password_requirements import is_password_valid
from utils.streaming_response_util import convert
from utils.authentication import GPFOAuth2Authentication

from .models import ResetPasswordCode, SetPasswordCode
from .serializers import UserSerializer, UserWithoutEmailSerializer
from .forms import WdaePasswordForgottenForm, WdaeResetPasswordForm, \
    WdaeRegisterPasswordForm, WdaeLoginForm

from .utils import csrf_clear, get_default_application


def iterator_to_json(users):
    """Wraps an iterator over WdaeUser models to produce json objects
    using the appropriate serializer.
    """
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
        else:
            yield yieldval + ","
        curr = post
        post = next(users, None)
    yield "]"
    return 0


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = get_user_model().objects.order_by("email").all()
    permission_classes = (permissions.IsAdminUser,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("email", "name", "groups__name")

    @request_logging(LOGGER)
    def list(self, request, *args, **kwargs):
        return super().list(request)

    @request_logging(LOGGER)
    def create(self, request, *args, **kwargs):
        return super().create(request)

    @request_logging(LOGGER)
    def retrieve(self, request, *args, pk=None, **kwargs):
        return super().retrieve(request, pk=pk)

    @request_logging(LOGGER)
    def update(self, request, *args, pk=None, **kwargs):
        if (
            request.user.pk == int(pk)
            and request.user.is_staff
            and "admin" not in request.data["groups"]
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, pk=pk, *args, **kwargs)

    @request_logging(LOGGER)
    def partial_update(self, request, pk=None):
        if (
            request.user.pk == int(pk)
            and request.user.is_staff
            and "admin" not in request.data["groups"]
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, pk=pk)

    @request_logging(LOGGER)
    def destroy(self, request, *args, pk=None, **kwargs):
        if request.user.pk == int(pk):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, pk=pk)

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == "update" or self.action == "partial_update":
            serializer_class = UserWithoutEmailSerializer

        return serializer_class

    @request_logging(LOGGER)
    @action(detail=False, methods=["get"])
    def streaming_search(self, request):
        self.check_permissions(request)
        queryset = get_user_model().objects.all()
        search_param = request.GET.get("search", None)
        if search_param:
            queryset = queryset.filter(
                Q(name__icontains=search_param)
                | Q(email__icontains=search_param)
            )
        return StreamingHttpResponse(
            iterator_to_json(queryset.iterator()),
            status=status.HTTP_200_OK,
            content_type="text/event-stream",
        )


class ForgotPassword(views.APIView):
    @request_logging(LOGGER)
    def get(self, request):
        form = WdaePasswordForgottenForm()
        return render(
            request,
            "users_api/registration/forgotten-password.html",
            {"form": form, "show_form": True}
        )

    @request_logging(LOGGER)
    def post(self, request):
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
                    "show_form": True
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        email = form.data["email"]
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
            user.reset_password()
            user.deauthenticate()

            message = (
                f"An e-mail has been sent to {email}"
                " containing the reset link"
            )

            return render(
                request,
                "users_api/registration/forgotten-password.html",
                {
                    "form": form,
                    "message": message,
                    "message_type": "success",
                    "show_form": False
                }
            )
        except user_model.DoesNotExist:
            form = WdaePasswordForgottenForm()
            message = f"There is no user registered for {email}"
            return render(
                request,
                "users_api/registration/forgotten-password.html",
                {
                    "form": form,
                    "message": message,
                    "message_type": "warn",
                    "show_form": True
                },
                status=status.HTTP_404_NOT_FOUND
            )


class BasePasswordView(views.APIView):
    """Base class for set/reset password views."""

    verification_code_model: Optional[models.Model] = None
    template: Optional[str] = None
    form: Optional[forms.Form] = None
    code_type: Optional[str] = None

    def _check_request_verification_path(self, request):
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
            verif_code = self.verification_code_model.objects.get(
                path=verification_path)
        except ObjectDoesNotExist:
            return None, f"Invalid {self.code_type} code"

        is_valid = verif_code.validate()

        if not is_valid:
            return verif_code, f"Expired {self.code_type} code"

        return verif_code, None

    @request_logging(LOGGER)
    def get(self, request):
        verif_code, msg = \
            self._check_request_verification_path(request)

        if msg is not None:
            if verif_code is not None:
                verif_code.delete()
            return render(
                request,
                self.template,
                {"message": msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = verif_code.user

        form = self.form(user)  # pylint: disable=not-callable
        request.session[f"{self.code_type}_code"] = verif_code.path
        request.path = request.path[:request.path.find("?")]
        return render(
            request,
            self.template,
            {"form": form}
        )

    @request_logging(LOGGER)
    def post(self, request):
        verif_code, msg = \
            self._check_request_verification_path(request)

        if msg is not None:
            if verif_code is not None:
                verif_code.delete()
            return render(
                request,
                self.template,
                {"message": msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = verif_code.user
        # pylint: disable=not-callable
        form = self.form(user, data=request.data)
        is_valid = form.is_valid()
        if not is_valid:
            return render(
                request,
                self.template,
                {
                    "form": form
                },
                status=status.HTTP_400_BAD_REQUEST
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


class WdaeLoginView(views.APIView):

    @request_logging(LOGGER)
    def get(self, request):
        next_uri = request.GET.get("next")
        if next_uri is None:
            next_uri = get_default_application().redirect_uris.split(" ")[0]
        form = WdaeLoginForm()

        return render(
            request,
            "users_api/registration/login.html",
            {
                "form": form,
                "next": next_uri
            }
        )

    @request_logging(LOGGER)
    def post(self, request):
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
                "show_errors": True
            },
            status=response_status
        )


@request_logging_function_view(LOGGER)
@api_view(["POST"])
def change_password(request):
    password = request.data["password"]
    verif_code = request.data["verifPath"]

    if not is_password_valid(password):
        LOGGER.error(log_filter(
            request,
            f"Password change failed: Invalid password: '{str(password)}'"
        ))
        return Response(
            {"error_msg": ("Invalid password entered. Password is either too"
                           " short (<10 symbols) or too weak.")},
            status=status.HTTP_400_BAD_REQUEST
        )

    get_user_model().change_password(verif_code, password)
    return Response({}, status.HTTP_201_CREATED)


@request_logging_function_view(LOGGER)
@api_view(["POST"])
def register(request):
    user_model = get_user_model()

    try:
        email = BaseUserManager.normalize_email(request.data["email"])
        if not is_email_valid(email):
            raise ValueError

        if settings.OPEN_REGISTRATION:
            preexisting_user, _ = user_model.objects.get_or_create(email=email)
        else:
            preexisting_user = user_model.objects.get(
                email__iexact=email
            )

        preexisting_user.register_preexisting_user(request.data.get("name"))
        LOGGER.info(
            log_filter(
                request,
                "registration succeded; "
                "email: '" + str(email) + "'",
            )
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except IntegrityError:
        LOGGER.error(
            log_filter(
                request,
                "Registration failed: IntegrityError; "
                "email: '" + str(email) + "'",
            )
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except user_model.DoesNotExist:
        LOGGER.error(
            log_filter(
                request,
                "Registration failed: Email or Researcher Id not found; "
                "email: '" + str(email) + "'",
            )
        )
        return Response(
            {"error_msg": ("Registration is closed."
                           " Please contact an administrator.")},
            status=status.HTTP_403_FORBIDDEN
        )
    except KeyError:
        LOGGER.error(
            log_filter(
                request, "Registration failed: KeyError; " + str(request.data)
            )
        )
        return Response({}, status=status.HTTP_201_CREATED)
    except ValueError:
        LOGGER.error(
            log_filter(
                request,
                f"Registration failed: Invalid email; email: '{str(email)}'"
            )
        )
        return Response(
            {"error_msg": ("Invalid email address entered."
                           " Please use a valid email address.")},
            status=status.HTTP_400_BAD_REQUEST
        )


@request_logging_function_view(LOGGER)
@csrf_clear
@api_view(["POST"])
@authentication_classes((SessionAuthentication,))
def logout(request):
    django.contrib.auth.logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@request_logging_function_view(LOGGER)
@ensure_csrf_cookie
@api_view(["GET"])
@authentication_classes((GPFOAuth2Authentication,))
def get_user_info(request):
    """Get user info for currently logged-in user."""
    user = request.user
    if user.is_authenticated:
        return Response(
            {
                "loggedIn": True,
                "email": user.email,
                "isAdministrator": user.is_staff,
            },
            status.HTTP_200_OK,
        )
    return Response({"loggedIn": False}, status.HTTP_200_OK)


@request_logging_function_view(LOGGER)
@api_view(["POST"])
def check_verif_code(request):
    verif_code = request.data["verifPath"]
    try:
        ResetPasswordCode.objects.get(path=verif_code)
        return Response({}, status=status.HTTP_200_OK)
    except ObjectDoesNotExist:
        return Response(
            {"errors": "Verification path does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@authentication_classes((OAuth2Authentication,))
def get_federation_credentials(request):
    """Create a new federation application and return its credentials."""
    user = request.user

    if not user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    application = get_application_model()
    if application.objects.filter(name=request.GET.get("name")).exists():
        return Response(status=status.HTTP_400_BAD_REQUEST)

    new_application = application(**{
        "name": request.GET.get("name"),
        "user_id": user.id,
        "client_type": "confidential",
        "authorization_grant_type": "client-credentials"
    })

    new_application.full_clean()
    cleartext_secret = new_application.client_secret
    new_application.save()

    credentials = base64.b64encode(
        f"{new_application.client_id}:{cleartext_secret}".encode("utf-8")
    )
    return Response({"credentials": credentials}, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes((OAuth2Authentication,))
def revoke_federation_credentials(request):
    """Delete a given federation app."""
    user = request.user
    if not user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    app = get_application_model().objects.get(name=request.GET.get("name"))
    if not user.id == app.user_id:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    app.delete()
    return Response(status=status.HTTP_200_OK)
