# -*- mode: ruby -*-
# vi: set ft=ruby :

#
# Use this environment for running unit and coverage tests
#
# Install the requirements:
#
#   * https://www.vagrantup.com/downloads.html
#   * https://www.virtualbox.org
#
# Build or rebuild doc/mmd-specification.(html|pdf):
#
#   vagrant up
#
# Remove the build environment:
#
#   vagrant destroy -f
#

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y docker.io docker-compose
  SHELL

  config.vm.provision "shell", "run": "always", inline: <<-SHELL
    cd /vagrant
    docker-compose -f docker-compose.tests.yml up --build --exit-code-from tests
  SHELL
end
