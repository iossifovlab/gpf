import re

EMAIL_REGEX = (
    r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@("
    r"[a-z0-9]([a-z0-9-]*[a-z0-9])*\.)+[a-z0-9]([a-z0-9-]*[a-z0-9])*")


def is_email_valid(email: str) -> bool:
    return bool(re.search(EMAIL_REGEX, email))
