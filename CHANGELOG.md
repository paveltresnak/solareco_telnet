# Changelog

All notable changes to this project will be documented in this file.

Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

CHANGELOG sestaven zpětně z GitHub releases 2025-10 až 2026-04.

## [3.0.2] — 2026-04-19

### Fixed
- **Potlačen warning „sun.sun entity not available" během startu HA.** Při restartu se integrace načítají paralelně; `sun.sun` se občas objeví o sekundu později než solareco_telnet coordinator. Dřívější verze zalogovala WARNING ihned při první absenci. Nyní se warning objeví až po **5 po sobě jdoucích chybách** (asi 25 s při 5s poll intervalu) — to odpovídá reálnému config problému, ne startup race. Při úspěšném nálezu se čítač nuluje a warning se znovu „nabije" pro případ pozdějšího výpadku.

## [3.0.1] — 2026-04-19

### Fixed
- Odstraněn znovu zavedený senzor `total_energy` (v v3.0.0 omylem vrácen do SENSORS). Regulátor tuto metriku neposkytuje — odpovídá stavu v2.1.3+.

## [3.0.0] — 2026-04-19

Velký interní refactoring — kompletní přepis transportní vrstvy a state managementu. **Entity IDs a unique_ids zachované** (žádný history loss), ale interní architektura se změnila natolik, že si zaslouží major bump.

### Changed (interní, žádné breaking pro uživatele)
- **Odstraněn `telnetlib`** — Python 3.11 ho deprecatoval, **Python 3.13 ho odstranil** (PEP 594). Integrace by po upgradu HA runtimu na Py3.13 přestala fungovat (import error). Nahrazen `asyncio.open_connection()` — stdlib, async, Py3.13-safe.
- **`DataUpdateCoordinator`** místo custom `SensorConnector` + `async_track_time_interval` + vlastní dispatcher. Standardní HA pattern. Úspora ~80 řádků, automatická integrace s HA (`last_update_success`, `available`).
- **Nový modul `parsers.py`** — regex patterns precompiled jako `re.Pattern` konstanty + pojmenované parser funkce. Dříve se regex kompiloval při každém update cyklu (~20× za 5 s). Testovatelné samostatně.
- **`SensorEntityDescription` dataclasses** místo `SolarecoSensorConfig` custom class. Standardní HA pattern.
- **Úzké exception types** — `asyncio.TimeoutError`, `OSError`, `ConnectionError` místo bare `Exception`.
- **Lazy logging formatting** — `%s` placeholder místo `f"..."` v `_LOGGER` voláních.
- **CoordinatorEntity base class** pro senzory — méně ručního dispatcheru.

### Preserved
- Entity `unique_ids` ve formátu `{entry_id}_{sensor_name}` → žádný history loss.
- Backoff schedule (3 pokusy pak 10/30/60/120/300 s) z v2.2.0.
- Pause at night (sun.sun `below_horizon` detekce) z v2.1.0+.
- Options flow (poll_interval, timeout, pause_at_night runtime configurable).
- CS + EN překlady.

### Fixed
- Blocking I/O v HA eventloop — `telnetlib.Telnet(...)` se sice volal přes `async_add_executor_job`, ale nyní běží plně async bez executor overhead.

### Doc
- Přidán tento `CHANGELOG.md`.
- `codeowners: ["@paveltresnak"]` v manifest.json.

## [2.2.0] — 2026-02-10

### Added
- **Exponenciální backoff** při nedostupnosti regulátoru. Po 3 neúspěšných pokusech progresivní prodloužení: 10 s → 30 s → 60 s → 2 min → 5 min (max).
- Zabraňuje zahlcení logu (dřív ~314 chyb za 25 min) a blokování worker vláken HA.

## [2.1.5] — 2025-10-29

### Fixed
- Kompatibilita s Home Assistant 2025.12 — odstraněno deprecated explicitní nastavení `config_entry` v `OptionsFlowHandler`. Ukládá se nyní do `_config_entry`.

## [2.1.4] — 2025-10-27

### Fixed
- Kompatibilita s Home Assistant 2025.12+ — automatický `self.config_entry` z rodičovské třídy, eliminace warningu.
- Přidán chybějící `callback` import v `config_flow.py`.

## [2.1.3] — 2025-10-24

### Added
- **Options Flow** — nastavení (`poll_interval`, `timeout`, `pause_at_night`) lze měnit v UI bez odstranění integrace.

### Fixed
- SyntaxWarnings v regex výrazech (raw strings).
- Chybějící sekce v `strings.json`.

### Removed
- Nefunkční senzor `total_energy` (regulátor tato data neposkytuje).

## [2.1.2] — 2025-10-23

### Added
- **Automatický noční režim** (re-release) — volitelné pozastavení dotazování, když je slunce pod horizontem (`sun.sun = below_horizon`). Výhody: čisté logy, úspora síťových prostředků. Fallback pokud není nakonfigurována lokace.

## [2.1.1] — 2025-10-23

### Added
- Automatický noční režim (re-release).

## [2.1.0] — 2025-10-23

### Added
- **Automatický noční režim** (první release) — `sun.sun` detekce, volitelná konfigurace.

## [2.0.1] — 2025-10-23

### Internal
- (opravy bez release notes)

## [2.0.0] — 2025-10-23

Velký přepis z v1 (YAML konfigurace).

### Changed (breaking z 1.x)
- **Konfigurace přes UI** místo `configuration.yaml`.
- **Doména přejmenována** `solareco` → `solareco_telnet`.
- HACS-kompatibilní struktura.

### Added
- DeviceInfo grupování senzorů pod jedno zařízení.
- Podpora více zařízení současně (per-entry config).
- `_consecutive_errors` counter (3 pokusy → unavailable).
- České + anglické překlady v UI.

### Migration
Pro existující uživatele: bylo potřeba odebrat starou integraci `solareco` z `configuration.yaml` a přidat znovu přes UI jako `solareco_telnet`.
