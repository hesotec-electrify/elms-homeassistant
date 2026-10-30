"""Der Schalter: freigeben oder pausieren."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ElmsEintrag
from .entitaet import Ladepunktentitaet, anzulegen, matteroption
from .koordinator import Ladepunktkoordinator
from .ladepunkt import Ladepunkt
from .portal import Portal, Portalfehler


async def async_setup_entry(
    hass: HomeAssistant,
    eintrag: ElmsEintrag,
    hinzufuegen: AddEntitiesCallback,
) -> None:
    """Legt je Ladepunkt einen Schalter an."""
    koordinator = eintrag.runtime_data

    hinzufuegen(
        Freigabeschalter(koordinator, p)
        for p in anzulegen(koordinator, matteroption(dict(eintrag.options)))
    )


class Freigabeschalter(Ladepunktentitaet, SwitchEntity):
    """„An" heißt freigegeben, nicht „lädt".

    **Das ist der Unterschied, an dem sich jeder einmal vergreift.** Eine
    Säule kann freigegeben sein und niemand steckt an; sie kann laden und
    freigegeben sein. „Aus" heißt: **von Hand pausiert** — das Portal liest
    dafür ``PauseUrsache = 'hand'`` und nicht den allgemeinen Pausemerker,
    damit der Schalter für das steht, was ein Mensch zuletzt wollte, statt
    sich umzulegen, sobald das Fahrzeug eine Ladepause macht.

    Ob gerade Strom fließt, sagt der Sensor „Lädt" daneben.
    """

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_translation_key = "freigabe"

    def __init__(self, koordinator: Ladepunktkoordinator, punkt: Ladepunkt) -> None:
        super().__init__(koordinator, punkt)
        self._attr_unique_id = f"{punkt.seriennummer}_freigabe"

    @property
    def is_on(self) -> bool | None:
        punkt = self.punkt
        return None if punkt is None else punkt.an

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._schalten(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._schalten(False)

    async def _schalten(self, an: bool) -> None:
        portal: Portal = self.coordinator.portal

        try:
            await portal.schalten(self._kennung, an)
        except Portalfehler as fehler:
            # Die Begründung des Portals durchreichen und nicht übersetzen:
            # bei einem Schlüssel ohne verwaltende Rolle steht dort genau
            # der Satz, den auch die Maske zeigt.
            raise HomeAssistantError(fehler.text or str(fehler)) from fehler

        # NICHT den Zustand hier setzen und fertig: der Auftrag geht an echte
        # Hardware, und bis die Säule ihn bestätigt, vergeht ein Augenblick.
        # Das Portal antwortet mit „angenommen", nicht mit „erledigt". Ein
        # frischer Abruf zeigt, was wirklich steht — und wenn es noch nicht
        # umgesetzt ist, zeigt ihn der nächste Takt.
        await self.coordinator.async_request_refresh()
