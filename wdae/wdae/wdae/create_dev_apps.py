# To create the dev apps, run the following command:
# wdaemanage.py shell < create_dev_apps.py

import os
from oauth2_provider.models import get_application_model  # type: ignore
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wdae.settings")

gpfjs_url = os.environ.get("GPFJS_URL", "http://localhost:4200")

User = get_user_model()
Application = get_application_model()

user = User.objects.get(id=1)  # Get admin user, should be the first one

new_application = Application(**{
    "name": "gpfjs dev app",
    "user_id": user.id,
    "client_type": "public",
    "authorization_grant_type": "authorization-code",
    "redirect_uris": f"{gpfjs_url}/datasets",
    "client_id": "gpfjs",
})
new_application.full_clean()
new_application.save()

# gpfjs_frontpage_url = os.environ.get(
#     "GPFJS_FRONTPAGE_URL", "http://localhost:9000/frontpage_prefix"
# )

# new_application = Application(**{
#     "name": "gpfjs frontpage dev app",
#     "user_id": user.id,
#     "client_type": "public",
#     "authorization_grant_type": "authorization-code",
#     "redirect_uris": f"{gpfjs_frontpage_url}",
#     "client_id": "gpfjs-frontpage",
# })
# new_application.full_clean()
# new_application.save()
