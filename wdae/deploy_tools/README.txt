To deploy application:
-------------------------


fab -H root@wigserv2 deploy

fab -H root@wigserv5 deploy

To sync data:
-----------------

fab -H root@wigserv2 data_sync_to

By default the remote directory where data is sent is 
'/data/dae/DAEDB/data'. If you want to change the remote directory you
can add following REMOTE_DATA_DIR parameter to the 'fab' command:

fab -H root@wigserv2 data_sync_to --set REMOTE_DATA_DIR="test-sync-data"




Setelis Staging:
------------------
fab -f fabdev.py -H lubo@seqpipe-vm.setelis.com staging
