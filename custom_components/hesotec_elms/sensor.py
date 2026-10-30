"""Leistung, Strom, Energie der Sitzung — und wann zuletzt gemeldet wurde."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import ElmsEintrag
from .entitaet import Ladepunktentitaet, anzulegen, matteroption
from .koordinator import Ladepunktkoordinator
from .ladepunkt import Ladepunkt


@dataclass(frozen=True, kw_only=True)
class Messgroesse(SensorEntityDescription):
    """Eine Zahl am Ladepunkt und wie man sie herausholt."""

    wert: Callable[[Ladepunkt], float | datetime | None]


MESSGROESSEN: tuple[Messgroesse, ...] = (
    Messgroesse(
        key="leistung",
        translation_key="leistung",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        wert=lambda p: p.leistung_angezeigt,
    ),
    Messgroesse(
        key="strom",
        translation_key="strom",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        wert=lambda p: p.strom_angezeigt,
    ),
    # TOTAL_INCREASING UND NICHT TOTAL: die Zahl ist die Energie der
    # LAUFENDEN Sitzung und springt beim nächsten Ladevorgang auf 0 zurück.
    # Mit `total` hielte Home Assistant jeden Rücksprung für einen Fehler;
    # mit `total_increasing` ist er genau das erwartete Verhalten und wird
    # als neuer Zyklus gezählt.
    Messgroesse(
        key="sitzungsenergie",
        translation_key="sitzungsenergie",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        wert=lambda p: p.energie_kwh,
    ),
    # DAS ALTER GEHÖRT ZU DEN MESSWERTEN DAZU. Die Daten kommen höchstens
    # alle 20 Sekunden; ein Wert ohne seinen Zeitpunkt behauptet mehr, als
    # das Portal weiß. Als eigener Sensor ist er außerdem das, womit sich
    # eine Automatisierung gegen ein stilles Gerät absichern lässt.
    Messgroesse(
        key="stand",
        translation_key="stand",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        wert=lambda p: _mit_zeitzone(p.stand),
    ),
)


def _mit_zeitzone(wert: datetime | None) -> datetime | None:
    """Macht aus der Portalzeit eine zonenbehaftete Zeit.

    **Das Portal sendet ohne Zeitzone** — die Anwendung rechnet durchgehend
    in Ortszeit, und ``System.Text.Json`` schreibt ein ``DateTime`` ohne
    Kennzeichen dann als ``2026-10-30T09:25:23``. Ein Zeitstempelsensor
    verlangt in Home Assistant aber eine zonenbehaftete Zeit, sonst wird
    der Wert verworfen.

    **Nicht ``dt_util.as_local``**: das deutet eine zonenlose Zeit als UTC
    und verschöbe sie damit um ein bis zwei Stunden — im Winter anders als
    im Sommer, was die Sache beim Suchen noch schöner macht. Richtig ist,
    sie als das zu kennzeichnen, was sie ist: Ortszeit.

    Die Annahme dahinter: Home Assistant steht in derselben Zeitzone wie
    das Portal. Für eine Anlage und ihre Hausautomation trifft das zu;
    deshalb ist dieser Sensor auch der einzige, der standardmäßig
    abgeschaltet ist.
    """
    if wert is None:
        return None

    if wert.tzinfo is not None:
        return wert

    return wert.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)


async def async_setup_entry(
    hass: HomeAssistant,
    eintrag: ElmsEintrag,
    hinzufuegen: AddEntitiesCallback,
) -> None:
    """Legt je Ladepunkt die Messgrößen an."""
    koordinator = eintrag.runtime_data

    hinzufuegen(
        Messwert(koordinator, p, beschreibung)
        for p in anzulegen(koordinator, matteroption(dict(eintrag.options)))
        for beschreibung in MESSGROESSEN
    )


class Messwert(Ladepunktentitaet, SensorEntity):
    """Eine Zahl, die der Koordinator schon geholt hat."""

    entity_description: Messgroesse

    def __init__(
        self,
        koordinator: Ladepunktkoordinator,
        punkt: Ladepunkt,
        beschreibung: Messgroesse,
    ) -> None:
        super().__init__(koordinator, punkt)
        self.entity_description = beschreibung
        self._attr_unique_id = f"{punkt.seriennummer}_{beschreibung.key}"

    @property
    def native_value(self) -> float | datetime | None:
        punkt = self.punkt
        return None if punkt is None else self.entity_description.wert(punkt)
