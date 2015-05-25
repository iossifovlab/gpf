'''
Created on May 25, 2015

@author: lubo
'''
from django.test import TestCase
from api.models import WdaeUser

class UserTestCase(TestCase):
    def setUp(self):
        self.user = WdaeUser.objects.create(email="iossifov@cshl.edu",
            first_name="Ivan",
            last_name="Iossifov",
            researcher_id="ala bala")
        
    def test_user(self):
        user = self.user
        self.assertTrue(user)
        self.assertEquals("iossifov@cshl.edu", user.email)

    def test_verification_email(self):
        msg = self.user.email_user("Just Test", "Testing... Testing...")
        self.assertTrue(msg)
        print(type(msg))
