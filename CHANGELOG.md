# Changelog

All notable changes to this project will be documented in this file.

Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [3.0.0] — 2026-04-19

Velký interní refactoring — kompletní přepis transportní vrstvy a state managementu. **Entity IDs a unique_ids zachované** (žádný history loss), ale interní architektura se změnila natolik, že si zaslouží major bump.

### Changed (interní, žádné breaking pro uživatele)
- **Odstraněn `telnetlib`** — Python 3.11 ho deprecatoval, 3.13 ho odstranil (PEP 594).
  Integrace by po upgradu HA na Py3.13 přestala fungovat.
  Nahrazen `asyncio.open_connection()` (stdlib, async).
- **`DataUpdateCoordinator`** místo custom `SensorConnector` + `async_track_time_interval` + dispatcher.
  Standardní HA pattern. Úspora ~80 řádků, lepší integrace se zbytkem HA (last_update_success, available).
- **Regex patterns precompiled** v novém modulu `parsers.py` jako `re.Pattern` konstanty.
  Dříve se regex kompiloval při každém update cyklu (~20× za 5 s). Čitelnější + testovatelné.
- **`SensorEntityDescription` dataclasses** místo `SolarecoSensorConfig` custom class.
  Standard HA pattern; `icon`, `device_class`, `state_class` spravované HA.
- **Úzké exception types** — `asyncio.TimeoutError`, `OSError`, `ConnectionError` místo bare `Exception`.
- **Lazy logging formatting** — `%s` placeholder místo `f"..."` v `_LOGGER.debug/warning`.
  Efektivnější když debug level není aktivní.
- **CoordinatorEntity base class** pro senzory — méně ručního dispatcheru.

### Preserved
- **Entity unique_ids** — zachované ve formátu `{entry_id}_{sensor_name}`, žádný history loss.
- **Backoff schedule** (3 pokusy + 10/30/60/120/300 s) — zachována jako v2.2.0.
- **Pause at night** — sun.sun `below_horizon` detekce + auto resume.
- **Options flow** — poll_interval, timeout, pause_at_night runtime configurable.
- **Překlady** — cs.json, en.json (v2.2.0 stav).

### Fixed
- **Blocking I/O v HA eventloop** — `telnetlib.Telnet(...)` se sice volal přes `async_add_executor_job`,
  ale nyní běží plně async přes `asyncio.open_connection()`. Žádný executor overhead.

### Technical
- `codeowners: ["@paveltresnak"]` doplněno v manifest.json.
- Nové soubory: `coordinator.py`, `parsers.py`.

## [2.2.0] — 2026-04

### Added
- **Backoff strategy** při opakovaných chybách spojení — 3 pokusy pak progresivní pauza (10 s → 5 min).
  Zabraňuje zbytečnému spamu do logu když je wallbox offline.
- **Pause at night** — volba v config flow. Když `sun.sun = below_horizon`, integrace se nepřipojuje.

## [2.1.0] — dřívější

### Added
- Options flow pro runtime změnu poll_interval / timeout / pause_at_night.

## [2.0.0] — dřívější

### Changed (breaking z 1.x)
- **Konfigurace přes UI** místo `configuration.yaml`.
- **Doména přejmenována** `solareco` → `solareco_telnet`.
- HACS kompatibilní struktura.
- DeviceInfo grupování senzorů pod jedno zařízení.

### Added
- České + anglické překlady.
- Více zařízení současně (per-entry config).
- `_consecutive_errors` counter (3 pokusy → unavailable).
