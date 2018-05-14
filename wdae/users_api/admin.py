from __future__ import absolute_import
from .models import WdaeUser, VerificationPath
from django.contrib import admin

admin.site.register(WdaeUser)
admin.site.register(VerificationPath)
