from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Type, cast

from datasets_api.permissions import get_directly_allowed_genotype_data
from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    PermissionsMixin,
    User,
)
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models.signals import m2m_changed, post_delete, pre_delete
from django.utils import timezone
from oauth2_provider.models import Application, get_application_model

logger = logging.getLogger(__name__)


class WdaeUserManager(BaseUserManager):
    """User manager for wdae users."""

    def _create_user(
        self, email: str, password: str | None, **kwargs: Any,
    ) -> WdaeUser:
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")

        email = self.normalize_email(email)
        email = email.lower()

        user = cast(WdaeUser, self.model(email=email, **kwargs))
        user.set_password(password)

        user.save(using=self._db)

        return user

    def get_or_create(  # type: ignore
        self, **kwargs: Any,
    ) -> tuple[WdaeUser, bool]:
        try:
            return cast(WdaeUser, self.get(**kwargs)), False
        except WdaeUser.DoesNotExist:  # pylint: disable=no-member
            return self.create_user(**kwargs), True

    def create(self, **kwargs: Any) -> WdaeUser:  # type: ignore
        return self.create_user(**kwargs)

    def create_user(
        self, email: str, password: str | None = None,
        **kwargs: Any,
    ) -> WdaeUser:
        user = self._create_user(email, password, **kwargs)
        return user

    def create_superuser(
        self, email: str, password: str,
        **kwargs: Any,
    ) -> WdaeUser:
        """Create and save a superuser."""
        user = self._create_user(email, password, **kwargs)

        user.is_superuser = True
        user.is_active = True
        user.is_staff = True

        user.save()

        return user


class WdaeUser(AbstractBaseUser, PermissionsMixin):
    """Class representing a user in wdae."""

    name: models.CharField = models.CharField(max_length=100)
    email: models.EmailField = models.EmailField(unique=True)

    is_staff: models.BooleanField = models.BooleanField(default=False)
    is_active: models.BooleanField = models.BooleanField(default=False)
    date_joined: models.DateTimeField = models.DateTimeField(null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    SUPERUSER_GROUP = "admin"
    UMLIMITED_DOWNLOAD_GROUP = "unlimited"

    objects = WdaeUserManager()

    @property
    def has_unlimited_download(self) -> bool:
        return self.groups.filter(  # pylint: disable=no-member
            name=self.UMLIMITED_DOWNLOAD_GROUP).count() > 0

    @property
    def allowed_datasets(self) -> list[dict[str, Any]]:
        return get_directly_allowed_genotype_data(cast(User, self))

    def email_user(
        self, subject: str, message: str,
        from_email: str | None = None,
    ) -> int:
        """Send an email to the user."""
        # pylint: disable=import-outside-toplevel
        from django.conf import settings

        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL  # type: ignore

        override = None
        try:
            override = settings.EMAIL_OVERRIDE  # type: ignore
        except Exception:  # pylint: disable=broad-exception-caught
            logger.debug("no email override; sending email")
            override = None
        if override:
            to_email = override
        else:
            to_email = self.email

        mail = send_mail(subject, message, from_email, [to_email])
        logger.info("email sent: to:      <%s>", str(self.email))
        logger.info("email sent: from:    <%s>", str(from_email))
        logger.info("email sent: subject:  %s", str(subject))
        logger.info("email sent: message:  %s", str(message))

        return mail

    def set_password(self, raw_password: str | None) -> None:
        super().set_password(raw_password)

        has_password = bool(raw_password)
        if self.is_active != has_password:
            self.is_active = has_password

    def set_unusable_password(self) -> None:
        super().set_unusable_password()

        if self.is_active:
            self.is_active = False

    def reset_password(self, by_admin: bool = False) -> None:
        verif_code = ResetPasswordCode.create(self)
        send_reset_email(self, verif_code, by_admin)

    def deauthenticate(self) -> None:
        all_sessions = Session.objects.all()
        for session in all_sessions:
            session_data = session.get_decoded()
            if self.pk == session_data.get("_auth_user_id"):
                session.delete()

    def register_preexisting_user(self, name: str | None) -> None:
        """Register already existing user."""
        if self.is_active:
            send_already_existing_email(self)
        else:
            self.date_joined = timezone.now()
            if name is not None and name != "":
                self.name = name

            verif_code = SetPasswordCode.create(self)
            send_verif_email(self, verif_code)

            self.save()

    @staticmethod
    def change_password(
        verification_path: SetPasswordCode | ResetPasswordCode,
        new_password: str,
    ) -> WdaeUser:
        """Initiate password reset for the user."""
        user = verification_path.user
        user.set_password(new_password)
        user.save()

        # Reset account lockout
        AuthenticationLog(
            email=user.email,
            time=timezone.now(),
            failed_attempt=0,
        ).save()

        verification_path.delete()

        return cast(WdaeUser, user)

    def __str__(self) -> str:
        return str(self.email)

    class Meta:  # pylint: disable=too-few-public-methods
        db_table = "users"


class BaseVerificationCode(models.Model):
    """Base class for temporary codes for verifying the user without login."""

    path: models.Field = models.CharField(max_length=255, unique=True)
    user: models.Field = models.OneToOneField(
        WdaeUser, on_delete=models.CASCADE)
    created_at: models.Field = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.path)

    def validate(self) -> bool:
        raise NotImplementedError

    class Meta:  # pylint: disable=too-few-public-methods
        abstract = True

    @classmethod
    def get_code(
        cls, user: WdaeUser,
    ) -> BaseVerificationCode | None:
        """Get a verification code for a user."""
        try:
            # pylint: disable=no-member
            return cast(
                BaseVerificationCode,
                cls.objects.get(user=user))  # type: ignore
        except ObjectDoesNotExist:
            return None

    @classmethod
    def create(cls, user: WdaeUser) -> BaseVerificationCode:
        """Create an email verification code."""
        try:
            # pylint: disable=no-member
            verif_code = cls.objects.get(user=user)  # type: ignore
        except ObjectDoesNotExist:
            # pylint: disable=no-member
            verif_code = cls.objects.create(  # type: ignore
                user=user, path=uuid.uuid4())
            return cast(BaseVerificationCode, verif_code)

        if verif_code.validate is not True:
            verif_code.delete()
            return cls.create(user)

        return cast(BaseVerificationCode, verif_code)


