"""Was alle Entitäten dieser Integration gemeinsam haben."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BEREICH, FELD_AUCH_HINTER_MATTER, HERSTELLER
from .koordinator import Ladepunktkoordinator
from .ladepunkt import Ladepunkt


class Ladepunktentitaet(CoordinatorEntity[Ladepunktkoordinator]):
    """Eine Entität, die zu genau einem Ladepunkt gehört."""

    _attr_has_entity_name = True

    def __init__(self, koordinator: Ladepunktkoordinator, punkt: Ladepunkt) -> None:
        super().__init__(koordinator)
        self._kennung = punkt.id

        # DIE SERIENNUMMER UND NICHT DIE KENNUNG. Die Bezeichnung eines
        # Ladepunkts darf sich im Portal jederzeit ändern, die Seriennummer
        # nicht — sie steht am Gerät. Eine Entität, die ihre Identität an
        # einen änderbaren Namen hängt, verliert beim Umbenennen ihren
        # Verlauf.
        self._seriennummer = punkt.seriennummer

        self._attr_device_info = DeviceInfo(
            identifiers={(BEREICH, punkt.seriennummer)},
            name=punkt.name,
            manufacturer=HERSTELLER,
            serial_number=punkt.seriennummer,
        )

    @property
    def punkt(self) -> Ladepunkt | None:
        """Der aktuelle Stand — oder ``None``, wenn er verschwunden ist."""
        return self.coordinator.data.get(self._kennung)

    @property
    def available(self) -> bool:
        """Erreichbar heißt: das Gerät hat sich in der Frist gemeldet.

        **Nicht „aus".** Ein Ladepunkt ohne Netz ist nicht pausiert, und ihn
        als „aus" zu zeigen wäre dieselbe Verwechslung, die im Portal selbst
        schon einmal auf dem Dashboard stand: eine Pause sah aus wie eine
        Störung. ``unavailable`` sagt, was wirklich der Fall ist — wir
        wissen es gerade nicht.
        """
        punkt = self.punkt
        return super().available and punkt is not None and punkt.erreichbar


def anzulegen(koordinator: Ladepunktkoordinator, auch_hinter_matter: bool) -> list[Ladepunkt]:
    """Die Ladepunkte, für die Entitäten entstehen sollen.

    Hinter einer SmartBox mit eigener Matter-Brücke steht der Ladepunkt
    sonst zweimal in Home Assistant — einmal hierüber, einmal über Matter.
    Wer beides will, schaltet es in den Einstellungen ein.
    """
    alle = list(koordinator.data.values())

    if auch_hinter_matter:
        return alle

    return [p for p in alle if not p.smartbox_matter_aktiv]


def matteroption(eintrag_optionen: dict) -> bool:
    """Liest die Matter-Einstellung aus einem Eintrag."""
    return bool(eintrag_optionen.get(FELD_AUCH_HINTER_MATTER, False))
