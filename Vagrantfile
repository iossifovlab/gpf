# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|


  config.vm.define "vagrant" do |vagrant|
	vagrant.vm.box = "ubuntu/xenial64"
	vagrant.vm.hostname = "vagrant"
	vagrant.vm.network "private_network", ip: "192.168.200.17"

  end


  config.vm.provision "shell", path: "scripts/bootstrap.sh"
  config.vm.synced_folder ENV['DAE_DB_DIR'], "/data-dev"


  config.vm.provider "virtualbox" do |v|
    v.memory = 4096
    v.cpus = 2
  end



end
