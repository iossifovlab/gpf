# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
    config.vm.box = "generic/ubuntu2004"

    config.vm.provider "qemu" do |qe|
        qe.arch = "x86_64"
        qe.machine = "q35"
        qe.cpu = "max"
        qe.net_device = "virtio-net-pci"
    end
    config.vm.synced_folder ".", "/vagrant", type: "smb", smb_host: "10.0.2.2", mount_options: ['mfsymlink']

    config.vm.provision "shell", path: "scripts/provision.sh"

end

# Vagrant.configure("2") do |config|
    
#     config.vm.define "vagrant" do |vagrant|
#         vagrant.vm.box = "ubuntu/focal64"
#         # vagrant.disksize.size='50GB'
#     end

#     config.vm.provider "virtualbox" do |vb|
#         vb.memory = "4096"
#     end

#     config.vm.provision "shell", path: "scripts/provision.sh"
# end
