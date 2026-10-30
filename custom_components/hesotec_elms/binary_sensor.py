"""Läuft gerade ein Ladevorgang?"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ElmsEintrag
from .entitaet import Ladepunktentitaet, anzulegen, matteroption
from .koordinator import Ladepunktkoordinator
from .ladepunkt import Ladepunkt


async def async_setup_entry(
    hass: HomeAssistant,
    eintrag: ElmsEintrag,
    hinzufuegen: AddEntitiesCallback,
) -> None:
    """Legt je Ladepunkt einen Ladeanzeiger an."""
    koordinator = eintrag.runtime_data

    punkte = anzulegen(koordinator, matteroption(dict(eintrag.options)))

    hinzufuegen(
        [
            *(Ladeanzeige(koordinator, p) for p in punkte),
            *(Freigabeanzeige(koordinator, p) for p in punkte),
        ]
    )


class Ladeanzeige(Ladepunktentitaet, BinarySensorEntity):
    """Fließt Strom?

    Das ist die Hälfte der Auskunft, die der Schalter **nicht** gibt: er
    steht auf „freigegeben", hier steht „lädt". Beides zusammen beschreibt
    den Ladepunkt; eines allein führt in die Irre.
    """

    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
    _attr_translation_key = "laedt"

    def __init__(self, koordinator: Ladepunktkoordinator, punkt: Ladepunkt) -> None:
        super().__init__(koordinator, punkt)
        self._attr_unique_id = f"{punkt.seriennummer}_laedt"

    @property
    def is_on(self) -> bool | None:
        punkt = self.punkt
        return None if punkt is None else punkt.laedt


class Freigabeanzeige(Ladepunktentitaet, BinarySensorEntity):
    """Wartet eine Säule auf die Autorisierung?

    **Das ist der dritte Grund, aus dem ein Ladepunkt nicht lädt** — und der
    einzige, den man weder am Schalter noch am Ladeanzeiger sieht. Von Hand
    pausiert: Pause aufheben. Vom Fahrzeug pausiert: nichts tun, es geht
    weiter. Auf Autorisierung wartend: eine Freigabe schicken. Wer hier den
    Schalter umlegt, ändert nichts, und das ohne Rückmeldung.

    **Ohne `device_class`**, denn es ist keine Störung. Eine Säule, die nach
    einer Berechtigung fragt, tut genau das, was sie soll.
    """

    _attr_translation_key = "wartet_auf_freigabe"

    def __init__(self, koordinator: Ladepunktkoordinator, punkt: Ladepunkt) -> None:
        super().__init__(koordinator, punkt)
        self._attr_unique_id = f"{punkt.seriennummer}_wartet_auf_freigabe"

    @property
    def is_on(self) -> bool | None:
        punkt = self.punkt
        return None if punkt is None else punkt.wartet_auf_freigabe
