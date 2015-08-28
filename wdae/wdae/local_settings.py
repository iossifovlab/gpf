from django.conf import settings

settings.INSTALLED_APPS += [
    'transmitted',
    'django_nose',
]

# Use nose to run all tests
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'foo' and 'bar' apps
NOSE_ARGS = [
             # '--with-coverage',
             # '--cover-package=api',
             '--verbosity=2',
]
