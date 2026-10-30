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

    hinzufuegen(
        Ladeanzeige(koordinator, p)
        for p in anzulegen(koordinator, matteroption(dict(eintrag.options)))
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
