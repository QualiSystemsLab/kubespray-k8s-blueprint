#!/bin/bash
wget https://get.helm.sh/helm-v3.6.0-linux-amd64.tar.gz
tar xvf helm-v3.6.0-linux-amd64.tar.gz 
sudo mv linux-amd64/helm /usr/local/bin
rm helm-v3.6.0-linux-amd64.tar.gz 
rm -rf linux-amd64
helm version --short