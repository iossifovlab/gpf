'''
Created on Apr 29, 2017

@author: lubo
'''
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from datasets_api.studies_manager import get_studies_manager
from datasets_api.models import Dataset

from precompute import register


class BaseAuthenticatedUserTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        raise RuntimeError("BaseAuthenticatedUserTest should be removed")
        super(BaseAuthenticatedUserTest, cls).setUpClass()
        dataset_facade = get_studies_manager().get_facade()

        print("datasets in dataset facade: ", dataset_facade.get_all_dataset_ids())
        for dataset in dataset_facade.get_all_datasets():
            Dataset.recreate_dataset_perm(dataset.id, [])

        Dataset.recreate_dataset_perm('META', [])
        Dataset.recreate_dataset_perm('SD_TEST', [])
        Dataset.recreate_dataset_perm('SD', [])
        Dataset.recreate_dataset_perm('SSC', [])
        Dataset.recreate_dataset_perm('SVIP', [])
        Dataset.recreate_dataset_perm('SPARKv1', [])
        Dataset.recreate_dataset_perm('SPARKv2', [])
        Dataset.recreate_dataset_perm('AGRE_WG', [])
        Dataset.recreate_dataset_perm('TESTdenovo_db', [])

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

