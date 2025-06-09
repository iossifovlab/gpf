Publicly Accessible GPF Site
============================

Requirements for the host
-------------------------

The recommended minimum requirements for the host are:

- 2 CPUs cores
- 4 GB RAM
- 25 GB disk space
- public IP address

Depending on the number of users and the amount of data, you may need to
increase these values.

You also need to have root access to the host to install and configure
the required software.

DNS name
--------

To set up a publicly accessible GPF, you need to have a DNS name that points to
the public IP address of the host.

In the example below, we will use ``demo.iossifovlab.com`` as the DNS name.


Firewall
--------

You should open the following ports on the firewall:

.. csv-table::
   :header-rows: 1

    Type,Protocol,Port,Description
    ICMP,ICMP,,Allow ping
    TCP,TCP,22,SSH
    TCP,TCP,80,HTTP
    TCP,TCP,443,HTTPS


Required Software
-----------------

Apache2 web server
^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    sudo apt-get install apache2
    sudo a2enmod proxy
    sudo a2enmod proxy_http
    sudo a2enmod ssl
    sudo a2enmod headers
    sudo a2enmod rewrite


Docker
^^^^^^

To install Docker, follow the instructions in the official Docker
documentation for your operating system. For example, on Ubuntu, you can
look at the following link:
https://docs.docker.com/engine/install/ubuntu/


SSL Certificate
---------------

For a publicly accessible GPF, you need to have a valid SSL certificate
for the DNS name. We recommend using a free SSL certificate from Let's Encrypt.

Create an virtual host configuration file for the Apache2 web server to
serve the demo domain over HTTPS. For example, for our demo domain
``demo.iossifovlab.com``, you can create a file
``/etc/apache2/sites-available/demo.iossifovlab.com.conf`` with the following
conteint:

.. code-block:: shell
    :linenos:

    LoadModule ssl_module /usr/lib/apache2/modules/mod_ssl.so

    <VirtualHost *:443>
        ServerName demo.iossifovlab.com
        ServerAdmin admin@iossifovlab.com

        LogLevel info ssl:warn

        DocumentRoot /var/www/html

    </VirtualHost>


To install the SSL certificate, you can use the instructions from
https://certbot.eff.org. For example, on Ubuntu with install Apache2 web
server, you can check the following link:
https://certbot.eff.org/instructions?ws=apache&os=snap

In our case, we used:

.. code-block:: shell
    :linenos:

    certbot run --apache -d demo.iossifovlab.com

This will install the SSL certificate and configure the Apache2 web server
to serve the demo domain over HTTPS. The Apache2 configuration file
``/etc/apache2/sites-available/demo.iossifovlab.com.conf`` will be similar to
the following:

.. code-block:: shell
    :linenos:

    LoadModule ssl_module /usr/lib/apache2/modules/mod_ssl.so

    <VirtualHost *:443>
        ServerName demo.iossifovlab.com
        ServerAdmin admin@iossifovlab.com

        LogLevel info ssl:warn

        DocumentRoot /var/www/html

        ### Added by Let's Encrypt certbot
        SSLCertificateFile /etc/letsencrypt/live/demo.iossifovlab.com/fullchain.pem
        SSLCertificateKeyFile /etc/letsencrypt/live/demo.iossifovlab.com/privkey.pem
        Include /etc/letsencrypt/options-ssl-apache.conf
        SessionCryptoPassphrase Di3ahti8oophushiePh0vang2ri2AeK0maetha7loz2Waleez2

    </VirtualHost>


Create an installation user
---------------------------

We recommend creating a user that will be used to install and configure GPF.
Let's say our user is called ``gpfdemo``. You can create the user with the
following command:

.. code-block:: shell

    adduser gpfdemo

We need this user to be able to run Docker commands without
``sudo``. To do this, you can add the user to the ``docker`` group:

.. code-block:: shell

    usermod -aG docker gpfdemo

