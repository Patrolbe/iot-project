from ustawienia import Ustawienia
from asyncua import Client
import asyncio
async def main():
  ustawienia = Ustawienia()
  url = ustawienia.pobierz('url')



if __name__ == "__main__":
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())