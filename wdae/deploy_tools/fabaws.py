from fabric.contrib.files import append, exists, sed, upload_template
from fabric.api import env, run, cd, sudo, local, put
from fabric.colors import green, yellow, red

from fabtools import apache, service
import random
import os



def staging():
    site_folder = '/home/%s/sites/%s' % (env.user, env.host)
    source_folder = os.path.join(site_folder, 'source')
    wdae_folder = os.path.join(source_folder, 'python/wdae')
    dae_folder = os.path.join(source_folder, 'python/DAE')
    data_folder = '/home/lubo/data-dev'

    print("site_folder: %s, source_folder: %s" % (site_folder, source_folder))

    _create_directory_structure_if_necessary(site_folder)
    _put_repository_tarball(site_folder, source_folder)
    
    _update_source_consts(wdae_folder)
    _update_settings(site_folder, wdae_folder)
    _update_wsgi(site_folder, dae_folder, wdae_folder, data_folder)
    _update_static_files(wdae_folder)
    _update_settings_logfile(site_folder, wdae_folder)
    _update_vhost_conf(site_folder, wdae_folder)


def _create_directory_structure_if_necessary(site_folder):
    for subfolder in ('database', 'static', 'source', 'logs'):
        run('mkdir -p %s/%s' % (site_folder, subfolder))


def _put_repository_tarball(site_folder, source_folder):
    print(yellow("put new source tarball..."))    
    local('hg archive -t tgz SeqPipeline.tar.gz')
    remote_tarball = os.path.join(site_folder, 'SeqPipeline.tar.gz')
    put('SeqPipeline.tar.gz', remote_tarball)
    with cd(site_folder):
        run('tar zxvf %s -C %s --strip-components=1' %(remote_tarball, source_folder))

        
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


def _update_settings_logfile(site_folder, wdae_folder):
    settings_path = os.path.join(wdae_folder, 'wdae/settings.py')
    logs_path = os.path.join(site_folder, 'logs/wdae-apt.log')
    sed(settings_path,
        'wdae-api.log',
        logs_path)
    sudo('touch %s' % logs_path)
    sudo('chown www-data:www-data %s' % logs_path)
    
def _update_source_consts(wdae_folder):
    jsconst_path = os.path.join(wdae_folder,
                                'variants/static/variants/js/constants.js')
    sed(jsconst_path, "/api/", "/api/")


def _update_static_files(wdae_folder):
    with cd(wdae_folder):
        run('python manageWDAE.py collectstatic --noinput')


def _update_vhost_conf(site_folder, wdae_folder):
    upload_template('confs/iossifovlab.conf',
                    '/etc/apache2/sites-available/iossifovlab.com.conf',
                    context={'wsgi_file': os.path.join(wdae_folder,
                                                       'wdae/index.wsgi'),
                             'static_folder': os.path.join(site_folder,
                                                           'static'),
                             'wdae_folder': wdae_folder},
                    use_sudo=True)
    apache.enable_module('wsgi')
    apache.enable_site('iossifovlab.com')
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
