#! /bin/bash

set -x # enable trace
set -e # enable exit on first error
YQ_VERSION=4.15.1

# validate that all needed variables were passed from orch script
while read -r env_var; do
  [ -z "${!env_var}" ] && { echo "$env_var is empty or not set. Exiting.."; exit 1; }
done << EOF
APPLICATIONS_TO_CONFIGURE
KUBESPRAY_REF
METALLB_IP_RANGE
SSH_PASSWORD
SSH_USER
EOF

# previous check won't work with this option, so it must be enabled after
set -u # no unset variables

# switch to the home folder
cd ~/ 
# create a working folder and switch to it
mkdir -p kubespray-config && cd "$_" 

yum install wget -y
yum install sshpass -y
yum install python3 -y

# get kubespray release version if not exist already
        wget "${KUBESPRAY_REF}" -O ./kubespray.zip
        unzip ./kubespray.zip
        KUBESPRAY_FOLDER=$(find . -maxdepth 1 -type d -regextype sed -regex "./*kubespray-[.0-9a-zA-Z]*")
        echo "KUBESPRAY_FOLDER: ${KUBESPRAY_FOLDER}"
        rm ./kubespray.zip -f

# install needed packages
pip3 install wheel
pip3 install -r "${KUBESPRAY_FOLDER}"/requirements.txt 

# configure ssh
yes | ssh-keygen -q -f ~/.ssh/id_rsa  -t rsa -N ""

declare -a IP_LIST=($(echo "$APPLICATIONS_TO_CONFIGURE" | tr "," "\n"))
# add entries to know_hosts files on machines to configure
for IP in "${IP_LIST[@]}"
do
        # we have to use sshpass in order to pass password to ssh-copy-id
        # StrictHostKeyChecking is set to no in order to disable prompt for user agreement
        # on known_hosts file change
        sshpass -p "${SSH_PASSWORD}" ssh-copy-id "${SSH_USER}"@"${IP}" -o StrictHostKeyChecking=no
done

# configuring inventory files
cp -rfp "${KUBESPRAY_FOLDER}"/inventory/sample "${KUBESPRAY_FOLDER}"/inventory/mycluster

# build inventory files
CONFIG_FILE="${KUBESPRAY_FOLDER}"/inventory/mycluster/hosts.yaml python3 "${KUBESPRAY_FOLDER}"/contrib/inventory_builder/inventory.py "${IP_LIST[@]}"

# get yq to edit yml files, yq is a commandline YAML file processor
if [[ ! -f ./yqk ]]; then
        wget https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64 -O ./yqk && chmod +x ./yqk
fi

# update yml files in place
./yqk e -i '
        .kube_proxy_strict_arp = true' "${KUBESPRAY_FOLDER}"/inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml
./yqk e -i '
        .metallb_enabled = true |
        .metallb_speaker_enabled = true |
        .metallb_ip_range |= [strenv(METALLB_IP_RANGE)]
' "${KUBESPRAY_FOLDER}"/inventory/mycluster/group_vars/k8s_cluster/addons.yml

# tee will swallow exit code of ansible-playbook command, this option will make script fail if playbook failed
set -o pipefail
# finally, run the playbook
ansible-playbook -i "${KUBESPRAY_FOLDER}"/inventory/mycluster/hosts.yaml  --become --become-user=root "${KUBESPRAY_FOLDER}"/cluster.yml \
    |& tee ./ansible.log

