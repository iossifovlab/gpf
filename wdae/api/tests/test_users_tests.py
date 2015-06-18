'''
Created on May 25, 2015

@author: lubo
'''
from django.test import TestCase
from api.models import WdaeUser, VerificationPath, Researcher
from django.contrib.auth import authenticate
from rest_framework.test import APITestCase
from rest_framework import status

class WdaeUserTestCase(TestCase):
    def setUp(self):
        self.user = WdaeUser.objects.create(email="test@example.com",
            first_name="Ivan",
            last_name="Testov",
            researcher_id="ala bala")

        self.user.set_password("pass")
        self.user.save()
        
    def test_user(self):
        user = self.user
        self.assertTrue(user)
        self.assertEquals("test@example.com", user.email)

    def test_verification_email(self):
        msg = self.user.email_user("Just Test", "Testing... Testing...")
        self.assertTrue(msg)

#     def test_create_superuser(self):
#         u = WdaeUser.objects.create(
#                 email="iossifov@cshl.edu",
#                 first_name="Ivan",
#                 last_name="Iossifov",
#                 researcher_id="1")
#         u.set_password("pasivan")
#         u.is_staff = True
#         
#         u.save()
#         
#         all_users = WdaeUser.objects.all()
#         user = all_users[1]
#         self.assertEqual("iossifov@cshl.edu", user.email)
#         self.assertTrue(user.is_staff)
#         self.assertEqual("Ivan", user.first_name)
#         self.assertEqual("Iossifov", user.last_name)
        
    def test_password_reset(self):
        u = authenticate(email='test@example.com', password='pass')
        self.assertTrue(u)

        user=self.user
        user.reset_password()
        self.assertTrue(user.verification_path)

        u = authenticate(email='test@example.com', password='pass')
        self.assertFalse(u)
        
        path = user.verification_path.path
        vp = VerificationPath.objects.get(path=path)
        u = WdaeUser.objects.get(verification_path=vp)
        self.assertTrue(u)
        self.assertEqual(user.id, u.id)
        
        WdaeUser.change_password(vp, "pass1")
        u = authenticate(email='test@example.com', password='pass')
        self.assertFalse(u)
        u = authenticate(email='test@example.com', password='pass1')
        self.assertEqual(user.id, u.id)
        
        
class SuperUserTestCase(TestCase):
    def setUp(self):
        self.user = WdaeUser.objects.create(email="test@example.com",
            first_name="Ivan",
            last_name="Testov",
            researcher_id="ala bala")
        self.user.is_staff = True
        self.user.set_password("pass")
        
        self.user.save()
        
    def test_user(self):
        user = self.user
        self.assertTrue(user)
        self.assertEquals("test@example.com", user.email)
        
    def test_password_reset(self):
        u = authenticate(email='test@example.com', password='pass')
        self.assertTrue(u)

        user=self.user
        user.reset_password()
        self.assertTrue(user.verification_path)
        
        u = authenticate(email='test@example.com', password='pass')
        self.assertFalse(u)

        path = user.verification_path.path
        vp = VerificationPath.objects.get(path=path)
        u = WdaeUser.objects.get(verification_path=vp)
        self.assertTrue(u)
        self.assertEqual(user.id, u.id)
        
        WdaeUser.change_password(vp, "pass1")
        u = authenticate(email='test@example.com', password='pass')
        self.assertFalse(u)
        u = authenticate(email='test@example.com', password='pass1')
        self.assertEqual(user.id, u.id)
        
        
class UserRegistrationTest(APITestCase):
    def test_fail_register(self):
        data = {
            'email': 'faulthymail@faulthy.com',
            'first_name': 'bad_first_name',
            'last_name': 'bad_last_name'
        }

        response = self.client.post('/api/users/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_register(self):
        res = Researcher()
        res.first_name = 'fname'
        res.last_name = 'lname'
        res.unique_number = '11aa--bb'
        res.email = 'fake@fake.com'
        res.save()

        data = {
            'first_name': res.first_name,
            'last_name': res.last_name,
            'researcher_id': res.unique_number,
            'email': res.email
        }

        response = self.client.post('/api/users/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['researcher_id'], res.unique_number)
        self.assertEqual(response.data['email'], res.email)

#     def test_ssc_query_variants_preview_security(self):
#         response = self.client.post('/api/ssc_query_variants_preview', {}, format="json")
#         # FIXME: unauthorized test
#         # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_query_variants_full_security(self):
        pass

    def test_query_variants_preview_full_security(self):
        pass    

class UserAuthenticationTest(APITestCase):
    def setUp(self):
        self.user = WdaeUser.objects.create(email="test@example.com",
            first_name="Ivan",
            last_name="Testov",
            researcher_id="ala bala")
        self.user.set_password("pass")
        self.user.is_active = True
        self.user.save()

    def test_successful_auth(self):
        data = {
            'username': 'test@example.com',
            'password': 'pass',
        }

        response = self.client.post('/api/users/api-token-auth', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failed_auth(self):
        data = {
            'username': 'bad@example.com',
            'password': 'pass'
        }

        response = self.client.post('/api/users/api-token-auth', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_auth(self):
        self.user.is_staff = True
        self.user.save()
        
        data = {
            'username': 'test@example.com',
            'password': 'pass',
        }

        response = self.client.post('/api/users/api-token-auth', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'token': response.data['token']
        }

        response = self.client.post('/api/users/get_user_info', data, format='json')
        self.assertEqual(response.data['userType'], 'admin')