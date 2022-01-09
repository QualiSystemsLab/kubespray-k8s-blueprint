import helpers

from yaml import load, dump, Loader

from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow


def inject_configuration_management_parameters(sandbox, _):
    sandbox.components.refresh_components(sandbox)

    cluster_nodes = helpers.get_resources_info_by_name_contains(sandbox, helpers.CLUSTER_NODE)
    kubespray_nodes = sandbox.components.get_apps_by_name_contains(helpers.KUBESPRAY_NODE)
    assert len(kubespray_nodes) == 1, "Only one kubespray app allowed"
    kubespray_node = kubespray_nodes[0]

    # assuming that each cluster node have identical username and password
    username = cluster_nodes[0]["username"]
    password = cluster_nodes[0]["password"]
    cluster_node_ips = [node["ip"] for node in cluster_nodes]

    sandbox.apps_configuration.set_config_param(kubespray_node, helpers.APPS_IP_PARAMETER_NAME, ",".join(cluster_node_ips))
    sandbox.apps_configuration.set_config_param(kubespray_node, helpers.SSH_USER_PARAMETER_NAME, username)
    sandbox.apps_configuration.set_config_param(kubespray_node, helpers.SSH_PASSWORD_PARAMETER_NAME, password)

    # configure all apps so we won't skip anything
    all_apps = [app for _, app in sandbox.components.apps.items()]
    sandbox.apps_configuration.apply_apps_configurations(all_apps)


def attach_kube_config_file_to_blueprint(sandbox, _):
    sandbox.components.refresh_components(sandbox)
    nodes = helpers.get_resources_info_by_name_contains(sandbox, "Cluster")
    # get kube config file from first cluster node that has it
    for node in nodes:
        try:
            with helpers.get_file_via_ssh(node["ip"], node["username"], node["password"]) as file:
                config = load(file, Loader)
                config["clusters"][0]["cluster"]["server"] = f"https://{node['ip']}:6443"
                yaml_config = dump(config)
                helpers.upload_file_to_reservation(sandbox.id, helpers.get_do_auth_token(sandbox),
                       sandbox.automation_api.host, 9000, yaml_config)
                break
        except(FileNotFoundError):
            continue


def main():
    sandbox = Sandbox()
    DefaultSetupWorkflow().register(sandbox, enable_configuration=False)
    sandbox.workflow.add_to_configuration(function=inject_configuration_management_parameters, components=[])
    sandbox.workflow.on_configuration_ended(attach_kube_config_file_to_blueprint)
    sandbox.execute_setup()


main()

