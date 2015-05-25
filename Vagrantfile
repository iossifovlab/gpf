# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|


  config.vm.define "vagrant" do |vagrant|
	vagrant.vm.box = "ubuntu/trusty64"
	vagrant.vm.hostname = "vagrant"
	vagrant.vm.network "private_network", ip: "192.168.200.17"

	config.vm.provision "ansible" do |ansible|
		ansible.playbook = "deploy_tools/iossifovlab-provision.yml"
		ansible.host_key_checking = false
		ansible.verbose = "v"
	end
  end


  config.vm.provider "virtualbox" do |v|
    v.memory = 4096
    v.cpus = 2
  end

end
