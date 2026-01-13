from nornir import InitNornir
from nornir_jinja2.plugins.tasks import template_file
from nornir_rich.functions import print_result
from nornir_rich.progress_bar import RichProgressBar
from nornir_netmiko.tasks import netmiko_send_config as send_config
from nornir.core.task import Task, Result
from dotenv import load_dotenv
import os
import pynetbox
from nornir_pygnmi.tasks import gnmi_set
import json

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
    return Result(host=task.host, result={device})

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
            "tags": [tag.name for tag in iface.tags]
        })

    task.host.data.update({"interfaces": iface_list})
    return Result(host=task.host, result="Interfaces merged for {task.host.name}")


def render_template_cfg(task: Task) -> Result:
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
        path="templates/set",
        interfaces=task.host.data.get("interfaces", []),
        config_context=task.host.data,


    )
    rendered = r.result

    filename = f"src/rendered_config/set/{task.host.name}.cfg"
    with open(filename, "w") as f:
        f.write(rendered)
    print(f"\n--- {task.host.name} ---\n{rendered}\n")
    return Result(host=task.host, result=f"Rendered config written to {filename}")

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
        template="srlinux.json.j2",
        path="templates/json",
        interfaces=task.host.data.get("interfaces", []),
        config_context=task.host.data,


    )
    rendered = r.result

    filename = f"src/rendered_config/json/{task.host.name}.json"
    with open(filename, "w") as f:
        f.write(rendered)
    print(f"\n--- {task.host.name} ---\n{rendered}\n")
    return Result(host=task.host, result=f"Rendered config written to {filename}")


def push_config_netmiko(task: Task) -> Result:

    filename = f"src/rendered_config/set/{task.host.name}.cfg"
    with open(filename, "r") as f:
        rendered = f.read().splitlines()

    r = task.run(
        task=send_config,
        config_commands=rendered
    )
    return Result(host=task.host, result=r.result)

def push_config_gnmi(task: Task) -> Result:
    """
    Pushes the rendered configuration for a given device to the device using gNMI.

    Args:
        task (Task): The task to be executed.

    Returns:
        Result: A result object containing the updated host data and the result of the gNMI set operation.
    """
    filename = f"src/rendered_config/json/{task.host.name}.json"
    with open(filename, "r") as f:
        rendered = f.read()
    try:
        json.loads(rendered)
    except json.JSONDecodeError:
        return Result(host=task.host, result=f"Invalid JSON in {filename}")


    r = task.run(
        task=gnmi_set,
        encoding="json_ietf",
        update=[
            ("/", rendered)
        ]
    )
    return Result(host=task.host, result=r.result)

def main(nr: InitNornir = nr):
    nr = nr.with_processors([RichProgressBar()])
    results = nr.run(task=get_ct_from_netbox)
    print_result(results)
    results = nr.run(task=get_interfaces_from_netbox)
    print_result(results)
    #results = nr.run(task=render_template_cfg)
    #print_result(results)
    results = nr.run(task=render_template_json)
    print_result(results)
    #results = nr.run(task=push_config_netmiko)
    #print_result(results)
    results = nr.run(task=push_config_gnmi)
    print_result(results)


if __name__ == "__main__":
    main()