Then, you can switch to the ``gpfdemo`` user:

.. code-block:: shell

    su - gpfdemo

Make sure to add your SSH public key to the ``gpfdemo`` user's
``~/.ssh/authorized_keys`` file so you can log in to the host using SSH.


Directory Structure
-------------------

In the following example, we will assume that we install GPF in a subdirectory
``demo`` of the home directory of the user ``gpfdemo``. We will use the
following directory structure:

.. code-block:: text

    demo
    ├── docker-compose.yaml
    ├── grr
    │   ├── cache
    │   └── grr_definition.yaml
    ├── logs
    │   ├── access.log
    │   ├── error.log
    │   └── wdae-debug.log
    ├── minimal_instance
    │   ├── gpf_instance.yaml
    │   ├── ...
    │   └── ...
    └── mysql_data
        ├── ...

- ``docker-compose.yaml``: Docker Compose file to start GPF;
- ``grr``: directory with GRR definition file and cache;
- ``logs``: directory to store the logs;
- ``minimal_instance``: directory with the GPF instance configuration;
- ``mysql_data``: directory to store the MySQL data.


GRR Definition File
-------------------

.. code-block:: yaml
    :linenos:

    id: public
    type: "http"
    url: "https://grr.iossifovlab.com"
    cache_dir: /grr/cache


GPF Instance Directory
----------------------

For our example, we will use the GPF instance configuration and data created
in the :ref:`GPF Getting Started Guide` section. We need to copy the whole
``minimal_instance`` directory to the GPF instance public host
``/demo/minimal_instance`` directory. To this end, you can use ``rsync`` or
``scp`` command. We will use the ``rsync`` command in the following example.
Our example host is ``demo.iossifovlab.com`` and the user is ``root``. So our
command will look like this:

.. code-block:: shell

    rsync -av minimal_instance gpfdemo@demo.iossifovlab.com:demo/


.. note::

    You should change the ``demo.iossifovlab.com`` and ``gpfdemo`` to your own
    values.



GPF Docker Compose File
-----------------------

To run GPF, we are going to use
`Docker Compose commands <https://docs.docker.com/compose/>`_.
The following is an example of a Docker Compose configuration file you cat use
to run GPF:

.. code-block:: yaml
    :linenos:

    services:
        mysqldata:
            image: busybox:latest
            command: echo "mysql data only container"
            volumes:
            - ./mysql_data:/var/lib/mysql

        mysql:
            image: mysql:8.0
            hostname: mysql
            environment:
            - MYSQL_DATABASE=gpf_demo
            - MYSQL_USER=seqpipe
            - MYSQL_PASSWORD=AhWeez0rooGaiheTh5zei8qui
            - MYSQL_ROOT_PASSWORD=Uor2thiwou3shooxahngah0oc
            volumes_from:
            - mysqldata
            networks:
                main:
                    aliases:
                    - mysql

            command: ['mysqld', '--character-set-server=utf8', '--collation-server=utf8_bin', '--default-authentication-plugin=mysql_native_password']

        gpf:
            image: iossifovlab/iossifovlab-gpf-full:latest
            hostname: gpf
            ports:
            - "8000:80"
            networks:
                main:
                    aliases:
                    - gpf
            volumes:
            - ./minimal_instance:/data
            - ./grr:/grr
            - ./logs:/logs
            environment:
            - DAE_DB_DIR=/data
            - DAE_PHENODB_DIR=/data/pheno
            - GRR_DEFINITION_FILE=/grr/grr_definition.yaml
            - WDAE_DB_NAME=gpf_demo
            - WDAE_DB_USER=seqpipe
            - WDAE_DB_PASSWORD=AhWeez0rooGaiheTh5zei8qui
            - WDAE_DB_HOST=mysql
            - WDAE_DB_PORT=3306
            - WDAE_SECRET_KEY="Di3ahti8oophushiePh0vang2ri2AeK0maetha7loz2Waleez2"
            - WDAE_PUBLIC_HOSTNAME=demo.iossifovlab.com
            - WDAE_ALLOWED_HOST=demo.iossifovlab.com
            - WDAE_LOG_DIR=/logs
            - GPF_PREFIX=gpf
            - WDAE_PREFIX=gpf

        networks:
            main:


