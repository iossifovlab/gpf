'''
Created on Apr 29, 2017

@author: lubo
'''
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from datasets_api.models import Dataset


class BaseAuthenticatedUserTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(BaseAuthenticatedUserTest, cls).setUpClass()
        Dataset.recreate_dataset_perm('META', [])
        Dataset.recreate_dataset_perm('SD_TEST', [])
        Dataset.recreate_dataset_perm('SD', [])
        Dataset.recreate_dataset_perm('SSC', [])
        Dataset.recreate_dataset_perm('SVIP', [])
        Dataset.recreate_dataset_perm('SPARKv1', [])
        Dataset.recreate_dataset_perm('SPARKv2', [])
        Dataset.recreate_dataset_perm('AGRE_WG', [])
        Dataset.recreate_dataset_perm('denovo_db', [])

        User = get_user_model()
        u = User.objects.create(
            email="admin@example.com",
            name="First",
            is_staff=True,
            is_active=True,
            is_superuser=True)
        u.set_password("secret")
        u.save()

        Token.objects.get_or_create(user=u)
        cls.user = u
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        super(BaseAuthenticatedUserTest, cls).tearDownClass()

        cls.user.delete()

    def setUp(self):
        super(BaseAuthenticatedUserTest, self).setUp()

        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
