"""hesotec electrify — Ladepunkte in Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    FELD_ADRESSE,
    FELD_SCHLUESSEL,
    FELD_TAKT,
    VORGABE_TAKT,
)
from .koordinator import Ladepunktkoordinator
from .portal import Portal

PLATTFORMEN: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]

type ElmsEintrag = ConfigEntry[Ladepunktkoordinator]


async def async_setup_entry(hass: HomeAssistant, eintrag: ElmsEintrag) -> bool:
    """Richtet einen Portalzugang ein."""
    portal = Portal(
        async_get_clientsession(hass),
        eintrag.data[FELD_ADRESSE],
        eintrag.data[FELD_SCHLUESSEL],
    )

    takt = eintrag.options.get(FELD_TAKT, VORGABE_TAKT)

    koordinator = Ladepunktkoordinator(hass, eintrag, portal, takt)

    # Vor dem Anlegen der Entitäten einmal abrufen: ohne Daten wüsste
    # niemand, welche Ladepunkte es überhaupt gibt, und Home Assistant
    # legte eine leere Integration an, die erst nach dem ersten Takt
    # Geräte bekäme.
    await koordinator.async_config_entry_first_refresh()

    eintrag.runtime_data = koordinator

    await hass.config_entries.async_forward_entry_setups(eintrag, PLATTFORMEN)

    # Eine Änderung an den Einstellungen (Takt, Matter) wirkt erst beim
    # Neuladen — und der Horcher sorgt dafür, dass es von selbst passiert.
    eintrag.async_on_unload(eintrag.add_update_listener(_neu_laden))

    return True


async def async_unload_entry(hass: HomeAssistant, eintrag: ElmsEintrag) -> bool:
    """Räumt einen Portalzugang ab."""
    return await hass.config_entries.async_unload_platforms(eintrag, PLATTFORMEN)


async def _neu_laden(hass: HomeAssistant, eintrag: ElmsEintrag) -> None:
    await hass.config_entries.async_reload(eintrag.entry_id)
