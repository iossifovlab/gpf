from users_api.models import WdaeUser
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

    def test_fail_register_wrong_id(self):
        data = {
            'email': self.res.email,
            'name': 'ok name',
            'researcherId': 'bad id',
        }

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error_msg'],
                         'Email or Researcher Id not found')

    def test_fail_register_wrong_email(self):
        data = {
            'email': 'bad@email.com',
            'name': 'ok name',
            'researcherId': self.researcher_id,
        }

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error_msg'],
                         'Email or Researcher Id not found')

    def test_reset_pass_without_registration(self):
        data = {
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/reset_password', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error_msg'],
                         'User with this email is approved for registration. '
                         'Please, register first')

    def test_reset_pass_without_registration_wrong_email(self):
        data = {
            'email': 'wrong@email.com'
        }
        pprint(data)

        response = self.client.post('/api/v3/users/reset_password', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error_msg'],
                         'User with this email not found')

    def test_successful_register(self):
        name = "NEW_NAME"
        data = {
            'name': name,
            'researcherId': self.researcher_id,
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        u = WdaeUser.objects.get(email=self.res.email)
        self.assertEqual(u.name, name)

    def test_successful_register_empty_name(self):
        old_name = self.res.name
        data = {
            'name': '',
            'researcherId': self.researcher_id,
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        u = WdaeUser.objects.get(email=self.res.email)
        self.assertEqual(u.name, old_name)

    def test_successful_register_missing_name(self):
        old_name = self.res.name
        data = {
            'researcherId': self.researcher_id,
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/v3/users/register', data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        u = WdaeUser.objects.get(email=self.res.email)
        self.assertEqual(u.name, old_name)

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
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error_msg'], 'User already exists')


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


class UserGroups(APITestCase):

    def setUp(self):
        self.user = WdaeUser.objects.create_user(email='test@example.com')
        self.user.set_password("pass")
        self.user.is_active = True
        self.user.save()

        self.admin_group = Group.objects.create(name=WdaeUser.SUPERUSER_GROUP)

    def test_without_admin_group_does_not_have_is_staff(self):
        assert not self.user.is_staff

    def test_adding_admin_group_sets_is_staff(self):
        self.user.groups.add(self.admin_group)

        assert self.user.is_staff

    def test_removing_admin_group_unsets_is_staff(self):
        self.user.groups.add(self.admin_group)

        self.user.groups.remove(self.admin_group)
        assert not self.user.is_staff

    def test_deleting_some_group_does_not_break_is_staff(self):
        group = Group.objects.create(name="Some Other Group1")

        assert not self.user.is_staff
        self.user.groups.add(self.admin_group)
        assert self.user.is_staff

        group.delete()
        assert self.user.is_staff

    def test_deleting_admin_group_unsets_is_staff(self):
        self.user.groups.add(self.admin_group)
        self.admin_group.delete()

        self.user.refresh_from_db()
        assert not self.user.groups.filter(name=WdaeUser.SUPERUSER_GROUP)\
            .exists()
        assert not self.user.is_staff

    def test_adding_through_admin_group_sets_is_staff(self):
        self.admin_group.user_set.add(self.user)

        self.user.refresh_from_db()

        assert self.user.is_staff

    def test_adding_multiple_users_through_admin_group_sets_is_staff(self):
        other_user = WdaeUser.objects.create(email="email@test.com")
        self.admin_group.user_set.add(self.user, other_user)

        self.user.refresh_from_db()
        other_user.refresh_from_db()

        assert self.user.is_staff
        assert other_user.is_staff
