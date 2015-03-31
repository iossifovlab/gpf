import uuid

from django.db import models
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

from rest_framework import serializers
from rest_framework.authtoken.models import Token

# TODO: add south

class Researcher(models.Model):
	email = models.EmailField(unique=True)
	unique_number = models.CharField(max_length='100', unique=True)

	class Meta:
		db_table = 'researchers'

class VerificationPath(models.Model):
	path = models.CharField(max_length='255', unique=True)

	class Meta:
		db_table = 'verification_paths'

class WdaeUserManager(BaseUserManager):
    def _create_user(self, email, password, researcher_number):
        """
        Creates and saves a User with the given email and password.
        """
        verif_path = VerificationPath() 
        verif_path.path = uuid.uuid4() 
        verif_path.save() 

        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)

        user = self.model(email=email, date_joined=now)
        user.verification_path = verif_path
        user.researcher_number = researcher_number
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, researcher_number,  password=None,):
        user = self._create_user(email, uuid.uuid4(), researcher_number)
        #user.email_user('Registration validation', 'Hello. Follow this link to validate your account and to set your new password: ' + )

        return user

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)
        

class WdaeUser(AbstractBaseUser):
	objects = WdaeUserManager()

	first_name = models.CharField(max_length='100')
	middle_name = models.CharField(max_length='100')
	last_name = models.CharField(max_length='100')
	email = models.EmailField(unique=True)
	researcher_number = models.CharField(max_length='100', unique=True) #CHECK
	verification_path = models.OneToOneField(VerificationPath)
	is_active = models.BooleanField(default=False)
	date_joined = models.DateTimeField(default=timezone.now)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['researcher_number', 'first_name', 'last_name']

	def email_user(self, subject, message, from_email=None):
		send_mail(subject, message, from_email, [self.email])

	class Meta:
		db_table = 'users'

class UserSerializer(serializers.Serializer):
	first_name = serializers.CharField(max_length='100')
	middle_name = serializers.CharField(max_length='100')
	last_name = serializers.CharField(max_length='100')
	email = serializers.EmailField()
	researcher_number = serializers.CharField(max_length='100') #CHECK

	def validate(self, data):
		user_model = get_user_model()
		try:
			Researcher.objects.get(unique_number=data['researcher_number'], email=data['email'])
		except Researcher.DoesNotExist:
			raise serializers.ValidationError('A researcher with this number was not found.') 

		try:
			user_model.objects.get(email=data['email'])
			raise serializers.ValidationError('A user with the same email already exists')
		except user_model().DoesNotExist:
			return data