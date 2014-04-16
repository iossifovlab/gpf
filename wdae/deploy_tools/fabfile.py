from fabric.contrib.files import append, exists, sed
from fabric.api import env, run, cd
import random
import os

REPO_URL = "ssh://lubo@seqpipe.setelis.com:2020/SeqPipeline"


def staging():
    site_folder = '/home/%s/sites/%s' % (env.user, env.host)
    source_folder = os.path.join(site_folder, 'source')
    wdae_folder = os.path.join(source_folder, 'python/wdae')

    print("site_folder: %s, source_folder: %s" % (site_folder, source_folder))

    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_settings(site_folder, wdae_folder)
    _update_static_files(wdae_folder)


def _create_directory_structure_if_necessary(site_folder):
    for subfolder in ('database', 'static', 'virtualenv', 'source'):
        run('mkdir -p %s/%s' % (site_folder, subfolder))


def _get_latest_source(source_folder):
    if exists(os.path.join(source_folder, '.hg')):
        with cd(source_folder):
            run('hg pull')
    else:
        run('hg clone %s %s' % (REPO_URL, source_folder))

    with cd(source_folder):
        run('hg up --clean')


def _update_settings(site_folder, wdae_folder):
    settings_path = os.path.join(wdae_folder, 'wdae/settings.py')
    sed(settings_path, "DEBUG = True", "DEBUG = False")
    sed(settings_path,
        "ALLOWED_HOSTS = .+$",
        'ALLOWED_HOSTS = ["seqpipe-vm.setelis.com", "seqpipe.setelis.com"]')
    sed(settings_path,
        'TIME_ZONE = .+$',
        'TIME_ZONE = "Europe/Sofia"')
    sed(settings_path,
        'STATIC_ROOT = .+$',
        'STATIC_ROOT = "%s"' % os.path.join(site_folder, 'static'))

    secret_key_file = os.path.join(wdae_folder, 'wdae/secret_key.py')
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, 'SECRET_KEY = "%s"' % (key,))
    append(settings_path, '\nfrom .secret_key import SECRET_KEY')


def _update_static_files(source_folder):
    with cd(source_folder):
        run('python manageWDAE.py collectstatic --noinput')
