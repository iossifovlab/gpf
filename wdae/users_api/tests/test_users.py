from users.models import WdaeUser
from rest_framework.test import APITestCase
from rest_framework import status
from pprint import pprint
from django.contrib.auth.models import Group


class ResearcherRegistrationTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(ResearcherRegistrationTest, cls).setUpClass()

        cls.res = WdaeUser.objects.create_user(email='fake@fake.com')
        cls.res.name = 'fname'
        cls.res.save()

        cls.researcher_id = '11aa--bb'

        group_name = WdaeUser.get_group_name_for_researcher_id(
            cls.researcher_id)
        group, _ = Group.objects.get_or_create(name=group_name)
        group.user_set.add(cls.res)

    @classmethod
    def tearDownClass(cls):
        super(ResearcherRegistrationTest, cls).tearDownClass()
        cls.res.delete()

    def test_fail_register(self):
        data = {
            'email': 'faulthymail@faulthy.com',
            'name': 'bad_name',
        }

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_pass_without_registration(self):
        data = {
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/reset_password', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_register(self):
        data = {
            'name': self.res.name,
            'researcherId': self.researcher_id,
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_twice(self):
            data = {
                'name': self.res.name,
                'researcherId': self.researcher_id,
                'email': self.res.email
            }
            pprint(data)

            response = self.client.post('/api/v3/users/register', data,
                                        format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            response = self.client.post('/api/v3/users/register', data,
                                        format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_all_steps(self):
        data = {
            'name': self.res.name,
            'researcherId': self.researcher_id,
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        verifPath = self.res.verificationpath.path

        data = {
            'verifPath': verifPath,
        }
        response = self.client.post('/api/v3/users/check_verif_path', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'verifPath': verifPath,
            'password': 'testpas'
        }
        response = self.client.post('/api/v3/users/change_password', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {
            'username': self.res.email,
            'password': 'testpas',
        }

        response = self.client.post(
            '/api/v3/users/login', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class UsersAPITest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super(UsersAPITest, cls).setUpClass()

        cls.res = WdaeUser.objects.create_user(email='fake@fake.com')
        cls.res.name = 'fname'
        cls.res.email = 'fake@fake.com'
        cls.res.is_active = True
        cls.res.save()

        cls.researcher_id = '11aa--bb'

        group_name = WdaeUser.get_group_name_for_researcher_id(
            cls.researcher_id)
        group, _ = Group.objects.get_or_create(name=group_name)
        group.user_set.add(cls.res)

    def test_invalid_verif_path(self):
        data = {
            'verifPath': 'dasdasdasdasdsa',
        }
        response = self.client.post('/api/v3/users/check_verif_path', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_pass(self):
        data = {
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/reset_password', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register_existing_user(self):
        data = {
            'name': self.res.name,
            'researcherId': self.researcher_id,
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserAuthenticationTest(APITestCase):

    def setUp(self):
        self.user = WdaeUser.objects.create_user(email='test@example.com')
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
