# SolarEco Telnet - Custom Component for Home Assistant

Moderní integrace pro monitorování MPPT regulátoru SolarEco s konfigurací přes UI.

## O projektu

Tento projekt je **nástupce** původní integrace [solareco-homeassistant](https://gitea.solareco.cz/test/solareco-homeassistant), která používala konfiguraci přes `configuration.yaml`. 

**Původní autor:** SolarEco team  
**Nástupce a modernizace:** Pavel Tresnak

### Hlavní vylepšení oproti originálu:
- ✅ Konfigurace přes Home Assistant UI místo YAML
- ✅ Podpora pro více zařízení současně
- ✅ Automatické seskupení všech senzorů pod jedno zařízení
- ✅ Modernizovaný kód pro aktuální verze Home Assistantu
- ✅ HACS kompatibilní struktura
- ✅ České i anglické překlady

Děkujeme původním autorům za vytvoření základu této integrace!

## Co je Home Assistant?

[Home Assistant](https://www.home-assistant.io/) je open-source platforma pro automatizaci chytré domácnosti, která funguje jako centrální hub pro propojení a ovládání různých zařízení.

## Vlastnosti

### Podporované senzory

- **Napětí (Voltage)** - Monitoruje napětí MPPT regulátoru
- **Proud (Current)** - Měří proud procházející regulátorem
- **Výkon (Power)** - Vypočítává spotřebu energie regulátoru
- **Teplota chladiče (Cooler Temperature)** - Hlásí teplotu chladiče
- **Teplota bojleru (Boiler Temperature)** - Hlásí teplotu bojleru
- **Denní energie (Day Energy)** - Monitoruje denní výrobu energie
- **Celková energie (Total Energy)** - Celková vyrobená energie
- **Relé (Relay)** - Stav relé regulátoru
- **Šířka impulsu (Pulse Width)** - Šířka PWM impulsu
- **Ventilátor (Fan)** - Stav ventilátoru

## Instalace

### Metoda 1: Manuální instalace

1. Vytvořte adresář `solareco_telnet` v `/config/custom_components/`
2. Zkopírujte všechny soubory do tohoto adresáře:
   - `__init__.py`
   - `manifest.json`
   - `config_flow.py`
   - `sensor.py`
   - `strings.json`
   - `translations/` (celý adresář s `en.json` a `cs.json`)
3. **Restartujte Home Assistant** (důležité!)
4. Vyprázdněte cache prohlížeče (Ctrl+F5 nebo Ctrl+Shift+R)
5. Přejděte do **Nastavení → Zařízení a služby → Přidat integraci**

### Metoda 2: Přes HACS (pokud je integrace publikována)

1. Otevřete HACS v Home Assistantu
2. Přejděte do sekce "Integrations"
3. Klikněte na "Explore & Download Repositories"
4. Vyhledejte "SolarEco Telnet"
5. Klikněte na "Download"
6. Restartujte Home Assistant

## Konfigurace

### Přidání integrace

1. V Home Assistantu přejděte do **Nastavení** → **Zařízení a služby**
2. Klikněte na tlačítko **+ PŘIDAT INTEGRACI** v pravém dolním rohu
3. Vyhledejte **SolarEco Telnet**
4. Zadejte konfigurační údaje:
   - **IP adresa** - IP adresa vašeho SolarEco regulátoru (např. 192.168.1.100)
   - **Port** - Port pro telnet připojení (výchozí: 23)
   - **Interval dotazování** - Jak často se mají data načítat v sekundách (výchozí: 5)
   - **Timeout** - Časový limit pro připojení v sekundách (výchozí: 10)
5. Klikněte na **ODESLAT**

Integrace se automaticky připojí k zařízení a vytvoří všechny dostupné senzory.

### Přidání na dashboard

1. Přejděte na záložku **Přehled**
2. Klikněte na tři tečky v pravém horním rohu a zvolte **Upravit řídicí panel**
3. Klikněte na **+ PŘIDAT KARTU**
4. Vyberte **Entity** nebo jinou kartu dle preference
5. Vyberte entity začínající na `sensor.solareco_*`
6. Klikněte na **ULOŽIT**

## Příklad použití

Po úspěšné instalaci a konfiguraci budete mít k dispozici entity jako:

- `sensor.solareco_voltage` - Aktuální napětí
- `sensor.solareco_current` - Aktuální proud
- `sensor.solareco_power` - Aktuální výkon
- `sensor.solareco_cooler_temperature` - Teplota chladiče
- `sensor.solareco_boiler_temperature` - Teplota bojleru
- `sensor.solareco_day_energy` - Denní energie
- `sensor.solareco_total_energy` - Celková energie
- A další...

## Odstraňování problémů

### Integrace se nemůže připojit k zařízení

- Zkontrolujte, zda je IP adresa správná
- Ověřte, že port 23 (telnet) je dostupný
- Ujistěte se, že zařízení je zapnuté a dostupné v síti
- Zkuste zvýšit timeout v nastavení

### Senzory ukazují "Nedostupné"

- Zkontrolujte logy Home Assistantu v **Nastavení** → **Systém** → **Logy**
- Po třech po sobě jdoucích neúspěšných pokusech o připojení jsou senzory označeny jako nedostupné
- Zkontrolujte síťové připojení k zařízení

### Změna konfigurace

Pro změnu konfigurace (např. IP adresy nebo intervalu):

1. Přejděte do **Nastavení** → **Zařízení a služby**
2. Najděte kartu **SolarEco Telnet**
3. Klikněte na tři tečky a zvolte **Odstranit**
4. Přidejte integraci znovu s novými údaji

## Technické informace

- **Doména:** `solareco_telnet`
- **Verze:** 2.0.0
- **IoT třída:** `local_polling`
- **Platforma:** sensor
- **Komunikační protokol:** Telnet (TCP port 23)

## Změny oproti původní verzi

- ✅ Konfigurace přes UI místo configuration.yaml
- ✅ Změna domény z `solareco` na `solareco_telnet`
- ✅ Podpora pro více zařízení současně
- ✅ Automatické seskupení senzorů pod jedno zařízení
- ✅ Modernizovaný kód pro nové verze Home Assistantu (2024+)
- ✅ České překlady v UI
- ✅ Snadnější instalace a správa
- ✅ HACS kompatibilita
- ✅ Lepší error handling a logování

**Poznámka:** Pokud používáte původní integraci `solareco`, budete muset po instalaci této verze zařízení přidat znovu přes UI.

## Podpora

Pro hlášení problémů nebo návrhy na vylepšení použijte:
- [GitHub Issues](https://github.com/paveltresnak/solareco_telnet/issues)
- [GitHub Repository](https://github.com/paveltresnak/solareco_telnet)

## Licence

Tento projekt je open-source software. 

**Důležité:** Pokud jste původní autor nebo máte připomínky k licencování, prosím kontaktujte mě přes [GitHub Issues](https://github.com/paveltresnak/solareco_telnet/issues).

## Autoři a poděkování

- **Původní integrace:** [SolarEco team](https://gitea.solareco.cz/test/solareco-homeassistant)
- **Modernizace a údržba:** Pavel Tresnak

Děkuji původním autorům za vytvoření základu této integrace!
