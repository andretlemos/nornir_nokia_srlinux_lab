# nornir_nokia_srlinux_lab

A small lab repository for automating Nokia SR Linux device deployments and NetBox integration using Nornir, containerized NetBox, and Containerlab topologies.

**Overview**

- **Purpose:** Provide automation, inventory, and configuration templates for a Nokia SR Linux lab using Nornir and NetBox.
- **Scope:** Contains Containerlab topologies, NetBox docker setup, Nornir inventory, templates, and helper scripts.

**Quickstart**

Prerequisites:
- Docker / Docker Compose (for NetBox docker)
- Python 3.8+ and pip
- Containerlab (if you want to deploy the lab topology)

Get started (basic steps):

1. Install Python deps:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

2. (Optional) Launch NetBox (from `netbox-docker`):

```bash
cd netbox-docker
docker compose up -d
```

2.1 Import the database on Netbox

```bash
cd backup_netbox
./netbox_database_import.sh
```

3. (Optional) Deploy the lab with Containerlab:

```bash
sudo containerlab deploy --topo clab/lab.clab.yaml
```

4. Use the automation scripts:

```bash
python3 deploy_config.py
```

See the individual scripts for available options.

**Repository Structure**

- `clab/` — Containerlab topology files and per-node config trees used by the virtual lab.
- `netbox-docker/` — Containerized NetBox build and docker-compose configuration for a local NetBox instance.
- `inventory/` — Nornir-style inventory data: `hosts.yaml`, `groups.yaml`, `defaults.yaml`.
- `templates/` — Jinja2 templates used to render device config and system JSON.
- `configuration/` — Python helper modules used by the project (logging, plugins, extra helpers).
- `deploy_config.py` — main deployment/config helper script (previously `netbox.py`).
- `backup_netbox/` — helper scripts for exporting/importing NetBox DB snapshots.

**Usage Notes**

- Review `inventory/` and `templates/` before running automation to adapt to your lab.
- `deploy_config.py` is the primary entrypoint for applying configuration or pushing data to NetBox; open it to see CLI options and environment requirements.