class GpUserState(models.Model):
    """Class representing a user's gene profiles state."""
    user: models.OneToOneField = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE)
    data: models.TextField = models.TextField(
        null=False, blank=False)


class SetPasswordCode(BaseVerificationCode):
    """Base class for temporary paths for verifying user without login."""

    class Meta:  # pylint: disable=too-few-public-methods
        db_table = "set_password_verification_codes"

    def validate(self) -> bool:
        return True


class ResetPasswordCode(BaseVerificationCode):
    """Class used for verification of password resets."""

    class Meta:  # pylint: disable=too-few-public-methods
        db_table = "reset_password_verification_codes"

    def validate(self) -> bool:
        # pylint: disable=import-outside-toplevel
        from django.conf import settings
        max_delta = timedelta(
            hours=getattr(settings, "RESET_PASSWORD_TIMEOUT_HOURS", 24))
        if timezone.now() - self.created_at > max_delta:
            return False
        return True


class AuthenticationLog(models.Model):
    """A model to keep track of all requests for authentication.

    Which email was used, when they were
    made and what number of consecutive failed attempts have
    been made on this email. The failed attempt counter is reset
    on a succesful login or a changed password.
    """

    email: models.EmailField = models.EmailField()
    time: models.DateTimeField = models.DateTimeField()
    failed_attempt: models.IntegerField = models.IntegerField()

    class Meta:  # pylint: disable=too-few-public-methods
        db_table = "authentication_log"

    @staticmethod
    def get_last_login_for(email: str) -> AuthenticationLog | None:
        """Get the latest authentication attempt for a specified email."""
        query = AuthenticationLog.objects.filter(  # pylint: disable=no-member
            email__iexact=email,
        ).order_by("-time", "-failed_attempt")
        try:
            result = query[0]
        except IndexError:
            result = None
        return result

    @staticmethod
    def is_user_locked_out(email: str) -> bool:
        last_login = AuthenticationLog.get_last_login_for(email)
        return (
            last_login is not None
            and last_login.failed_attempt > LOCKOUT_THRESHOLD
            and AuthenticationLog.get_remaining_lockout_time(email) > 0
        )

    @staticmethod
    def get_locked_out_error(email: str) -> ValidationError:
        seconds_left = AuthenticationLog.get_remaining_lockout_time(email)
        hours = int(seconds_left / 3600)
        minutes = int(seconds_left / 60) % 60
        time_to_unlock = f"{hours} hours and {minutes} minutes"
        return ValidationError(
            "This account is locked out for %(time)s",
            code="locked_out",
            params={"time": time_to_unlock},
        )

    @staticmethod
    def get_remaining_lockout_time(email: str) -> float:
        """Get the remaining lockout time for a specified email."""
        last_login = AuthenticationLog.get_last_login_for(email)
        if last_login is None:
            return 0
        if last_login.failed_attempt is None:
            return 0
        if last_login.time is None:
            return 0

        assert last_login is not None
        assert last_login.time is not None
        assert last_login.failed_attempt is not None

        current_time = timezone.now().replace(microsecond=0)
        lockout_time = \
            pow(2, int(last_login.failed_attempt) - LOCKOUT_THRESHOLD)
        return float(
            (
                - (current_time - last_login.time)
                + timedelta(minutes=lockout_time)
            ).total_seconds())

    @staticmethod
    def log_authentication_attempt(email: str, failed: bool) -> None:
        """Log an attempt for authentication."""
        last_login = AuthenticationLog.get_last_login_for(email)

        if failed:
            failed_attempt = last_login.failed_attempt if last_login else 0
            failed_attempt += 1
        else:
            failed_attempt = 0

        login_attempt = AuthenticationLog(
            email=email,
            time=timezone.now().replace(microsecond=0),
            failed_attempt=failed_attempt,
        )
        login_attempt.save()


