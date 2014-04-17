from fabric.contrib.files import append, exists, sed, upload_template
from fabric.api import env, run, cd
from fabtools import apache, service
import random
import os

REPO_URL = "ssh://lubo@seqpipe.setelis.com:2020/SeqPipeline"


def staging():
    site_folder = '/home/%s/sites/%s' % (env.user, env.host)
    source_folder = os.path.join(site_folder, 'source')
    wdae_folder = os.path.join(source_folder, 'python/wdae')
    dae_folder = os.path.join(source_folder, 'python/DAE')
    data_folder = '/home/lubo/data-dev'

    print("site_folder: %s, source_folder: %s" % (site_folder, source_folder))

    # _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_source_consts(wdae_folder)
    _update_settings(site_folder, wdae_folder)
    _update_wsgi(site_folder, dae_folder, wdae_folder, data_folder)
    _update_static_files(wdae_folder)
    _update_vhost_conf(site_folder, wdae_folder)


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
        'STATIC_ROOT = "%s/"' % os.path.join(site_folder, 'static'))
    sed(settings_path,
        'STATIC_URL = .+$',
        'STATIC_URL = "/dae/static/"')

    secret_key_file = os.path.join(wdae_folder, 'wdae/secret_key.py')
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, 'SECRET_KEY = "%s"' % (key,))
    append(settings_path, '\nfrom .secret_key import SECRET_KEY')


def _update_source_consts(wdae_folder):
    jsconst_path = os.path.join(wdae_folder,
                                'variants/static/variants/js/constants.js')
    sed(jsconst_path, "/api/", "/dae/api/")


def _update_static_files(wdae_folder):
    with cd(wdae_folder):
        run('python manageWDAE.py collectstatic --noinput')

# VHOST_CONF = """
# <VirtualHost *:80>
#   ServerAdmin webmaster@mydomain.com
#   ServerName seqpipe-vm.setelis.com

#   WSGIScriptAlias /dae %s
#   WSGIApplicationGroup %{GLOBAL}

#   Alias /dae/static/ %s
#   <Location "/dae/static/">
#     Allow From All
#   </Location>

#   LogLevel debug
# </VirtualHost>
# """


def _update_vhost_conf(site_folder, wdae_folder):
    upload_template('confs/vhost.conf',
                    '/etc/apache2/sites-available/seqpipe.setelis.com.conf',
                    context={'wsgi_file': os.path.join(wdae_folder, 'wdae/index.wsgi'),
                             'static_folder': os.path.join(site_folder, 'static'),
                             'wdae_folder': wdae_folder},
                    use_sudo=True)
    apache.enable_module('wsgi')
    apache.enable_site('seqpipe.setelis.com')
    service.restart('apache2')


def _update_wsgi(site_folder, dae_folder, wdae_folder, data_folder):
    wsgi_file = os.path.join(wdae_folder, 'wdae/index.wsgi')
    upload_template('confs/index.wsgi',
                    wsgi_file,
                    context={'wsgi_file': wsgi_file,
                             'dae_folder': dae_folder,
                             'wdae_folder': wdae_folder,
                             'data_folder': data_folder})
    run('chmod +x %s' % wsgi_file)
