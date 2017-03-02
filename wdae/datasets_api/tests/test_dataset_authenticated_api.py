'''
Created on Jan 20, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status
from pprint import pprint
from django.contrib.auth import get_user_model


class DatasetApiTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(DatasetApiTest, cls).setUpClass()

        User = get_user_model()
        u = User.objects.create(
            email="admin@example.com",
            first_name="First",
            last_name="Last",
            is_staff=True,
            is_active=True,
            researcher_id="0001000")
        u.set_password("secret")
        u.save()

        cls.user = u
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        super(DatasetApiTest, cls).tearDownClass()
        cls.user.delete()

    def test_get_dataset_ssc(self):
        res = self.client.login(
            email='admin@example.com', password='secret')
        print(res)

        url = '/api/v3/datasets/SSC'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        pprint(data)
        data = data['data']
        self.assertIn('accessRights', data)
        self.assertTrue(data['accessRights'])

    def test_get_dataset_sd(self):
        self.client.login(email='admin@example.com', password='secret')

        url = '/api/v3/datasets/SD'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        pprint(data)

        data = data['data']
        self.assertIn('accessRights', data)
        self.assertTrue(data['accessRights'])

    def test_get_dataset_vip(self):
        self.client.login(email='admin@example.com', password='secret')

        url = '/api/v3/datasets/VIP'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        pprint(data)
        data = data['data']
        self.assertIn('accessRights', data)
        self.assertTrue(data['accessRights'])
