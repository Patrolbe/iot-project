import os

import azure.functions as func
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
    except ValueError as e:
        return func.HttpResponse(str(e), status_code=500)

    registry_manager = IoTHubRegistryManager(os.environ["ConnectionString"])
    for device in req_body:
        if device["errors_count"] > 3:
            registry_manager.invoke_device_method(
                device["ConnectionDeviceId"],
                CloudToDeviceMethod(method_name="EmergencyStop")
            )
    return func.HttpResponse("success", status_code=200)
