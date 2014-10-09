
fab -H root@wigserv2 deploy

fab -H root@wigserv5 deploy



Setelis Staging:
------------------
fab -f fabdev.py -H lubo@seqpipe-vm.setelis.com staging
