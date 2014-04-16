import os
import sys

# Add the app's directory to the PYTHONPATH
sys.path.append('%(wdae_folder)s')
sys.path.append('%(dae_folder)s')

os.environ['DJANGO_SETTINGS_MODULE'] = 'wdae.settings'
os.environ['DAE_DB_DIR'] = '%(data_folder)s'


import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


