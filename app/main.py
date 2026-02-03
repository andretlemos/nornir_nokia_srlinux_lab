from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from src.nornir_tasks.deploy_config import send_config_one_router
from dotenv import load_dotenv
import pynetbox
import os

load_dotenv(".env")
# Connect to NetBox
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

app = FastAPI(title="Nornir API")

@app.get("/")
async def get_routers():
  devices = nb.dcim.devices.all()
  info_dict = {}
  for device in devices:
    info_dict[device.name] =  {
      "name": device.name,
      "model": device.device_type.slug,
      "ip" : device.primary_ip4.address,
    }
  return JSONResponse(content={"devices": info_dict})

@app.post("/apply-config/{host}")
async def apply_config(host: str):

  try:
    send_config_one_router(host)
    return JSONResponse(
      content={"status": "success", "host": host}, status_code=200 )

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
