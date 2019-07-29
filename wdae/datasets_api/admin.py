from datasets_api.models import Dataset
from django.contrib import admin
from guardian.admin import GuardedModelAdmin

admin.site.register(Dataset, GuardedModelAdmin)
