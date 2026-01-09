# nornir_nokia_srlinux_lab

A lab repository for automating Nokia SR Linux device configuration and NetBox integration using Nornir, Containerlab topologies, and a containerized NetBox.

## Overview

- Purpose: Provide inventory, templates, scripts, and helper tooling to build and automate a small SR Linux lab.
- Key capabilities: Containerlab topologies, NetBox (docker) integration, Nornir inventory and templating, config rendering.

## Prerequisites

- Linux host (tested on Ubuntu)
- Docker & Docker Compose (for running NetBox)
- Python 3.8+ and pip
- Optional: Containerlab (to deploy the virtual topology)

## Quickstart

1. Clone the repo:

```bash
git clone https://your.repo/nornir_nokia_srlinux_lab.git
cd nornir_nokia_srlinux_lab
```

2. Create and activate a Python virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Start NetBox locally (from `netbox-docker`):

```bash
cd netbox-docker
docker compose up -d
```

4.  Import a NetBox DB snapshot :

```bash
cd backup_netbox
./netbox_database_import.sh
```

5. Deploy the lab topology with Containerlab:

```bash
sudo containerlab deploy --topo clab/lab.clab.yaml
```

6. Render or push device configs using the project's scripts:

```bash
python3 nornir_deploy_config.py
```

## Repository layout

- `clab/` — Containerlab topology and per-node configuration trees.
- `netbox-docker/` — Docker build and compose files to run NetBox locally.
- `inventory/` — Nornir inventory files: `hosts.yaml`, `groups.yaml`, `defaults.yaml`.
- `templates/` — Jinja2 templates for rendering device JSON/configs.
- `rendered_config/` — Example rendered configuration output for lab devices.
- `configuration/` — Python helper modules used across the project.
- `backup_netbox/` — Scripts to export/import NetBox DB snapshots.
- `clab/lab.clab.yaml` — Topology used for Containerlab.
- `nornir_deploy_config.py` — Main script to drive config rendering/push (see `--help`).

## Notes & tips

- Inspect and adapt `inventory/` and the Jinja2 templates in `templates/` to fit your environment before running any push operations.
- Use the virtual environment to avoid system package conflicts.
- If you run NetBox locally, allow some time for services to become healthy before importing data.
