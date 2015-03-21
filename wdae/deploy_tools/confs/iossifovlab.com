<VirtualHost *:80>
  ServerAdmin admin@iossifov.com
  ServerName iossifovlab.com

  WSGIScriptAlias / %(wsgi_file)s
  WSGIApplicationGroup %%{GLOBAL}

  Alias /static/ %(static_folder)s/
  <Location "/dae/static/">
    Allow From All
  </Location>

  <Directory %(wdae_folder)s/>
    Options FollowSymLinks
    AllowOverride None
    Require all granted
    Deny from All
  </Directory>


  <Directory %(static_folder)s/>
    Options FollowSymLinks
    AllowOverride None
    Require all granted
    Allow from All
  </Directory>


  <Files %(wsgi_file)s>
    Allow from All
  </Files>

  <Location "/dae">
    Allow from All
  </Location>

  LogLevel debug
</VirtualHost>
