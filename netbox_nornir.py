
from jinja2 import Template
import pynetbox
import os
from dotenv import load_dotenv
import yaml
# Load environment variables from .env file
load_dotenv()

# Connect to NetBox
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)


# Process data as a dictionary
def generate_hosts_yaml():

    # Retrieve devices from NetBox
    devices = nb.dcim.devices.all()

    hosts_data = {}
    for device in devices:
        hosts_data[device.name] = {
            "hostname": device.name.lower(),
            "platform": device.platform.name if device.platform else "unknown",
            "groups": [tag["name"] for tag in device.tags] if device.tags else [],
            }


    # Load Jinja2 template
    with open("templates/hosts.j2") as f:
        template = Template(f.read())

    # Render and save as hosts.yaml
    output = template.render(hosts=hosts_data)

    with open("inventory/hosts.yaml", "w") as f:
        f.write(output)

    print("hosts.yaml file generated successfully!")

def generate_groups_yaml():

    groups_data = {}
    devices = nb.dcim.devices.all()
    for device in devices:
        for tag in device.tags or []:
            if tag["name"] not in groups_data:
                groups_data[tag["name"]] = {
                    "description": f"{tag['name']}"
                }

    # Save to groups.yaml
    with open("inventory/groups.yaml", "w") as file:
        yaml.dump(groups_data, file, default_flow_style=False)

    print("groups.yaml file generated successfully!")

generate_hosts_yaml()
generate_groups_yaml()
