import os

import azure.functions as func
from azure.iot.hub import IoTHubRegistryManager


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
    except ValueError as e:
        return func.HttpResponse(str(e), status_code=500)

    registry_manager = IoTHubRegistryManager(os.environ["ConnectionString"])
    for device in req_body:
        if float(device["kpi"]) < 90:
            twin = registry_manager.get_twin(device["ConnectionDeviceId"])
            twin.properties.desired["ProductionRate"] = twin.properties.reported["ProductionRate"] - 10
            registry_manager.update_twin(device["ConnectionDeviceId"], twin, twin.etag)
    return func.HttpResponse("success", status_code=200)
