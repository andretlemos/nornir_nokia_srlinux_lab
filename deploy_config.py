
import os
import pynetbox
import json
from dotenv import load_dotenv
from nornir import InitNornir
from nornir_jinja2.plugins.tasks import template_file
from nornir_pygnmi.tasks import gnmi_set
from nornir_rich.functions import print_result
from nornir_rich.progress_bar import RichProgressBar


load_dotenv()
# Connect to NetBox
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

def enrich_interfaces(task):
    """
    Enriches task.host with interface data from NetBox.

    Iterates over device's interfaces, then iterates over each interface's
    IP addresses. The data is then stored in task.host["interfaces"].

    Args:
        task (Task): The task to enrich.

    Returns:
        None
    """
    device = nb.dcim.devices.get(name=task.host.name)
    interfaces = nb.dcim.interfaces.filter(device=device.name)
    interface_data = []
    for interface in interfaces:
        ips = nb.ipam.ip_addresses.filter(interface_id=interface.id)
        for ip in ips:
            interface_data.append({
                "interface": interface.name,
                "ip": ip.address
            })
    task.host["interfaces"] = interface_data


def render_and_push(task):
    # 1. Render JSON template
    """
    Renders a JSON template with host data and pushes the configuration to the device via gNMI.

    Args:
        task (Task): The task to render and push.

    Returns:
        None
    """
    rendered = task.run(
        task=template_file,
        template="srlinux.j2",
        path="templates",
        **task.host.data
    )

    # 2. Parse string to dict (Required for json_ietf encoding)
    config_dict = json.loads(rendered.result)

    # 3. Push via gNMI
    task.run(
        task=gnmi_set,
        encoding="json_ietf",
        update=[
            ("/", config_dict)
        ]
    )

if __name__ == "__main__":
    nr = InitNornir(config_file="config.yaml")
    nr_with_processors = nr.with_processors([RichProgressBar()])
    nr_with_processors.run(task=enrich_interfaces)
    result =  nr_with_processors.run(task=render_and_push)
    print_result(result)
