import uuid

from django.db import models
from django.core.mail import send_mail

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager

from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings

from utils.logger import LOGGER
from datasets_api.permissions import get_directly_allowed_genotype_data

from .utils import send_reset_email, send_verif_email, send_already_existing_email


class WdaeUser(AbstractBaseUser, PermissionsMixin):
    name: models.CharField = models.CharField(max_length=100)
    email: models.EmailField = models.EmailField(unique=True)

    is_staff: models.BooleanField = models.BooleanField(default=False)
    is_active: models.BooleanField = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    SUPERUSER_GROUP = "admin"
    UNLIMITED_DOWNLOAD_GROUP = "unlimited"

    objects = UserManager()

    @property
    def has_unlimited_download(self):
        return self.groups.filter(name=self.UNLIMITED_DOWNLOAD_GROUP).count() > 0

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

        to_email = self.email if not override else override

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
        verif_path = VerificationPath.create(self)
        send_reset_email(self, verif_path, by_admin)

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
            if name is not None and name != "":
                self.name = name

            verif_path = VerificationPath.create(self)
            send_verif_email(self, verif_path)

            self.save()

    @staticmethod
    def change_password(verification_path, new_password):
        verif_path = VerificationPath.objects.get(path=verification_path)

        user = verif_path.user
        user.set_password(new_password)
        user.save()

        # Reset account lockout
        AuthenticationLog(
            email=user.email, time=timezone.now(), failed_attempt=0
        ).save()

        verif_path.delete()

        return user

    def __str__(self):
        return self.email

    class Meta(object):
        db_table = "users"


class VerificationPath(models.Model):
    path = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(WdaeUser, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.path)

    @staticmethod
    def create(user):
        verif_path, _ = VerificationPath.objects.get_or_create(
            user=user, defaults={"path": uuid.uuid4()}
        )
        return verif_path

    class Meta(object):
        db_table = "verification_paths"


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
