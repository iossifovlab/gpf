from rest_framework.test import APITestCase
from rest_framework import status
from datasets_api.models import Dataset
from guardian.utils import get_anonymous_user
from users_api.models import WdaeUser
from django.contrib.auth.models import Group


class DatasetPermTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(DatasetPermTest, cls).setUpClass()
        Dataset.recreate_dataset_perm('META', [])
        Dataset.recreate_dataset_perm('SD_TEST', [])

    def get_dataset_permission(self, url='/api/v3/datasets/SD_TEST'):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)

        data = data['data']
        self.assertIn('accessRights', data)
        return data['accessRights']

    def test_wrong_group(self):
        groups = ["blabla"]
        Dataset.recreate_dataset_perm("SD_TEST", groups)

        self.assertFalse(self.get_dataset_permission())

    def test_default_user_groups(self):
        groups = WdaeUser.DEFAULT_GROUPS_FOR_USER
        Dataset.recreate_dataset_perm("SD_TEST", groups)

        self.assertTrue(self.get_dataset_permission())

        user = WdaeUser.objects.create_user(email='admin@example.com',
                                            password='secret')
        user.is_active = True
        user.save()
        self.client.login(email='admin@example.com', password='secret')

        self.assertTrue(self.get_dataset_permission())

    def test_default_dataset_group(self):
        Dataset.recreate_dataset_perm("SD_TEST", [])
        self.assertFalse(self.get_dataset_permission())

        user = WdaeUser.objects.create_user(email='admin@example.com',
                                            password='secret')
        user.is_active = True
        user.save()
        self.client.login(email='admin@example.com', password='secret')
        self.assertFalse(self.get_dataset_permission())

        group, _ = Group.objects.get_or_create(name="SD_TEST")
        group.user_set.add(user)
        self.client.login(email='admin@example.com', password='secret')
        self.assertTrue(self.get_dataset_permission())

    def test_default_all_datasets_access_group(self):
        Dataset.recreate_dataset_perm("SD_TEST", [])
        self.assertFalse(self.get_dataset_permission())

        user = WdaeUser.objects.create_user(email='admin@example.com',
                                            password='secret')
        user.is_active = True
        user.save()
        self.client.login(email='admin@example.com', password='secret')
        self.assertFalse(self.get_dataset_permission())

        group_name = Dataset.DEFAULT_GROUPS_FOR_DATASET[0]
        group, _ = Group.objects.get_or_create(name=group_name)
        group.user_set.add(user)
        self.client.login(email='admin@example.com', password='secret')
        self.assertTrue(self.get_dataset_permission())

    def test_anonymous_user_group(self):
        groups = [get_anonymous_user().email]
        Dataset.recreate_dataset_perm("SD_TEST", groups)
        self.assertTrue(self.get_dataset_permission())

        user = WdaeUser.objects.create_user(email='admin@example.com',
                                            password='secret')
        user.is_active = True
        user.save()
        self.client.login(email='admin@example.com', password='secret')
        self.assertFalse(self.get_dataset_permission())

    def test_group_with_email_name(self):
        groups = ['admin@example.com']
        Dataset.recreate_dataset_perm("SD_TEST", groups)
        self.assertFalse(self.get_dataset_permission())

        user = WdaeUser.objects.create_user(email='admin@example.com',
                                            password='secret')
        user.is_active = True
        user.save()
        self.client.login(email='admin@example.com', password='secret')
        self.assertTrue(self.get_dataset_permission())
