import uuid
from datetime import timedelta

from django.db import models, transaction
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from django.contrib.auth.models import \
    AbstractBaseUser, \
    BaseUserManager, \
    PermissionsMixin

from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed, post_delete, pre_delete

from utils.logger import LOGGER
from datasets_api.permissions import get_directly_allowed_genotype_data

from .utils import send_reset_email, send_already_existing_email, \
    send_verif_email, LOCKOUT_THRESHOLD


class WdaeUserManager(BaseUserManager):
    def _create_user(self, email, password, **kwargs):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("The given email must be set")

        email = self.normalize_email(email)
        email = email.lower()

        user = self.model(email=email, **kwargs)
        user.set_password(password)

        user.save(using=self._db)

        return user

    def get_or_create(self, **kwargs):
        try:
            return self.get(**kwargs), False
        except WdaeUser.DoesNotExist:
            return self.create_user(**kwargs), True

    def create(self, **kwargs):
        return self.create_user(**kwargs)

    def create_user(self, email, password=None, **kwargs):
        user = self._create_user(email, password, **kwargs)
        return user

    def create_superuser(self, email, password, **kwargs):
        user = self._create_user(email, password, **kwargs)

        user.is_superuser = True
        user.is_active = True
        user.is_staff = True

        user.save()

        return user


class WdaeUser(AbstractBaseUser, PermissionsMixin):
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
    def has_unlimited_download(self):
        return self.groups.filter(
            name=self.UMLIMITED_DOWNLOAD_GROUP).count() > 0

    @property
    def allowed_datasets(self):
        return get_directly_allowed_genotype_data(self)

    def email_user(self, subject, message, from_email=None):
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL

        override = None
        try:
            override = settings.EMAIL_OVERRIDE
        except Exception:
            LOGGER.debug("no email override; sending email")
            override = None
        if override:
            to_email = override
        else:
            to_email = self.email

        mail = send_mail(subject, message, from_email, [to_email])
        LOGGER.info("email sent: to:      <" + str(self.email) + ">")
        LOGGER.info("email sent: from:    <" + str(from_email) + ">")
        LOGGER.info("email sent: subject: " + str(subject))
        LOGGER.info("email sent: message: " + str(message))

        return mail

    def set_password(self, raw_password):
        super(WdaeUser, self).set_password(raw_password)

        has_password = bool(raw_password)
        if self.is_active != has_password:
            self.is_active = has_password

    def set_unusable_password(self):
        super(WdaeUser, self).set_unusable_password()

        if self.is_active:
            self.is_active = False

    def reset_password(self, by_admin=False):
        verif_code = ResetPasswordCode.create(self)
        send_reset_email(self, verif_code, by_admin)

    def deauthenticate(self):
        all_sessions = Session.objects.all()
        for session in all_sessions:
            session_data = session.get_decoded()
            if self.pk == session_data.get("_auth_user_id"):
                session.delete()

    def register_preexisting_user(self, name):
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
    def change_password(verification_path, new_password):
        user = verification_path.user
        user.set_password(new_password)
        user.save()

        # Reset account lockout
        AuthenticationLog(
            email=user.email,
            time=timezone.now(),
            failed_attempt=0
        ).save()

        verification_path.delete()

        return user

    def __str__(self):
        return self.email

    class Meta(object):
        db_table = "users"


class BaseVerificationCode(models.Model):
    """Base class for temporary codes for verifying the user without login."""

    path: models.Field = models.CharField(max_length=255, unique=True)
    user: models.Field = models.OneToOneField(
        WdaeUser, on_delete=models.CASCADE)
    created_at: models.Field = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.path)

    def validate(self):
        raise NotImplementedError

    class Meta:
        abstract = True

    @classmethod
    def get_code(cls, user):
        try:
            return cls.objects.get(user=user)
        except ObjectDoesNotExist:
            return None

    @classmethod
    def create(cls, user):
        try:
            verif_code = cls.objects.get(user=user)
        except ObjectDoesNotExist:
            verif_code = cls.objects.create(user=user, path=uuid.uuid4())
            return verif_code

        if verif_code.validate is not True:
            verif_code.delete()
            return cls.create(user)

        return verif_code


