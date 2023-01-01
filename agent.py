from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse
from asyncua.common.node import Node
from asyncua import ua
import json
import asyncio
from datetime import datetime
class Agent:
  def __init__(self, urzadzenie, connectionString):
    self.urzadzenie = urzadzenie
    self.connectionString = connectionString
    self.zadania = []

    self.klientIot = IoTHubDeviceClient.create_from_connection_string(self.connectionString)
    self.klientIot.connect()
    self.klientIot.on_twin_desired_properties_patch_received = self.aktualizacjaDesiredPropertiesUrzadzenia
    self.klientIot.on_method_request_received = self.otrzymaneMetody

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
    
  def aktualizacjaDesiredPropertiesUrzadzenia(self, data):
    try:
      if "ProductionRate" in data:
        self.zadania.append(self.ustawieniaUrzadzenia('ProductionRate', ua.Variant(data['ProductionRate'], ua.VariantType.Int32)))
    except Exception as e:
      print(e)

  async def ustawieniaUrzadzenia(self, nazwaWartosci, wartosc):
    await (await self.urzadzenie.get_child(nazwaWartosci)).write_value(wartosc)


  def otrzymaneMetody(self, metoda):

    if metoda.name == "MaintenanceDone":
      self.klientIot.patch_twin_reported_properties({"LastMaintenanceDate":  datetime.now().isoformat()})
    
    elif metoda.name == "ResetErrorStatus":
      print("resetowanie errorów")
      self.zadania.append(self.metodyUrzadzenia("ResetErrorStatus"))
      
    elif metoda.name == "EmergencyStop":
      print("awaryjny stop")
      self.zadania.append(self.metodyUrzadzenia("EmergencyStop"))

    self.klientIot.send_method_response(MethodResponse(metoda.request_id, 0))
  
  
  async def metodyUrzadzenia(self, metoda: str):
      return await self.urzadzenie.call_method(metoda)



  def zbiorZadan(self):
    zadania = []
    for zadanie in self.zadania:
      zadania.append(asyncio.create_task(zadanie))
    zadania.append(asyncio.create_task(self.telemetria()))
    self.zadania = []
    return zadania

  