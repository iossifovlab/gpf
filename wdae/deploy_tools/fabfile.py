from fabric.contrib.files import append, exists, sed, upload_template
from fabric.api import env, run, cd, local, put, sudo, path
from fabric.colors import green, yellow

# from fabtools import apache, service
import random
import os
from datetime import datetime

# APACHE_USER = 'www-data'
# APACHE_GROUP = 'www-data'

APACHE_USER = 'apache'
APACHE_GROUP = 'apache'

SITE_FOLDER = '/data/dae'

def deploy():
    site_folder = SITE_FOLDER
    source_folder = os.path.join(site_folder, 'SeqPipeline')
    wdae_folder = os.path.join(source_folder, 'python/wdae')
    
    # data_folder = '/home/lubo/data-dev'

    print("site_folder: %s, source_folder: %s" % (site_folder, source_folder))
    _create_directory_structure_if_necessary(site_folder)
    _backup_existing_source_dir(source_folder)
    _put_repository_tarball(site_folder)
    
    _patch_source_consts(wdae_folder)
    _patch_settings(site_folder, wdae_folder)

    _update_static_files(wdae_folder)

    run('/etc/init.d/httpd restart')

    # _update_wsgi(site_folder, dae_folder, wdae_folder, data_folder)
    # _update_vhost_conf(site_folder, wdae_folder)

def _create_directory_structure_if_necessary(site_folder):
    print(yellow("creating directory structure..."))
    static_dir = os.path.join(site_folder, 'static')
    log_dir = os.path.join(site_folder, 'logs')
    data_dir = os.path.join(site_folder, 'DAEDB')
    for folder in [static_dir, log_dir, data_dir]:
        if not exists(folder):
            run('mkdir -p %s' % folder)
    
def _backup_existing_source_dir(source_folder):
    print(yellow("backup source dir..."))
    if exists(source_folder):
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        source_folder_bak = '%s.%s' % (source_folder, timestamp)
        run('mv %s %s' % (source_folder, source_folder_bak))

def _put_repository_tarball(site_folder):
    print(yellow("put new source tarball..."))    
    local('hg archive -t tgz SeqPipeline.tar.gz')
    remote_tarball = os.path.join(site_folder, 'SeqPipeline.tar.gz')
    put('SeqPipeline.tar.gz', remote_tarball)
    with cd(site_folder):
        run('tar zxvf %s' % remote_tarball)

def _patch_source_consts(wdae_folder):
    print(yellow("patching constants.js file..."))    
    jsconst_path = os.path.join(wdae_folder,
                                'variants/static/variants/js/constants.js')
    # sed(jsconst_path, "/api/", "/dae-static/api/")
    sed(jsconst_path, "/api/", "/dae/api/")
    

def _patch_settings(site_folder, wdae_folder):
    print(yellow("patching settings.py file..."))    
    settings_path = os.path.join(wdae_folder, 'wdae/settings.py')
    static_path = os.path.join(site_folder, 'static')
    log_file = os.path.join(site_folder, 'logs/wdae-api.log')
    secret_key_file = os.path.join(wdae_folder, 'wdae/secret_key.py')
    
    sed(settings_path,
        "DEBUG = True",
        "DEBUG = False")
    sed(settings_path,
        "TEMPLATE_DEBUG =.+$",
        "DEBUG = False")
    
    sed(settings_path,
        "ALLOWED_HOSTS = .+$",
        'ALLOWED_HOSTS = ["wigserv2", "wigserv2.cshl.edu", "wigserv5", "wigserv5.cshl.edu",]')
    
    sed(settings_path,
        'TIME_ZONE = .+$',
        'TIME_ZONE = "America/Chicago"')
    
    sed(settings_path,
        'STATIC_ROOT = .+$',
        'STATIC_ROOT = "%s/"' % static_path)
    sed(settings_path,
        'STATIC_URL = .+$',
        'STATIC_URL = "/dae-static/"')

    _patch_settings_logfile(settings_path, log_file)
    _patch_settings_secret(settings_path, secret_key_file)
    

def _patch_settings_logfile(settings_path, log_file):
    sed(settings_path,
        'wdae-api.log',
        log_file)

    sudo('touch %s' % log_file)
    sudo('chown %s:%s %s' % (APACHE_USER, APACHE_GROUP, log_file))

def _patch_settings_secret(settings_path, secret_key_file):
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, 'SECRET_KEY = "%s"' % (key,))
        append(settings_path, '\nfrom .secret_key import SECRET_KEY')
    
def _update_static_files(wdae_folder):
    print(yellow("update static files..."))    
    with cd(wdae_folder), path('/data/software/local/bin',behavior='prepend'):
        run('python manageWDAE.py collectstatic --noinput')


# def _update_vhost_conf(site_folder, wdae_folder):
#     upload_template('confs/vhost.conf',
#                     '/etc/apache2/sites-available/seqpipe.setelis.com.conf',
#                     context={'wsgi_file': os.path.join(wdae_folder,
#                                                        'wdae/index.wsgi'),
#                              'static_folder': os.path.join(site_folder,
#                                                            'static'),
#                              'wdae_folder': wdae_folder},
#                     use_sudo=True)
#     apache.enable_module('wsgi')
#     apache.enable_site('seqpipe.setelis.com')
#     service.restart('apache2')


# def _update_wsgi(site_folder, dae_folder, wdae_folder, data_folder):
#     wsgi_file = os.path.join(wdae_folder, 'wdae/index.wsgi')
#     upload_template('confs/index.wsgi',
#                     wsgi_file,
#                     context={'wsgi_file': wsgi_file,
#                              'dae_folder': dae_folder,
#                              'wdae_folder': wdae_folder,
#                              'data_folder': data_folder})
#     run('chmod +x %s' % wsgi_file)
