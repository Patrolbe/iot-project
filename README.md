# DOKUMENTACJA – PROJEKT IOT

### PATRYK BLIŹNIEWSKI

## URUCHOMIENIE PROGRAMU

```
python -m venv ./venv
source ./venv/Scripts/activate
pip install -r req.txt
python main.py
```

## Połączenie z OPC UA severL

Połączenie odbywa się za pomocą biblioteki asyncua. Przy uruchomieniu programu wykona się funkcja pobierz() znajdująca się w pliku ustawienia.py Nalezy podać url servera a także connection stringi do
urzadzeń z których bedziemy korzystać. (Należy je również utworzyć w Azure)

```
def pobierz(self, zasob, urzadzenie = None):
    if urzadzenie:
      if self.config.has_option(urzadzenie, zasob):
        wartosc = self.config[urzadzenie][zasob]
      else:
        wartosc = str(input(f"Proszę, podaj {zasob} dla urządzenia {urzadzenie}: "))
        self.config[urzadzenie] = {
          zasob: wartosc
        }
        self.zapisz()
    else:
      if self.config.has_option('INNE_USTAWIENIA', zasob):
        wartosc = self.config['INNE_USTAWIENIA'][zasob]
      else:
        wartosc = str(input(f"Proszę, podaj {zasob}: "))
        self.config['INNE_USTAWIENIA'] = {
          zasob: wartosc
        }
        self.zapisz()
    return wartosc
```

Wartości zapisza się do pliki config.ini

Połączenie odbywa się w głównej funkcji main() w pliku main.py

```
async def main():
  ustawienia = Ustawienia()
  url = ustawienia.pobierz('url')

  agenci = []

  async with Client(url=url) as klient:
    urzadzenia = await klient.get_objects_node().get_children()
    for urzadzenie in urzadzenia:
      nazwa = (await urzadzenie.read_browse_name()).Name
      if (nazwa!= 'Server'):
        connectionString = ustawienia.pobierz('connectionString',nazwa)
        agent = Agent(urzadzenie, connectionString)
        agenci.append(agent)
    while True:
      zadania = []
      for agent in agenci:
        zadania_agenta = agent.zbiorZadan()
        for zadanie_agenta in zadania_agenta:
          zadania.append(zadanie_agenta)

      await asyncio.gather(*zadania)
      await asyncio.sleep(5)
```

## Konfiguracja Agenta i D2C Message

Po podaniu connection stringa agent się utworzy za pomocą funkcji IoTHubDeviceClient.create_from_connection_string(self.connectionString) znajdującej się w pliku agent.py

Agent jest odpowiedzialny za wysyłanie danych do Iot Hub. Wysyłanie odbywa się w funkcji telemetria().

```
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

```

## Direct Method

Agent obsługuje następujące direct methody: EmergencyStop, ResetErrorStatus, MainstanaceDone

```
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


```

## Data Calculations and buisness logic

Wykokane kwerendy:

```
-- produkcja per workorderId
SELECT
    WorkorderId,
    SUM(GoodCount) AS GoodCountSum,
    SUM(BadCount) AS BadCountSum
INTO [asa-out-production-counts]
FROM [asa-in] TIMESTAMP BY EventEnqueuedUtcTime
GROUP BY
    WorkorderId, TumblingWindow(minute , 15)

-- production kpi
SELECT
    (SUM(GoodCount) / (SUM(GoodCount) + SUM(BadCount))) AS ProductionKPI
INTO [asa-out-kpi]
FROM [asa-in] TIMESTAMP BY EventEnqueuedUtcTime
GROUP BY
    TumblingWindow(minute , 15)

-- minimalna, maksymalna i średnia temperatura
SELECT
    WorkorderId,
    AVG(Temperature) AS AvgTemp,
    MIN(Temperature) AS MinTemp,
    MAX(Temperature) AS MaxTemp
INTO [asa-out-machine-temperatures]
FROM [asa-in] TIMESTAMP BY EventEnqueuedUtcTime
GROUP BY
    WorkorderId, TumblingWindow(minute , 5)

-- błędy w 15 minutowym okienku
SELECT ih.IoTHub.ConnectionDeviceId, COUNT(message_type) as errors
INTO [asa-out-error-per-machine]
FROM [asa-in] ih TIMESTAMP by EventEnqueuedUtcTime
WHERE message_type = 'event'
GROUP BY
    message_type, ih.IoTHub.ConnectionDeviceId, TumblingWindow(minute , 15)
HAVING count(message_type) > 3

--- awaryjne zatrzymanie dla funkcji
SELECT ih.IoTHub.ConnectionDeviceId, COUNT(message_type) as errors_count
INTO [asa-out-emergency-stop-http-trigger]
FROM [asa-in] ih TIMESTAMP by EventEnqueuedUtcTime
WHERE message_type = 'event'
GROUP BY
    message_type, ih.IoTHub.ConnectionDeviceId, TumblingWindow(minute , 15)

-- production kpi dla funkcji
SELECT
    (SUM(GoodCount) / (SUM(GoodCount) + SUM(BadCount))) AS kpi,
    System.Timestamp() AS WindowEndTime
INTO [asa-out-production-kpi-http-trigger]
FROM [asa-in] TIMESTAMP BY EventEnqueuedUtcTime
GROUP BY
    TumblingWindow(minute , 15)

```

Wszelkie kalkulacje i logika zrobinona została za pomocą tych kwerend oraz funkcji, które można znaleść w katalogu asa i functions.
