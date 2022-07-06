import base64
import logging
import os
from oauth2_provider.models import get_application_model
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

logger = logging.getLogger(__name__)

User = get_user_model()
Application = get_application_model()

user = User.objects.get(id=1) # Get admin user, should be the first one

new_application = Application(**{
    "name": f"remote federation testing app",
    "user_id": user.id,
    "client_type": "confidential",
    "authorization_grant_type": "client-credentials",
    "client_id": "federation",
    "client_secret": "secret"
})

new_application.full_clean()
cleartext_secret = new_application.client_secret
new_application.save()

credentials = base64.b64encode(
    f"{new_application.client_id}:{cleartext_secret}".encode("utf-8")
)
# credentials should be always be the same
assert credentials == b'ZmVkZXJhdGlvbjpzZWNyZXQ=', credentials
logger.info(f"Set up federation app on remote with credentials: {credentials}")
