from nornir import InitNornir
from nornir_jinja2.plugins.tasks import template_file
from nornir_rich.functions import print_result
from nornir_rich.progress_bar import RichProgressBar
from nornir.core.task import Task, Result
from dotenv import load_dotenv
import os
import pynetbox
from nornir_pygnmi.tasks import gnmi_set
import json
import yaml
import logging

load_dotenv(".env")
# Connect to NetBox
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)
nr = InitNornir(config_file="config.yaml")


def get_ct_from_netbox(task: Task) -> Result:
    """
    Retrieves the current configuration context from NetBox and updates the task's host data.

    Args:
        task (Task): The task to be executed.

    Returns:
        Result: A result object containing the updated host data and the retrieved configuration context.
    """
    device = nb.dcim.devices.get(name=task.host.name)
    if device and device.config_context:
      task.host.data.update(device.config_context)
    return Result(host=task.host, result="Got config context for {task.host.name}")

def get_interfaces_from_netbox(task: Task) -> Result:

    """
    Retrieves a list of interfaces and their IP addresses from NetBox and updates the task's host data.

    Args:
        task (Task): The task to be executed.

    Returns:
        Result: A result object containing the updated host data and a message indicating the interfaces were merged for the given device.
    """
    interfaces = nb.dcim.interfaces.filter(device=task.host.name)
    iface_list = []

    for iface in interfaces:
        ips = list(nb.ipam.ip_addresses.filter(interface_id=iface.id))
        if not ips:
            continue
        ip_address = ips[0].address

        iface_list.append({
            "name": iface.name,
            "description": iface.description,
            "ip": ip_address,
            "enabled": iface.enabled,
            "tags": [tag.name for tag in iface.tags]
        })

        if iface.name.lower().startswith("lo0"):
            lo0_ip = ip_address.split("/")[0]
            lo0_description = iface.description


    task.host.data.update({
        "interfaces": iface_list,
        "lo0_ip": lo0_ip,
        "lo0_description": lo0_description
        })
    return Result(host=task.host, result="Got interfaces data for {task.host.name}")


def get_ebgp_from_netbox(task:Task) -> Result:
    """
    Retrieves eBGP session details from NetBox and updates the task's host data.

    Fetches active BGP sessions for the device, determines their status, and collects
    details such as ASNs, addresses, and policies.

    Args:
        task (Task): The task to be executed.

    Returns:
        Result: A result object containing the updated host data with eBGP sessions.
    """

    bgp_sessions = nb.plugins.bgp.session.filter(device=task.host.name)
    ebgp_list = []

    for neighbor in bgp_sessions:

        if neighbor.status.value == "active":
            status = "enable"
        else:
            status = "disable"

        ebgp_list.append({
            "local_asn": neighbor.local_as.asn,
            "remote_asn": neighbor.remote_as.asn,
            "local_address":  neighbor.local_address.address.split("/")[0],
            "remote_address": neighbor.remote_address.address.split("/")[0],
            "status": status,
            "description": neighbor.description,
            "peer_group": neighbor.peer_group.name if neighbor.peer_group else None,
            "export_policy": neighbor.export_policies[0].name if neighbor.export_policies else None,
            "import_policy": neighbor.import_policies[0].name if neighbor.import_policies else None,
        })

    task.host.data.update({"ebgp_sessions": ebgp_list})
    return Result(host=task.host, result="Got ebgp data for {task.host.name}")


def render_template_json(task: Task) -> Result:
    """
    Renders the SR Linux configuration template for a given device using Jinja2
    and writes the rendered configuration to a file.

    Args:
        task (Task): The task to be executed.

    Returns:
        Result: A result object containing the updated host data and a message indicating the rendered configuration was written to a file.
    """
    r = task.run(
        task=template_file,
        template="srlinux.j2",
        path="./src/templates/",
        interfaces=task.host.data.get("interfaces", []),
        config_context=task.host.data,
    )

    rendered = r.result
    parsed = yaml.safe_load(rendered)
    rendered_json = json.dumps(parsed, indent=2)

    filename = f"src/rendered_config/{task.host.name}.json"
    with open(filename, "w") as f:
        f.write(rendered_json)

    return Result(host=task.host, result=f"Rendered config written to {filename}")


def push_config_gnmi(task: Task) -> Result:
    """
    Pushes the rendered configuration for a given device to the device using gNMI.

    Args:
        task (Task): The task to be executed.

    Returns:
        Result: A result object containing the updated host data and the result of the gNMI set operation.
    """
    filename = f"src/rendered_config/{task.host.name}.json"
    with open(filename, "r") as f:
        rendered = f.read()


    r = task.run(
        task=gnmi_set,
        encoding="json_ietf",
        update=[
            ("/", rendered)
        ],
        severity_level=logging.DEBUG
    )
    return Result(host=task.host, result=r.result)


def send_config_one_router(host):
    nr = InitNornir(config_file="config.yaml")
    nr = nr.filter(name=host)
    results = nr.run(task=push_config_gnmi)
    print_result(results)


def main(nr: InitNornir = nr):
    """
    Main execution entry point for the Nornir automation script.

    Initializes Nornir with a progress bar and executes a series of tasks:
    1. Fetch config context from NetBox.
    2. Fetch interface data from NetBox.
    3. Fetch eBGP session data from NetBox.
    4. Render configuration templates.
    5. Push configuration via gNMI.

    Args:
        nr (InitNornir): The initialized Nornir object. Defaults to the global `nr` object.
    """
    nr = nr.with_processors([RichProgressBar()])
    results = nr.run(task=get_ct_from_netbox)
    #print_result(results)
    results = nr.run(task=get_interfaces_from_netbox)
    #print_result(results)
    results = nr.run(task=get_ebgp_from_netbox)
    #print_result(results)
    results = nr.run(task=render_template_json)
    #print_result(results)
    results = nr.run(task=push_config_gnmi)
    print_result(results)



if __name__ == "__main__":
    main()
