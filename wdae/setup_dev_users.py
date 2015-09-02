#!/usr/bin/env python

import os
import sys


# Add the project directory to system path
proj_dir = os.path.expanduser('./wdae')

sys.path.append(proj_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wdae.default_settings")

from django.contrib.auth import get_user_model

User = get_user_model()
u, _ = User.objects.get_or_create(email='admin@iossifovlab.com')
u.is_staff = True
u.is_active = True

u.set_password('secret')
u.save()


u, _ = User.objects.get_or_create(email='research@iossifovlab.com')
u.is_staff = False
u.is_active = True
u.researcher_id = '10001'
u.set_password('secret')
u.save()