def staff_update(
    sender: Any, **kwargs: Any,  # pylint: disable=unused-argument
) -> None:
    """Update if user is part of staff when SUPERUSER_GROUP is added/rmed."""
    for key in ["action", "instance", "reverse"]:
        if key not in kwargs:
            return
    if kwargs["action"] not in ["post_add", "post_remove", "post_clear"]:
        return

    if kwargs["reverse"]:
        users = WdaeUser.objects.filter(pk__in=kwargs["pk_set"])
    else:
        users = [kwargs["instance"]]  # type: ignore

    with transaction.atomic():
        for user in users:
            should_be_staff = user.groups.filter(
                name=WdaeUser.SUPERUSER_GROUP,
            ).exists()
            if user.is_staff != should_be_staff:
                user.is_staff = should_be_staff
                user.save()


def group_post_delete(
    sender: Type[Group], **kwargs: Any,  # pylint: disable=unused-argument
) -> None:
    """Automatically remove staff privileges of SUPERUSER_GROUP users.

    Automatically remove staff privileges of users belonging to the
    SUPERUSER_GROUP group if that group is deleted.
    """
    if "instance" not in kwargs:
        return
    group = kwargs["instance"]
    if group.name != WdaeUser.SUPERUSER_GROUP:
        return
    if not hasattr(group, "_user_ids"):
        return

    with transaction.atomic():
        # pylint: disable=protected-access
        for user in WdaeUser.objects.filter(pk__in=group._user_ids).all():
            user.is_staff = False
            user.save()


# a hack to save the users the group had, used in the post_delete signal
def group_pre_delete(
    sender: Type[Group], **kwargs: Any,  # pylint: disable=unused-argument
) -> None:
    """Attach user-ids when a group is being deleted.

    When deleting a group, attaches the ids of the users who belonged to it
    in order to be used in the post_delete signal. Used only for the
    SUPERUSER_GROUP group.
    """
    if "instance" not in kwargs:
        return
    group = kwargs["instance"]
    if group.name == WdaeUser.SUPERUSER_GROUP:
        # pylint: disable=protected-access
        group._user_ids = [u.pk for u in group.user_set.all()]


m2m_changed.connect(
    staff_update, WdaeUser.groups.through,  # pylint: disable=no-member
    weak=False)
post_delete.connect(group_post_delete, Group, weak=False)
pre_delete.connect(group_pre_delete, Group, weak=False)


