from rest_framework.test import APITestCase
from rest_framework import status
from datasets_api.models import Dataset
from guardian.utils import get_anonymous_user


class DatasetPermTest(APITestCase):

    def test_wrong_group(self):
        groups = ["blabla"]
        Dataset.recreate_dataset_perm("SD", groups)

        url = '/api/v3/datasets/SD'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)

        data = data['data']
        self.assertIn('accessRights', data)
        self.assertFalse(data['accessRights'])

    def test_anonymous_user_group(self):
        groups = [get_anonymous_user().email]
        Dataset.recreate_dataset_perm("SD", groups)

        url = '/api/v3/datasets/SD'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)

        data = data['data']
        self.assertIn('accessRights', data)
        self.assertFalse(data['accessRights'])
