from configparser import ConfigParser

class Ustawienia:
  def __init__(self):
    self.config = ConfigParser()
    self.config.read('./config.ini')

  def zapisz(self):
    with open('./config.ini', 'w') as plik_konfiguracyjny:
        self.config.write(plik_konfiguracyjny)

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