LOCKOUT_THRESHOLD = 4


def csrf_clear(view_func: Callable) -> Any:
    """Skips the CSRF checks by setting the 'csrf_processing_done' to true."""

    def wrapped_view(*args: Any, **kwargs: Any) -> Any:
        request = args[0]
        request.csrf_processing_done = True
        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapped_view)


def get_default_application() -> Application:
    # pylint: disable=import-outside-toplevel
    from django.conf import settings
    client_id = settings.DEFAULT_OAUTH_APPLICATION_CLIENT
    model = get_application_model()
    return model.objects.get(client_id=client_id)


def send_verif_email(user: WdaeUser, verif_path: BaseVerificationCode) -> None:
    """Send a verification email to the user."""
    # pylint: disable=import-outside-toplevel
    from django.conf import settings
    email = _create_verif_email(
        settings.EMAIL_VERIFICATION_ENDPOINT,  # type: ignore
        settings.EMAIL_VERIFICATION_SET_PATH,
        str(verif_path.path),
    )
    user.email_user(email["subject"], email["message"])


def send_already_existing_email(user: WdaeUser) -> None:
    """Send an email to already existing user."""
    subject = "GPF: Attempted registration with email in use"
    message = (
        "Hello. Someone has attempted to create an account in GPF "
        "using an email that your account was registered with.  "
        "If this was you, you can simply log in to your existing account, "
        "or if you've forgotten your password, you can reset it "
        "by using the 'Forgotten password' button on the login window. \n"
        "Otherwise, please ignore this email."
    )
    user.email_user(subject, message)


def send_reset_inactive_acc_email(user: WdaeUser) -> None:
    """Send an email to an inactive user."""
    subject = "GPF: Password reset for inactive account"
    message = (
        "Hello. You've requested a password reset for an inactive account. "
        "You must first finish your registration by following the "
        "account validation link in the email you received when registering. "
        "If you have lost that email or the link in it has expired, you can "
        "register again to get a new validation email sent. \n"
        "If you did not request this, please ignore this email."
    )
    user.email_user(subject, message)


def send_reset_email(
    user: WdaeUser, verif_path: BaseVerificationCode,
    by_admin: bool = False,
) -> None:
    """Return dict with subject and message of the email."""
    # pylint: disable=import-outside-toplevel
    from django.conf import settings
    email = _create_reset_mail(
        settings.EMAIL_VERIFICATION_ENDPOINT,  # type: ignore
        settings.EMAIL_VERIFICATION_RESET_PATH,
        str(verif_path.path),
        by_admin,
    )

    user.email_user(email["subject"], email["message"])


def _create_verif_email(
    endpoint: str, path: str, verification_path: str,
) -> dict[str, str]:
    message = (
        "Welcome to GPF: Genotype and Phenotype in Families! "
        "Follow the link below to validate your new account "
        "and set your password:\n {link}"
    )

    email_settings = {
        "subject": "GPF: Registration validation",
        "initial_message": message,
        "endpoint": endpoint,
        "path": path,
        "verification_path": verification_path,
    }

    return _build_email_template(email_settings)


def _create_reset_mail(
    endpoint: str, path: str, verification_path: str, by_admin: bool = False,
) -> dict[str, str]:
    message = (
        "Hello. You have requested to reset your password for "
        "your GPF account. To do so, please follow the link below:\n {link}\n"
        "If you did not request for your GPF account password to be reset, "
        "please ignore this email."
    )
    if by_admin:
        message = (
            "Hello. Your password has been reset by an admin. Your old "
            "password will not work. To set a new password in "
            "GPF: Genotype and Phenotype in Families "
            "please follow the link below:\n {link}"
        )
    email_settings = {
        "subject": "GPF: Password reset request",
        "initial_message": message,
        "endpoint": endpoint,
        "path": path,
        "verification_path": verification_path,
    }

    return _build_email_template(email_settings)


def _build_email_template(email_settings: dict[str, str]) -> dict[str, str]:
    subject = email_settings["subject"]
    message = email_settings["initial_message"]
    path = email_settings["path"].format(email_settings["verification_path"])

    message = message.format(link=f"{email_settings['endpoint']}{path}")

    return {"subject": subject, "message": message}
