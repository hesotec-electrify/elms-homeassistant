"""Die Taste „Freigabe senden"."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ElmsEintrag
from .const import FELD_KARTEN
from .entitaet import Ladepunktentitaet, anzulegen, matteroption
from .koordinator import Ladepunktkoordinator
from .ladepunkt import Ladepunkt
from .portal import Portalfehler


async def async_setup_entry(
    hass: HomeAssistant,
    eintrag: ElmsEintrag,
    hinzufuegen: AddEntitiesCallback,
) -> None:
    """Legt die Taste nur dort an, wo eine Karte hinterlegt ist.

    **Kein Knopf ohne Karte.** Eine Taste, die beim Drücken zuverlässig
    scheitert, ist schlechter als keine — und was sie freigeben soll, kann
    sie sich nicht aussuchen: ``AddAuth`` im Portal trägt genau eine Karte.
    Zugeordnet wird sie in den Einstellungen der Integration.
    """
    koordinator = eintrag.runtime_data
    karten: dict = dict(eintrag.options).get(FELD_KARTEN) or {}

    hinzufuegen(
        Freigabetaste(koordinator, p, int(karten[p.seriennummer]))
        for p in anzulegen(koordinator, matteroption(dict(eintrag.options)))
        if karten.get(p.seriennummer)
    )


class Freigabetaste(Ladepunktentitaet, ButtonEntity):
    """Schickt die hinterlegte Karte an den Ladepunkt.

    **Sie hebt keine Pause auf**, und der Schalter daneben schickt keine
    Freigabe. Das sind zwei verschiedene Lagen mit zwei verschiedenen
    Handgriffen, und ein Bedienelement, das je nach unsichtbarem Zustand
    das eine oder das andere täte, wäre in einer Automatisierung nicht mehr
    vorhersagbar.

    Wann sie gebraucht wird, sagt der Sensor *Wartet auf Freigabe*.
    """

    _attr_translation_key = "freigabe_senden"

    def __init__(
        self,
        koordinator: Ladepunktkoordinator,
        punkt: Ladepunkt,
        karte: int,
    ) -> None:
        super().__init__(koordinator, punkt)
        self._karte = karte
        self._attr_unique_id = f"{punkt.seriennummer}_freigabe_senden"

    async def async_press(self) -> None:
        try:
            await self.coordinator.portal.freigeben(self._kennung, self._karte)
        except Portalfehler as fehler:
            # Vier Lagen kommen hier als 403 an: keine verwaltende Rolle,
            # fremder Mandant, gesperrte Karte, oder es steht schon eine
            # Freigabe aus. Welche es war, sagt nur der Text — deshalb geht
            # er unverändert weiter.
            raise HomeAssistantError(fehler.text or str(fehler)) from fehler

        # Der Auftrag wird in die Datenbank geschrieben und vom Dienst im Takt
        # abgeholt. Nachsehen lohnt sich also gleich, aber das Ergebnis steht
        # erst, wenn das Gerät geantwortet hat.
        await self.coordinator.async_request_refresh()
