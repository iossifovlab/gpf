# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

    config.vm.define "vagrant" do |vagrant|
        vagrant.vm.box = "ubuntu/focal64"
        # vagrant.disksize.size='50GB'
    end

    config.vm.provider "virtualbox" do |vb|
        vb.memory = "16000"
    end

    config.vm.synced_folder ENV['DAE_DB_DIR'], "/data"
    config.vm.synced_folder ENV['DAE_PHENODB_DIR'], "/data"
    # config.vm.synced_folder ENV['DAE_GENOMIC_SCORES_HG19'], "/genomic-scores-hg19"
    # config.vm.synced_folder ENV['DAE_GENOMIC_SCORES_HG38'], "/genomic-scores-hg38"

    # config.vm.provision "shell", path: "scripts/provision.sh"
end
