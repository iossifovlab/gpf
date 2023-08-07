from django import forms
from django.contrib.auth.forms import SetPasswordForm, UsernameField
from django.contrib.auth import password_validation, get_user_model, \
    authenticate, login
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext_lazy
from django.utils.text import capfirst
from utils.password_requirements import is_password_valid
from users_api.models import AuthenticationLog
from rest_framework import status


class WdaeResetPasswordForm(SetPasswordForm):
    """A form for users to reset their password when forgotten."""

    error_messages = {
        "password_invalid": gettext_lazy(
            "Your password is either too short "
            "(less than 10 symbols) or too weak."
        ),
        "password_mismatch": gettext_lazy(
            "The two passwords do not match."
        ),
    }

    def clean_new_password2(self):
        password2 = super().clean_new_password2()
        if not is_password_valid(password2):
            raise ValidationError(
                self.error_messages["password_invalid"],
                code="password_invalid"
            )


class WdaeRegisterPasswordForm(WdaeResetPasswordForm):
    """A form for users to set their password when registered in the system."""

    new_password1 = forms.CharField(
        label=gettext_lazy("Password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=gettext_lazy("Password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )


class WdaeLoginForm(forms.Form):

    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True, "tabindex": 1}))
    password = forms.CharField(
        label=gettext_lazy("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "tabindex": 2}),
    )

    error_messages = {
        "invalid_credentials": gettext_lazy(
            "Invalid login credentials."
        ),
        "no_password": gettext_lazy(
            "Password not provided."
        ),
        "inactive": gettext_lazy(
            "User is inactive."
        ),
        "no_user": gettext_lazy(
            "User not found."
        ),
        "no_username": gettext_lazy(
            "Username not provided."
        )
    }

    def __init__(self, request=None, **kwargs):
        self.request = request
        super().__init__(**kwargs)

        # Set the max length and label for the "username" field.
        user_model = get_user_model()
        self.username_field = \
            user_model._meta.get_field(user_model.USERNAME_FIELD)
        username_max_length = self.username_field.max_length or 254
        self.fields["username"].max_length = username_max_length
        self.fields["username"].widget.attrs["maxlength"] = username_max_length
        if self.fields["username"].label is None:
            self.fields["username"].label = capfirst(
                self.username_field.verbose_name)

        self.status_code = None
        self.user_cache = None

    def confirm_login_allowed(self, user):
        if AuthenticationLog.is_user_locked_out(user.email):
            self.status_code = status.HTTP_403_FORBIDDEN
            raise AuthenticationLog.get_locked_out_error(user.email)
        if not user.is_active:
            self.status_code = status.HTTP_403_FORBIDDEN
            raise ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )

    def clean(self):
        username = self.cleaned_data.get("username")
        user_model = get_user_model()

        if username is None or username == "":
            self.status_code = status.HTTP_400_BAD_REQUEST
            raise ValidationError(
                self.error_messages["no_username"],
                code="no_username"
            )
        try:
            self.user_cache = user_model.objects.get(
                email__iexact=username
            )
        except ObjectDoesNotExist:
            self.status_code = status.HTTP_404_NOT_FOUND
            raise ValidationError(
                self.error_messages["no_user"],
                code="no_user"
            ) from None

        self.confirm_login_allowed(self.user_cache)

        password = self.cleaned_data.get("password")

        if password is None or password == "":
            self.status_code = status.HTTP_400_BAD_REQUEST
            raise ValidationError(
                self.error_messages["no_password"],
                code="no_password"
            )

        username = self.user_cache.email

        self.user_cache = authenticate(
            self.request, username=username, password=password
        )

        if self.user_cache is None:
            AuthenticationLog.log_authentication_attempt(
                username, failed=True
            )
            if AuthenticationLog.is_user_locked_out(username):
                self.status_code = status.HTTP_403_FORBIDDEN
                raise AuthenticationLog.get_locked_out_error(username)
            self.status_code = status.HTTP_401_UNAUTHORIZED
            raise ValidationError(
                self.error_messages["invalid_credentials"],
                code="invalid_credentials"
            )

        login(self.request, self.user_cache)

        AuthenticationLog.log_authentication_attempt(username, failed=False)

        return self.cleaned_data

    def get_status_code(self):
        if self.is_valid():
            return status.HTTP_200_OK

        assert self.status_code is not None

        return self.status_code


class WdaePasswordForgottenForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
