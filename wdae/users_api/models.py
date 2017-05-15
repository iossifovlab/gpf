'''
Created on Aug 10, 2016

@author: lubo
'''
import uuid

from django.db import models
from django.core.mail import send_mail
# from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin
from django.utils import timezone
from django.conf import settings
from guardian.conf import settings as guardian_settings
from django.contrib.auth.models import Group
from helpers.logger import LOGGER


class WdaeUserManager(BaseUserManager):

    def _create_user(self, email, password):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)

        user.save(using=self._db)

        groups = list(user.DEFAULT_GROUPS_FOR_USER)
        groups.append(email)
        for group_name in groups:
            group, _ = Group.objects.get_or_create(name=group_name)
            group.user_set.add(user)
            group.save()

        return user

    def create_user(self, email, password=None,):
        user = self._create_user(email, password)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self._create_user(email, password)

        user.is_superuser = True
        user.is_active = True
        user.is_staff = True

        user.save()

        return user


class WdaeUser(AbstractBaseUser, PermissionsMixin):
    app_label = 'api'
    name = models.CharField(max_length='100')
    email = models.EmailField(unique=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    DEFAULT_GROUPS_FOR_USER = ("any_user", )
    RESEARCHER_GROUP_PREFIX = "SFID#"

    objects = WdaeUserManager()

    def email_user(self, subject, message, from_email=None):
        override = None
        try:
            override = settings.EMAIL_OVERRIDE
        except Exception:
            LOGGER.info("exception on email override")
            override = None
        if override:
            mail = send_mail(subject, message, from_email, override)
        else:
            mail = send_mail(subject, message, from_email, [self.email])

        return mail

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        "Returns the short name for the user."
        return self.name

    def reset_password(self):
        self.set_password(uuid.uuid4())
        self.save()

        verif_path = _create_verif_path(self)
        send_reset_email(self, verif_path)

    def register_preexisting_user(self, name):
        now = timezone.now()

        self.date_joined = now
        self.name = name

        verif_path = _create_verif_path(self)
        send_verif_email(self, verif_path)

        self.save()

    @staticmethod
    def change_password(verification_path, new_password):
        verif_path = VerificationPath.objects.get(path=verification_path)

        user = verif_path.user
        user.set_password(new_password)
        user.is_active = True
        user.save()

        verif_path.delete()

        return user

    @classmethod
    def get_group_name_for_researcher_id(cls, researcher_id):
        return cls.RESEARCHER_GROUP_PREFIX + researcher_id

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'users'


def send_verif_email(user, verif_path):
    email = _create_verif_email(
        settings.EMAIL_VERIFICATION_HOST,
        settings.EMAIL_VERIFICATION_PATH, str(verif_path.path))
    user.email_user(email['subject'], email['message'])


def send_reset_email(user, verif_path):
    ''' Returns dict - subject and message of the email '''
    email = _create_reset_mail(
        settings.EMAIL_VERIFICATION_HOST,
        settings.EMAIL_VERIFICATION_PATH, str(verif_path.path))

    user.email_user(email['subject'], email['message'])


def _create_verif_email(host, path, verification_path):
    settings = {
        'subject': 'GPF: Registration validation',
        'initial_message': 'Hello. Follow this link to validate '
        'your account in GPF: Genotype and Phenotype in Families '
        'and to set your new password: ',
        'host': host,
        'path': path,
        'verification_path': verification_path
    }

    return _build_email_template(settings)


def _create_reset_mail(host, path, verification_path):
    settings = {
        'subject': 'GPF: Password reset',
        'initial_message': 'Hello. To change your password in '
        'GPF: Genotype and Phenotype in Families '
        'please follow this link: ',
        'host': host,
        'path': path,
        'verification_path': verification_path
    }

    return _build_email_template(settings)

# ''' settings[dict] must contain :
# subject, initial_message, host, path, verification_path'''


def _build_email_template(settings):
    subject = settings['subject']
    message = settings['initial_message']
    path = settings['path'].format(settings['verification_path'])

    message += '{0}{1}'.format(settings['host'], path)

    return {
        'subject': subject,
        'message': message
    }


def _create_verif_path(user):
    verif_path, _ = \
        VerificationPath.objects.get_or_create(user=user,
                                               defaults={'path': uuid.uuid4()})
    return verif_path


def get_anonymous_user_instance(CurrentUserModel):
    try:
        user = CurrentUserModel.objects.get(
            email=guardian_settings.ANONYMOUS_USER_NAME)
        return user
    except CurrentUserModel.DoesNotExist:
        user = CurrentUserModel.objects.create_user(
            email=guardian_settings.ANONYMOUS_USER_NAME)
        user.set_unusable_password()
        user.is_active = True
        user.save()
        return user


class VerificationPath(models.Model):
    path = models.CharField(max_length='255', unique=True)
    user = models.OneToOneField(WdaeUser)

    def __str__(self):
        return str(self.path)

    class Meta:
        db_table = 'verification_paths'
