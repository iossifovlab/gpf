import pytest

from django.core.urlresolvers import reverse


@pytest.fixture()
def save_endpoint():
    return reverse("save-query")


@pytest.fixture()
def load_endpoint():
    return reverse("load-query")
