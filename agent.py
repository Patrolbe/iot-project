from azure.iot.device import IoTHubDeviceClient, Message
from asyncua.common.node import Node
from asyncua import Client
import json

class Agent:
  def __init__(self, urzadzenie, connectionString):
    self.urzadzenie = urzadzenie
    self.connectionString = connectionString

    self.klientIot = IoTHubDeviceClient.create_from_connection_string(self.connectionString)
    self.klientIot.connect()

    self.klientIot.patch_twin_reported_properties({'DeviceError': None})
    self.klientIot.patch_twin_reported_properties({'ProductionRate': None})

  async def telemetria(self):
    dane = {
        "WorkorderId": await (await self.urzadzenie.get_child('WorkorderId')).read_value(),
        "ProductionStatus": await (await self.urzadzenie.get_child('ProductionStatus')).read_value(),
        "GoodCount": await (await self.urzadzenie.get_child('GoodCount')).read_value(),
        "BadCount": await (await self.urzadzenie.get_child('BadCount')).read_value(),
        "Temperature": await (await self.urzadzenie.get_child('Temperature')).read_value(),
        "ProductionRate":await ( await self.urzadzenie.get_child('ProductionRate')).read_value(),
        "DeviceError": await (await self.urzadzenie.get_child('DeviceError')).read_value()
    }

    print(dane)
    self.klientIot.patch_twin_reported_properties({'DeviceError': dane["DeviceError"]})
    self.klientIot.patch_twin_reported_properties({'ProductionRate': dane["ProductionRate"]})

    wiadomosc = Message(json.dumps(dane), "UTF-8", "JSON")
    self.klientIot.send_message(wiadomosc)
    