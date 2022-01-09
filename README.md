# Summary
This repository contains orchestration and configuration management
scripts for [Kubernetes Cluster - IL](http://do/RM/Diagram/Index/a685b455-b96a-4494-a3eb-a9ae588e845e?diagramType=Topology)
blueprint.

This blueprint setups kubernetes cluster on multiple machines and provides 
access to the cluster via kubernetes configuration file that is being attached 
to the sandbox at the end of sandbox configuration.

## Blueprint overview

* Global inputs:

    * _KUBERNETES_VERSION_ - (defaults to v1.21.6.) Will install kubernetes of a
    provided version. Important note: there is a dependency between kubespray 
    version and kubernetes versions that it can setup. Current kubespray version 
    is v2.17.1 and it is hardcoded into configuration management script.

    * _METALLB_IP_RANGE_ - (defaults to "192.168.85.150-192.168.85.200" ) ip 
    range that will be provided to [metallb](https://metallb.universe.tf/) 
    kubernetes load balancer. This ip range is shared across sandboxes, 
    so in case of multiple sandboxes there may be conflicts, 
    it is advised to use smaller ranges.
 
* Orchestration script:

    * Orchestration script provides parameters to Kubespray Node configuration 
    management script. It collects actual ip addresses of applications that has 
    _Cluster Node_ in their names and passes them to the application that has 
    _Kubespray Node_ in its name.

    * After configuration is completed, orchestration script will upload 
    kubernetes configuration file to the sandbox.

* Troubleshooting - sometimes things aren't going well with kubespray, to check 
logs of kubespray ansible playbook: connect to the Kubepsray Node via ssh and 
open logs at _/root/kubespray-config/ansible.log_

## Repository overview:

* _./kubespray_configuration_management.sh_ - configuration management script
that is defined on a *Kubespray Node* application. 

* _./kubespray_orchestration_script/_ - orchestration startup script with its
dependencies for blueprint setup.

