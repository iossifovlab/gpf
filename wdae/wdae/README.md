# How to Run Development Environment


## Automation of Reseting Development DB

To reset development environment use scrip `reset_dev.sh` located in 
`SeqPipeline/python/wdae`.

	cd SeqPipeline/python/wdae
	./reset_dev.sh
	
This script will:

* remove development data base (if one exists);
* create fresh empty data base
* create fresh admin user `admin@iossifovlab.com` with password `secret`
* create fresh research user `research@iossifovlab.com` with password `secret`.

Individual steps of this script are described bellow.

## Create DB

Go into `SeqPipeline/python/wdae` directory and run

	python manage.py syncdb
	
This creates new `sqlite3` database, that is used for development
purposes. This is embeded database, and it's database file is named
`wdae.sql` created in this directory.

## Run DB Migrations

To handle changes into DB model are used migrations. To run migrations
run following command:

	python manage.py migrate
	
## Create Default Development Users

To create development users use `setup_dev_users.py` script. 

	python setup_dev_users.py
	
This script creates admin and research users with following credentials:

* admin

	user: admin@iossifovlab.com
	pass: secret
	
* researcher

	user: research@iossifovlab.com
	pass: secret
	




	

