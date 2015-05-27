'''
Created on May 25, 2015

@author: lubo
'''
from django.test import TestCase
from api.models import WdaeUser, VerificationPath
from django.contrib.auth import authenticate

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
        print(type(msg))

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
        
        