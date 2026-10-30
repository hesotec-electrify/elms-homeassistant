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
    """Die Pause, und sonst nichts: „Laden erlaubt".

    **„Aus" heißt von Hand pausiert**, „An" heißt es nicht. Das Portal liest
    dafür ``PauseUrsache = 'hand'`` und nicht den allgemeinen Pausemerker,
    damit der Schalter für das steht, was ein Mensch zuletzt wollte, statt
    sich umzulegen, sobald das Fahrzeug eine Ladepause macht.

    **Er hieß bis zum 30.10.2026 „Freigabe", und das war falsch** (Befund
    des Betreibers). Auf derselben Karte stand das Wort dann für zwei
    verschiedene Dinge: hier für die Pause, bei „Wartet auf Freigabe" und
    „Freigabe senden" für die Autorisierung. Das Portal selbst nennt diesen
    Schalter auch gar nicht so — dort heißen die Knöpfe „Pausieren" und
    „Pause aufheben".

    **Die Polarität blieb, als der Name wechselte.** „Pause" wäre noch näher
    am Portal gewesen, hieße aber An = pausiert — und eine Entität, die ihre
    Bedeutung umdreht, zerschießt stillschweigend jede Automatisierung, die
    es schon gibt. Die Kennung (``…_freigabe``) blieb aus demselben Grund:
    sie traegt den Verlauf.

    Ob gerade Strom fließt, sagt „Lädt" daneben. Ob eine Autorisierung
    fehlt, sagt „Wartet auf Freigabe" — und dagegen hilft dieser Schalter
    nicht.
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
