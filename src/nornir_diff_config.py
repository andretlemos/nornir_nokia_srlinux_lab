from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_rich.functions import print_result
import requests
import json
import urllib3
import time
from pathlib import Path

# Disable SSL warnings for labs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Pushgateway Base Configuration
PUSHGATEWAY_BASE = "http://localhost:9091/metrics/job/nornir_diff_config"

LOG_FILE = "clab/configs/promtail/logs/nornir_diff_config.log"

def log_to_file(message: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def jsonrpc_diff(task: Task) -> Result:
    """
    Executes a JSON-RPC diff and sends the individual metric per device to the Pushgateway.
    """
    # Load expected configuration from local file
    config_file = Path(f"src/rendered_config/{task.host.name}.json")
    if not config_file.exists():
        return Result(host=task.host, result=f"Arquivo {config_file} não encontrado", failed=True)

    rendered_config = json.loads(config_file.read_text())

    # Build JSON-RPC Payload
    payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "diff",
        "params": {
            "commands": [
                {
                    "action": "update",
                    "path": "/",
                    "value": rendered_config
                }
            ],
            "output-format": "text"
        }
    }

    # Inventory connection details
    host = task.host.hostname
    user = task.host.username
    password = task.host.password
    url = f"https://{host}/jsonrpc"

    try:
        # Send request to the device
        response = requests.post(
            url,
            json=payload,
            auth=(user, password),
            verify=False,
            timeout=10
        )
        result = response.json()

        # Determine Compliance
        # If 'result' is empty [], it means there are no differences
        if "result" in result and result["result"] == []:
            diff_output = "✅ Config matches (no differences)"
            compliance_value = 1
            log_to_file(f"{task.host.name}: {diff_output}")

        else:
            diff_text = "\n".join(result.get("result", ["Erro ao ler diff"]))
            diff_output = f"❌ Config does not match:\n{diff_text}"
            compliance_value = 0
            log_to_file(f"{task.host.name}: {diff_output}")

    except Exception as e:
        diff_output = f"Erro de conexão: {str(e)}"
        compliance_value = 0

    # Send metric to Pushgateway
    device_specific_url = f"{PUSHGATEWAY_BASE}/device/{task.host.name}"
    metric_payload = f"config_match {compliance_value}\n"

    try:
        requests.post(
            device_specific_url,
            data=metric_payload,
            headers={"Content-Type": "text/plain"},
            timeout=5
        )
    except Exception as e:
        print(f"Error sending metric to Pushgateway: {e}")

    return Result(
        host=task.host,
        result=diff_output,
    )

def main():
    """
    Main execution entry point for the Nornir automation script.

    Initializes Nornir with a configuration file, executes a series of tasks
    in parallel on all hosts, and displays the formatted result on the console.

    Tasks executed in parallel on all hosts:

    1. Fetch current configuration from the device using json-rpc.
    2. Fetch desired configuration from the device using json-rpc.
    3. Determine compliance by comparing the current and desired configurations.
    4. Send a metric to Pushgateway with the compliance result.
    """
    nr = InitNornir(config_file="config.yaml")

    # Execute the task in parallel on all hosts
    results = nr.run(task=jsonrpc_diff)

    # Display the formatted result on the console
    print_result(results)

if __name__ == "__main__":
    print("Start compliance check on all devices (Loop every 30s)...")
    while True:
        main()
        time.sleep(30)
