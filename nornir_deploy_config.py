from nornir import InitNornir
from nornir_jinja2.plugins.tasks import template_file
from nornir_rich.functions import print_result
from nornir_rich.progress_bar import RichProgressBar
from nornir.core.task import Task, Result
from dotenv import load_dotenv
import os
import pynetbox
from nornir_pygnmi.tasks import gnmi_set

load_dotenv()
# Connect to NetBox
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)
nr = InitNornir(config_file="config.yaml")


def get_ct_from_netbox(task: Task) -> Result:
    device = nb.dcim.devices.get(name=task.host.name)
    if device and device.config_context:
      task.host.data.update(device.config_context)
    return Result(host=task.host, result={device})

def get_interfaces_from_netbox(task: Task) -> Result:
    interfaces = nb.dcim.interfaces.filter(device=task.host.name)
    iface_list = []

    for iface in interfaces:
        ips = list(nb.ipam.ip_addresses.filter(interface_id=iface.id))
        if not ips:
            continue
        ip_address = ips[0].address
        iface_list.append({
            "name": iface.name,
            "ip": ip_address
        })

    task.host.data.update({"interfaces": iface_list})
    return Result(host=task.host, result="Interfaces merged for {task.host.name}")

def render_template(task: Task) -> Result:
    r = task.run(
        task=template_file,
        template="srlinux.j2",
        path="templates",

    )
    rendered = r.result

    filename = f"rendered_config/{task.host.name}.json"
    with open(filename, "w") as f:
        f.write(rendered)
    print(f"\n--- {task.host.name} ---\n{rendered}\n")
    return Result(host=task.host, result=f"Rendered config written to {filename}")

def push_config(task: Task) -> Result:
    filename = f"rendered_config/{task.host.name}.json"
    with open(filename, "r") as f:
        rendered = f.read()
    r = task.run(
        task=gnmi_set,
        encoding="json_ietf",
        update=[
            ("/", rendered)
        ]
    )
    return Result(host=task.host, result=r.result)

#nr = nr.with_processors([RichProgressBar()])
results = nr.run(task=get_ct_from_netbox)
print_result(results)
results = nr.run(task=get_interfaces_from_netbox)
print_result(results)
results = nr.run(task=render_template)
print_result(results)
results = nr.run(task=push_config)
print_result(results)