class SetPasswordCode(BaseVerificationCode):
    """Base class for temporary paths for verifying user without login."""

    class Meta:
        db_table = "set_password_verification_codes"

    def validate(self):
        return True


class ResetPasswordCode(BaseVerificationCode):
    """Class used for verification of password resets."""

    class Meta:
        db_table = "reset_password_verification_codes"

    def validate(self):
        max_delta = timedelta(hours=settings.RESET_PASSWORD_TIMEOUT_HOURS)
        if timezone.now() - self.created_at > max_delta:
            return False
        return True


class AuthenticationLog(models.Model):
    """A model to keep track of all requests for
    authentication: which email was used, when they were
    made and what number of consecutive failed attempts have
    been made on this email. The failed attempt counter is reset
    on a succesful login or a changed password.
    """
    email = models.EmailField()
    time = models.DateTimeField()
    failed_attempt = models.IntegerField()

    class Meta():
        db_table = "authentication_log"

    @staticmethod
    def get_last_login_for(email: str):
        """Get the latest authentication attempt for a specified email."""
        query = AuthenticationLog.objects.filter(
            email__iexact=email
        ).order_by("-time", "-failed_attempt")
        try:
            result = query[0]
        except IndexError:
            result = None
        return result

    @staticmethod
    def is_user_locked_out(email: str):
        last_login = AuthenticationLog.get_last_login_for(email)
        return (
            last_login is not None
            and last_login.failed_attempt > LOCKOUT_THRESHOLD
            and AuthenticationLog.get_remaining_lockout_time(email) > 0
        )

    @staticmethod
    def get_locked_out_error(email: str):
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
    def get_remaining_lockout_time(email: str):
        last_login = AuthenticationLog.get_last_login_for(email)
        current_time = timezone.now().replace(microsecond=0)
        lockout_time = pow(2, last_login.failed_attempt - LOCKOUT_THRESHOLD)
        return (
            - (current_time - last_login.time)
            + timedelta(minutes=lockout_time)
        ).total_seconds()

    @staticmethod
    def log_authentication_attempt(email: str, failed: bool):
        last_login = AuthenticationLog.get_last_login_for(email)

        if failed:
            failed_attempt = last_login.failed_attempt if last_login else 0
            failed_attempt += 1
        else:
            failed_attempt = 0

        login_attempt = AuthenticationLog(
            email=email,
            time=timezone.now().replace(microsecond=0),
            failed_attempt=failed_attempt
        )
        login_attempt.save()


def staff_update(sender, **kwargs):
    """Updates whether a user is part of the staff when the SUPERUSER_GROUP is
    added or removed to them.
    """
    for key in ["action", "instance", "reverse"]:
        if key not in kwargs:
            return
    if kwargs["action"] not in ["post_add", "post_remove", "post_clear"]:
        return

    if kwargs["reverse"]:
        users = WdaeUser.objects.filter(pk__in=kwargs["pk_set"])
    else:
        users = [kwargs["instance"]]

    with transaction.atomic():
        for user in users:
            should_be_staff = user.groups.filter(
                name=WdaeUser.SUPERUSER_GROUP
            ).exists()
            if user.is_staff != should_be_staff:
                user.is_staff = should_be_staff
                user.save()


def group_post_delete(sender, **kwargs):
    """Automatically remove staff privileges of users who belonged to the
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
        for user in WdaeUser.objects.filter(pk__in=group._user_ids).all():
            user.is_staff = False
            user.save()


# a hack to save the users the group had, used in the post_delete signal
def group_pre_delete(sender, **kwargs):
    """When deleting a group, attaches the ids of the users who belonged to it
    in order to be used in the post_delete signal. Used only for the
    SUPERUSER_GROUP group.
    """
    if "instance" not in kwargs:
        return
    group = kwargs["instance"]
    if group.name == WdaeUser.SUPERUSER_GROUP:
        group._user_ids = [u.pk for u in group.user_set.all()]


m2m_changed.connect(staff_update, WdaeUser.groups.through, weak=False)
post_delete.connect(group_post_delete, Group, weak=False)
pre_delete.connect(group_pre_delete, Group, weak=False)
