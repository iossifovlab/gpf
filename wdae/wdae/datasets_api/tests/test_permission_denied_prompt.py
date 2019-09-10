import os
import pytest
from box import Box
from datasets_api.studies_manager import StudiesManager
from .conftest import fixtures_dir


def test_missing_permission_denied_prompt(dae_config_fixture):
    sm = StudiesManager(dae_config_fixture)
    assert sm.get_permission_denied_prompt() == \
        ('This is a default permission denied prompt.'
         ' Please log in or register.')


def test_permission_denied_prompt_from_file(dae_config_fixture):
    filepath = os.path.join(fixtures_dir(), 'permissionDeniedPrompt.md')
    dae_config_fixture.gpfjs = Box()
    dae_config_fixture.gpfjs.permission_denied_prompt = filepath

    sm = StudiesManager(dae_config_fixture)
    assert sm.get_permission_denied_prompt() == \
        ('This is a real permission denied prompt.'
         ' The StudiesManager has successfully loaded the file.\n')


def test_permission_denied_prompt_from_nonexistent_file(dae_config_fixture):
    filepath = os.path.join(fixtures_dir(), 'nonExistentFile.someFormat')
    dae_config_fixture.gpfjs = Box()
    dae_config_fixture.gpfjs.permission_denied_prompt = filepath

    with pytest.raises(AssertionError):
        sm = StudiesManager(dae_config_fixture)
        sm.get_permission_denied_prompt()
