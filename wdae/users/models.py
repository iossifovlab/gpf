'''
Created on Aug 10, 2016

@author: lubo
'''
import uuid

from django.db import models
from django.core.mail import send_mail
# from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.conf import settings


class Researcher(models.Model):
    first_name = models.CharField(max_length='100')
    last_name = models.CharField(max_length='100')
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.first_name + ' ' + self.last_name + ' ' + self.email

    class Meta:
        db_table = 'researchers'


class ResearcherId(models.Model):
    researcher = models.ManyToManyField(Researcher)
    researcher_id = models.CharField(max_length='100', unique=True)

    class Meta:
        db_table = 'researcherid'


class VerificationPath(models.Model):
    path = models.CharField(max_length='255', unique=True)

    def __str__(self):
        return str(self.path)

    class Meta:
        db_table = 'verification_paths'


class WdaeUserManager(BaseUserManager):

    def _create_user(self, email, password, researcher_id=None,
                     is_staff=False, is_active=False):
        """
        Creates and saves a User with the given email and password.
        """

        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.date_joined = now
        user.set_password(password)
        user.is_staff = is_staff
        user.is_active = is_active

        if(not user.is_staff):
            user.verification_path = _create_verif_path()
            user.researcher_id = researcher_id
        user.save(using=self._db)

        return user

    def create_user(self, email, researcher_id, password=None,):
        user = self._create_user(email, uuid.uuid4(), researcher_id)
        send_verif_email(user)

        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self._create_user(email, password, None, True, True)
        user.first_name = extra_fields['first_name']
        user.last_name = extra_fields['last_name']
        user.save()

        return user


class WdaeUser(AbstractBaseUser):
    app_label = 'api'
    first_name = models.CharField(max_length='100')
    last_name = models.CharField(max_length='100')
    email = models.EmailField(unique=True)
    researcher_id = models.CharField(
        max_length='100',
        blank=True,
        null=True)
    verification_path = models.OneToOneField(
        VerificationPath,
        blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = WdaeUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['researcher_id', 'first_name', 'last_name']

    def email_user(self, subject, message, from_email=None):
        mail = send_mail(subject, message, from_email, [self.email])
        return mail

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    @property
    def is_superuser(self):
        return self.is_staff

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def reset_password(self):
        self.set_password(uuid.uuid4())
        self.verification_path = _create_verif_path()
        self.save()
        send_reset_email(self)

    @staticmethod
    def change_password(verification_path, new_password):
        verif_path = VerificationPath.objects.get(path=verification_path)

        user = WdaeUser.objects.get(verification_path=verif_path)
        user.set_password(new_password)
        user.verification_path.delete()
        user.verification_path = None
        user.is_active = True
        user.save()

        return user

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'users'


def send_verif_email(user):
    email = _create_verif_email(
        settings.EMAIL_VERIFICATION_HOST,
        settings.EMAIL_VERIFICATION_PATH, str(user.verification_path.path))
    user.email_user(email['subject'], email['message'])


def send_reset_email(user):
    ''' Returns dict - subject and message of the email '''
    email = _create_reset_mail(
        settings.EMAIL_VERIFICATION_HOST,
        settings.EMAIL_VERIFICATION_PATH, str(user.verification_path))

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
    message += '{0}{1}{2}'.format(settings['host'],
                                  settings['path'],
                                  settings['verification_path'])

    return {
        'subject': subject,
        'message': message
    }


def _create_verif_path():
    verif_path = VerificationPath()
    verif_path.path = uuid.uuid4()
    verif_path.save()

    return verif_path