.. warning::

    The above example is for demonstration purposes only. You should
    change the passwords and other parameters to your own values. The
    passwords should be strong and not easily guessable.


Start GPF
---------

We are going to use `Docker Compose <https://docs.docker.com/compose/>`_
to run GPF. To start the GPF instance and the MySQL database server, you can
use the following command:

.. code-block:: shell

    cd demo
    docker compose up -d

To inspect the logs, you can use the following command:

.. code-block:: shell

    docker compose logs -f

You can check the status of the containers using the following command:

.. code-block:: shell

    docker compose ps

If you want to enter the GPF container, you can use the following command:

.. code-block:: shell

    docker compose exec -it gpf /bin/bash


Create GPF Admin User and OAuth2 Application
--------------------------------------------

When you start the GPF instance for the first time, you need to create
an admin user and an OAuth2 application. To do this, you need to enter
the GPF container:

.. code-block:: shell

    docker compose exec -it gpf /bin/bash

Then, from inside the GPF container, you can use the following command to
create the admin user:

.. code-block:: shell
    :linenos:

    wdaemanage.py user_create admin@iossifovlab.com \
        -p xiequ6aZoNawaet7shooFam1A \
        -g any_dataset:admin

.. warning::

    The above command will create a user with the email
    ``admin@iossifovlab.com`` and the password
    ``xiequ6aZoNawaet7shooFam1A``.
    You should change the email and the password to your own values.

GPF uses OAuth2 for authentication.
Once the user is created, you have to create an OAuth2 application using the
following command:

.. code-block:: shell
    :linenos:

    wdaemanage.py createapplication --user 1 \
        --redirect-uris "https://demo.iossifovlab.com/gpf/login" \
        --name "GPF Genotypes and Phenotypes in Families" \
        --client-id gpfjs public authorization-code \
        --skip-authorization


.. warning::

    The above command will create an OAuth2 application with the
    redirect URI
    ``https://demo.iossifovlab.com/gpf/login``.
    You should change the domain name in the redirect URI to your own value.


Apache2 Proxy Configuration
---------------------------

Finally, you need to configure the Apache2 web server to proxy the requests
to the GPF instance. You can use the following configuration as an example:


.. code-block:: shell
    :linenos:

    LoadModule proxy_module /usr/lib/apache2/modules/mod_proxy.so
    LoadModule proxy_http_module /usr/lib/apache2/modules/mod_proxy_http.so
    LoadModule rewrite_module /usr/lib/apache2/modules/mod_rewrite.so
    LoadModule ssl_module /usr/lib/apache2/modules/mod_ssl.so

    <VirtualHost *:443>
        ServerName demo.iossifovlab.com
        ServerAdmin webmaster@localhost

        LogLevel info ssl:warn

        RedirectMatch ^/$ /gpf/
        <Location "/gpf">
            Allow From All
            ProxyPass "http://localhost:8000/gpf"
            ProxyPassReverse "http://localhost:8000/gpf"
            ProxyPreserveHost On
        </Location>

        ### Added by Let's Encrypt certbot
        SSLCertificateFile /etc/letsencrypt/live/demo.iossifovlab.com/fullchain.pem
        SSLCertificateKeyFile /etc/letsencrypt/live/demo.iossifovlab.com/privkey.pem
        Include /etc/letsencrypt/options-ssl-apache.conf
        SessionCryptoPassphrase Di3ahti8oophushiePh0vang2ri2AeK0maetha7loz2Waleez2

    </VirtualHost>

