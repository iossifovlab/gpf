from users.models import WdaeUser, Researcher, ResearcherId, VerificationPath
from django.contrib import admin

admin.site.register(WdaeUser)
admin.site.register(Researcher)
admin.site.register(ResearcherId)
admin.site.register(VerificationPath)
