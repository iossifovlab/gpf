from functools import wraps
from django.conf import settings
from oauth2_provider.models import get_application_model


LOCKOUT_THRESHOLD = 4


def csrf_clear(view_func):
    """Skips the CSRF checks by setting the 'csrf_processing_done' to true."""

    def wrapped_view(*args, **kwargs):
        request = args[0]
        request.csrf_processing_done = True
        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapped_view)


def get_default_application():
    client_id = settings.DEFAULT_OAUTH_APPLICATION_CLIENT
    model = get_application_model()
    return model.objects.get(client_id=client_id)


def send_verif_email(user, verif_path):
    email = _create_verif_email(
        settings.EMAIL_HOST,
        settings.EMAIL_SET_PATH,
        str(verif_path.path),
    )
    user.email_user(email["subject"], email["message"])


def send_already_existing_email(user):
    subject = "GPF: Attempted registration with email in use"
    message = (
        "Hello. Someone has attempted to create an account in GPF "
        "using an email that your account was registered with.  "
        "If this was you, you can simply log in to your existing account, "
        "or if you've forgotten your password, you can reset it "
        "by using the 'Forgotten password' button on the login window. \n"
        "Otherwise, please ignore this email."
    )
    user.email_user(subject, message)


def send_reset_inactive_acc_email(user):
    subject = "GPF: Password reset for inactive account"
    message = (
        "Hello. You've requested a password reset for an inactive account. "
        "You must first finish your registration by following the "
        "account validation link in the email you received when registering. "
        "If you have lost that email or the link in it has expired, you can "
        "register again to get a new validation email sent. \n"
        "If you did not request this, please ignore this email."
    )
    user.email_user(subject, message)


def send_reset_email(user, verif_path, by_admin=False):
    """Return dict with subject and message of the email."""
    email = _create_reset_mail(
        settings.EMAIL_HOST,
        settings.EMAIL_RESET_PATH,
        str(verif_path.path),
        by_admin,
    )

    user.email_user(email["subject"], email["message"])


def _create_verif_email(host, path, verification_path):
    message = (
        "Welcome to GPF: Genotype and Phenotype in Families! "
        "Follow the link below to validate your new account "
        "and set your password:\n {link}"
    )

    settings = {
        "subject": "GPF: Registration validation",
        "initial_message": message,
        "host": host,
        "path": path,
        "verification_path": verification_path,
    }

    return _build_email_template(settings)


def _create_reset_mail(host, path, verification_path, by_admin=False):
    message = (
        "Hello. You have requested to reset your password for "
        "your GPF account. To do so, please follow the link below:\n {link}\n"
        "If you did not request for your GPF account password to be reset, "
        "please ignore this email."
    )
    if by_admin:
        message = (
            "Hello. Your password has been reset by an admin. Your old "
            "password will not work. To set a new password in "
            "GPF: Genotype and Phenotype in Families "
            "please follow the link below:\n {link}"
        )
    settings = {
        "subject": "GPF: Password reset request",
        "initial_message": message,
        "host": host,
        "path": path,
        "verification_path": verification_path,
    }

    return _build_email_template(settings)


def _build_email_template(settings):
    subject = settings["subject"]
    message = settings["initial_message"]
    path = settings["path"].format(settings["verification_path"])

    message = message.format(link="{0}{1}".format(settings["host"], path))

    return {"subject": subject, "message": message}
