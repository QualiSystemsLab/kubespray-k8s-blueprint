from json import loads
from io import BytesIO
from requests import post, put
from paramiko import SSHClient, AutoAddPolicy

from cloudshell.api.cloudshell_api import CloudShellAPISession

from cloudshell.helpers.scripts.cloudshell_scripts_helpers import get_connectivity_context_details_dict, get_reservation_context_details_dict


APPS_IP_PARAMETER_NAME = "APPLICATIONS_TO_CONFIGURE"
SSH_USER_PARAMETER_NAME = "SSH_USER"
SSH_PASSWORD_PARAMETER_NAME = "SSH_PASSWORD"

CLUSTER_NODE = "Cluster Node"
KUBESPRAY_NODE = "Kubespray Node"


def get_resource_connection_credentials(resource_attributes):
    username = next((a.Value for a in resource_attributes if a.Name == "OS Login"))
    password = next((a.Value for a in resource_attributes if a.Name == "OS Password"))
    return username, password


def get_resources_info_by_name_contains(sandbox, name):
    reservation_details = sandbox.automation_api.GetReservationDetails(sandbox.id)
    resources = reservation_details.ReservationDescription.Resources
    resource_names = [r.Name for r in resources if name in r.Name]

    get_details = lambda x: sandbox.automation_api.GetResourceDetails(x)
    resources_details = [get_details(resource_name) for resource_name in resource_names]

    resources_info = []
    for detail in resources_details:
        username, password = get_resource_connection_credentials(detail.ResourceAttributes)
        resources_info.append({
            "name": detail.Name, 
            "ip": detail.FullAddress, 
            "username": username, 
            "password": password
        })
    return resources_info


def get_file_via_ssh(host, username, password):
    config_file_path = "/root/.kube/config" if username == "root" else f"/home/{username}/.kube/config"
    with SSHClient() as ssh:
        ssh.set_missing_host_key_policy(AutoAddPolicy)
        ssh.connect(host, username=username, password=password, look_for_keys=False)
        with ssh.open_sftp() as sftp:
            file = BytesIO()
            sftp.getfo(config_file_path, file)
            file.seek(0)
            return file


def upload_file_to_reservation(sandbox_id, auth_token, host, port, file):
    headers = {"Authorization": f"Basic {auth_token}"}
    multipart_form_data = {
            "reservationId": (None, sandbox_id),
            "saveFileAs": (None, "kube_config"),
            "overwriteIfExists": (None, True),
            "QualiPackage": (None, file)
    }

    url = f"http://{host}:{port}/API/Package/AttachFileToReservation"
    response = post(url, files=multipart_form_data, headers=headers)
    if response:
        parsed_response = loads(response.content)
        if not parsed_response["Success"]:
            raise Exception(parsed_response["ErrorMessage"])
    else:
        raise Exception(response.content)


def get_do_auth_token(sandbox):
    """
    Login REST API, get authentication
    """
    url = 'http://do:9000/API/Auth/Login'
    request_body = {
        'Username': sandbox.connectivityContextDetails.admin_user,
        'Password': sandbox.connectivityContextDetails.admin_pass,
        'Domain': sandbox.automation_api.domain
    }
    response = put(url, json=request_body)
    return loads(response.content)

