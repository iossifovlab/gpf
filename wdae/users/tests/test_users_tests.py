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


class Test(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()

        User = get_user_model()
        u = User.objects.create(email="admin@example.com",
                                first_name="First",
                                last_name="Last",
                                is_staff=True,
                                is_active=True)
        u.set_password("secret")
        u.save()

        cls.user = u
        _token = Token.objects.get_or_create(user=u)
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        super(Test, cls).tearDownClass()

        cls.user.delete()

    def setUp(self):
        super(Test, self).setUpClass()

        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_user(self):
        user = self.user
        self.assertTrue(user)
        self.assertEquals("admin@example.com", user.email)

    def test_verification_email(self):
        msg = self.user.email_user("Just Test", "Testing... Testing...")
        self.assertTrue(msg)

    def test_create_superuser(self):
        u = WdaeUser.objects.create(
            email="iossifov@cshl.edu",
            first_name="Ivan",
            last_name="Iossifov")
        u.set_password("pasivan")
        u.is_staff = True
        u.is_superuser = True

        u.save()

        user = WdaeUser.objects.get(email="iossifov@cshl.edu")
        self.assertEqual("iossifov@cshl.edu", user.email)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual("Ivan", user.first_name)
        self.assertEqual("Iossifov", user.last_name)

    def test_password_reset(self):
        u = authenticate(email='admin@example.com', password='secret')
        self.assertTrue(u)

        user = self.user
        user.reset_password()
        self.assertTrue(user.verificationpath)

        u = authenticate(email='admin@example.com', password='secret')
        self.assertFalse(u)

        path = user.verificationpath.path
        vp = VerificationPath.objects.get(path=path)
        u = vp.user
        self.assertTrue(u)
        self.assertEqual(user.id, u.id)

        WdaeUser.change_password(vp, "pass1")
        u = authenticate(email='admin@example.com', password='secret')
        self.assertFalse(u)
        u = authenticate(email='admin@example.com', password='pass1')
        self.assertEqual(user.id, u.id)


class SuperUserTestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(SuperUserTestCase, cls).setUpClass()

        User = get_user_model()
        u = User.objects.create(email="admin@example.com",
                                first_name="First",
                                last_name="Last",
                                is_staff=True,
                                is_active=True,
                                is_superuser=True)
        u.set_password("secret")
        u.save()

        cls.user = u
        _token = Token.objects.get_or_create(user=u)
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        super(SuperUserTestCase, cls).tearDownClass()

        cls.user.delete()

    def setUp(self):
        super(SuperUserTestCase, self).setUpClass()

        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_user(self):
        user = self.user
        self.assertTrue(user)
        self.assertEquals("admin@example.com", user.email)

    def test_password_reset(self):
        u = authenticate(email='admin@example.com', password='secret')
        self.assertTrue(u)

        user = self.user
        user.reset_password()
        self.assertTrue(user.verificationpath)

        u = authenticate(email='admin@example.com', password='secret')
        self.assertFalse(u)

        path = user.verificationpath.path
        vp = VerificationPath.objects.get(path=path)
        u = vp.user
        self.assertTrue(u)
        self.assertEqual(user.id, u.id)

        WdaeUser.change_password(vp, "pass1")
        u = authenticate(email='admin@example.com', password='pass')
        self.assertFalse(u)
        u = authenticate(email='admin@example.com', password='pass1')
        self.assertEqual(user.id, u.id)


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
            'first_name': 'bad_first_name',
            'last_name': 'bad_last_name'
        }

        response = self.client.post('/api/users/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_register(self):
        [id1] = self.res.researcherid_set.all()
        data = {
            'first_name': self.res.first_name,
            'last_name': self.res.last_name,
            'researcher_id': id1.researcher_id,
            'email': self.res.email
        }
        pprint(data)

        response = self.client.post('/api/users/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['researcher_id'], id1.researcher_id)
        self.assertEqual(response.data['email'], self.res.email)


class ResearcherWithTwoIdsRegistrationTest(APITestCase):

    def setUp(self):
        super(ResearcherWithTwoIdsRegistrationTest, self).setUp()

        self.res = WdaeUser()
        self.res.first_name = 'fname'
        self.res.last_name = 'lname'
        self.res.email = 'fake@fake.com'
        self.res.save()

        self.research_id1 = ResearcherId()
        self.research_id1.researcher_id = '101.1'
        self.research_id1.save()

        self.research_id1.researcher.add(self.res)

        self.research_id2 = ResearcherId()
        self.research_id2.researcher_id = '101.2'
        self.research_id2.save()

        self.research_id2.researcher.add(self.res)

    def tearDown(self):
        super(ResearcherWithTwoIdsRegistrationTest, self).tearDown()
        self.res.delete()
        users = WdaeUser.objects.filter(email='fake@fake.com')
        for u in users:
            u.delete()

    def test_successful_register1(self):
        data = {
            'first_name': 'fname',
            'last_name': 'lname',
            'researcher_id': '101.1',
            'email': 'fake@fake.com',
        }

        response = self.client.post('/api/users/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['researcher_id'], '101.1')
        self.assertEqual(response.data['email'], 'fake@fake.com')

        [user] = WdaeUser.objects.filter(email='fake@fake.com')

        self.assertEquals('fname', user.first_name)
        self.assertEquals('lname', user.last_name)
        self.assertEquals('fake@fake.com', user.email)
        self.assertIn('101.1',
            user.researcherid_set.values_list('researcher_id', flat=True).all())

    def test_successful_register2(self):
        data = {
            'first_name': 'fname',
            'last_name': 'lname',
            'researcher_id': '101.2',
            'email': 'fake@fake.com',
        }

        response = self.client.post('/api/users/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['researcher_id'], '101.2')
        self.assertEqual(response.data['email'], 'fake@fake.com')

        [user] = WdaeUser.objects.filter(email='fake@fake.com')

        self.assertEquals('fname', user.first_name)
        self.assertEquals('lname', user.last_name)
        self.assertEquals('fake@fake.com', user.email)
        self.assertIn('101.2',
            user.researcherid_set.values_list('researcher_id', flat=True).all())


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
            '/api/users/api-token-auth', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failed_auth(self):
        data = {
            'username': 'bad@example.com',
            'password': 'pass'
        }

        response = self.client.post(
            '/api/users/api-token-auth', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_auth(self):
        self.user.is_staff = True
        self.user.save()

        data = {
            'username': 'test@example.com',
            'password': 'pass',
        }

        response = self.client.post(
            '/api/users/api-token-auth', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'token': response.data['token']
        }

        response = self.client.post(
            '/api/users/get_user_info', data, format='json')
        self.assertEqual(response.data['userType'], 'admin')
