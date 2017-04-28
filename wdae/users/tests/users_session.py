'''
Created on May 25, 2015

@author: lubo
'''
from users.models import WdaeUser, VerificationPath, ResearcherId
from django.contrib.auth import authenticate, get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from pprint import pprint


class ResearcherRegistrationTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(ResearcherRegistrationTest, cls).setUpClass()

        cls.res = WdaeUser()
        cls.res.first_name = 'fname'
        cls.res.last_name = 'lname'
        cls.res.email = 'fake@fake.com'
        cls.res.save()

        cls.research_id = ResearcherId()
        cls.research_id.researcher_id = '11aa--bb'
        cls.research_id.save()

        cls.research_id.researcher.add(cls.res)

    @classmethod
    def tearDownClass(cls):
        super(ResearcherRegistrationTest, cls).tearDownClass()
        cls.res.delete()

    def test_fail_register(self):
        data = {
            'email': 'faulthymail@faulthy.com',
            'firstName': 'bad_first_name',
            'lastName': 'bad_last_name'
        }

        response = self.client.post('/api/v3/users/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_register(self):
        [id1] = self.res.researcherid_set.all()
        data = {
            'firstName': self.res.first_name,
            'lastName': self.res.last_name,
            'researcherId': id1.researcher_id,
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['researcherId'], id1.researcher_id)
        self.assertEqual(response.data['email'], self.res.email)


class UserAuthenticationTest(APITestCase):

    def setUp(self):
        self.user = WdaeUser.objects.create(email="test@example.com",
                                            first_name="Ivan",
                                            last_name="Testov")
        self.user.set_password("pass")
        self.user.is_active = True
        self.user.save()

    def test_successful_auth(self):
        data = {
            'username': 'test@example.com',
            'password': 'pass',
        }

        response = self.client.post(
            '/api/v3/users/login', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_failed_auth(self):
        data = {
            'username': 'bad@example.com',
            'password': 'pass'
        }

        response = self.client.post(
            '/api/v3/users/login', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_user_info_after_auth(self):
        self.user.is_staff = True
        self.user.save()

        data = {
            'username': 'test@example.com',
            'password': 'pass',
        }

        response = self.client.post(
            '/api/v3/users/login', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get('/api/v3/users/get_user_info')
        self.assertEqual(response.data['loggedIn'], True)
        self.assertEqual(response.data['email'], 'test@example.com')
