"""
Created on Aug 10, 2016

@author: lubo
"""
import uuid

from django.db import models, transaction
from django.core.mail import send_mail

from django.contrib.auth.models import \
    AbstractBaseUser, \
    BaseUserManager, \
    PermissionsMixin

from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
from guardian.conf import settings as guardian_settings  # type: ignore
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed, post_delete, pre_delete

from utils.logger import LOGGER
from datasets_api.permissions import get_directly_allowed_genotype_data


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

        groups = list(user.DEFAULT_GROUPS_FOR_USER)
        groups.append(email)

        for group_name in groups:
            group, _ = Group.objects.get_or_create(name=group_name)
            group.user_set.add(user)
            group.save()

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
    app_label = "api"
    name: models.CharField = models.CharField(max_length=100)
    email: models.EmailField = models.EmailField(unique=True)

    is_staff: models.BooleanField = models.BooleanField(default=False)
    is_active: models.BooleanField = models.BooleanField(default=False)
    date_joined: models.DateTimeField = models.DateTimeField(null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    DEFAULT_GROUPS_FOR_USER = ("any_user",)
    SUPERUSER_GROUP = "admin"
    UMLIMITTED_DOWNLOAD_GROUP = "unlimitted"

    objects = WdaeUserManager()

    def get_protected_group_names(self):
        return self.DEFAULT_GROUPS_FOR_USER + (self.email,)

    @property
    def protected_groups(self):
        return self.groups.filter(name__in=self.get_protected_group_names())

    @property
    def has_unlimitted_download(self):
        return self.groups.filter(
            name=self.UMLIMITTED_DOWNLOAD_GROUP).count() > 0

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

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        "Returns the short name for the user."
        return self.name

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

        verif_path = _create_verif_path(self)
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
            self.date_joined = timezone.now()
            if name is not None and name != "":
                self.name = name

            verif_path = _create_verif_path(self)
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
            email=user.email,
            time=timezone.now(),
            failed_attempt=0
        ).save()

        verif_path.delete()

        return user

    def __str__(self):
        return self.email

    class Meta(object):
        db_table = "users"


def send_verif_email(user, verif_path):
    email = _create_verif_email(
        settings.EMAIL_VERIFICATION_HOST,
        settings.EMAIL_VERIFICATION_PATH,
        str(verif_path.path),
    )
    user.email_user(email["subject"], email["message"])


def send_already_existing_email(user):
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


def send_reset_inactive_acc_email(user):
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


def send_reset_email(user, verif_path, by_admin=False):
    """ Returns dict - subject and message of the email """
    email = _create_reset_mail(
        settings.EMAIL_VERIFICATION_HOST,
        settings.EMAIL_VERIFICATION_PATH,
        str(verif_path.path),
        by_admin,
    )

    user.email_user(email["subject"], email["message"])


def _create_verif_email(host, path, verification_path):
    message = (
        "Welcome to GPF: Genotype and Phenotype in Families! "
        "Follow the link below to validate your new account "
        "and set your password:\n {link}"
    )

    settings = {
        "subject": "GPF: Registration validation",
        "initial_message": message,
        "host": host,
        "path": path,
        "verification_path": verification_path,
    }

    return _build_email_template(settings)


def _create_reset_mail(host, path, verification_path, by_admin=False):
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
    settings = {
        "subject": "GPF: Password reset request",
        "initial_message": message,
        "host": host,
        "path": path,
        "verification_path": verification_path,
    }

    return _build_email_template(settings)


# ''' settings[dict] must contain :
# subject, initial_message, host, path, verification_path'''


def _build_email_template(settings):
    subject = settings["subject"]
    message = settings["initial_message"]
    path = settings["path"].format(settings["verification_path"])

    message = message.format(link="{0}{1}".format(settings["host"], path))

    return {"subject": subject, "message": message}


def _create_verif_path(user):
    verif_path, _ = VerificationPath.objects.get_or_create(
        user=user, defaults={"path": uuid.uuid4()}
    )
    return verif_path


def get_anonymous_user_instance(current_user_model):
    try:
        print("current_user_model:", current_user_model)
        user = current_user_model.objects.get(
            email=guardian_settings.ANONYMOUS_USER_NAME
        )
        return user
    except current_user_model.DoesNotExist:
        user = current_user_model.objects.create_user(
            email=guardian_settings.ANONYMOUS_USER_NAME
        )
        user.set_unusable_password()
        user.is_active = True

        user.save()
        return user


def staff_update(sender, **kwargs):
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
    if "instance" not in kwargs:
        return
    group = kwargs["instance"]
    if group.name == WdaeUser.SUPERUSER_GROUP:
        group._user_ids = [u.pk for u in group.user_set.all()]


m2m_changed.connect(staff_update, WdaeUser.groups.through, weak=False)
post_delete.connect(group_post_delete, Group, weak=False)
pre_delete.connect(group_pre_delete, Group, weak=False)


class VerificationPath(models.Model):
    path = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(WdaeUser, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.path)

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
