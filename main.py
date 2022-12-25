from ustawienia import Ustawienia
from asyncua import Client
import asyncio
from agent import Agent

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
      for agent in agenci:
        nazwa =(await agent.urzadzenie.read_browse_name()).Name
        print(nazwa)
        await agent.telemetria()
      await asyncio.sleep(5)

if __name__ == "__main__":
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())