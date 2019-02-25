# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

    config.vm.define "vagrant" do |vagrant|
        vagrant.vm.box = "ubuntu/bionic64"
        vagrant.disksize.size='50GB'
    end

    config.vm.network "forwarded_port", guest: 8000, host: 8000

    config.vm.provider "virtualbox" do |vb|
        vb.memory = "16000"
    end

    config.vm.synced_folder ENV['DAE_DB_DIR'], "/data-dev"
end
