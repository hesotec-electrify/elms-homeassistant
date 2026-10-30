"""Ein Ladepunkt, wie ihn die Portalschnittstelle liefert.

OHNE JEDEN BEZUG AUF HOME ASSISTANT, und das ist Absicht: hier steckt die
ganze Auslegung der Antwort — wann ein Wert fehlt, was ``null`` bedeutet,
wie aus Wattstunden Kilowattstunden werden. Dieses Stück lässt sich ohne
installiertes Home Assistant prüfen, und genau das tut ``pruefung/``.

Die Feldnamen kommen in camelCase aus dem Portal (ASP.NET Core serialisiert
so). Sie sind **veröffentlicht**: dieselbe Antwortform liest das
Homebridge-Plugin auf Raspberry Pis, die beim Ausrollen des Portals nicht
mitkommen. Wer hier ein Feld vermisst, erweitert die Form im Portal — er
benennt nichts um.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Ladepunkt:
    """Der Stand eines Ladepunkts zu einem Zeitpunkt."""

    id: int
    name: str
    an: bool
    laedt: bool
    wartet_auf_freigabe: bool
    erreichbar: bool
    leistung_watt: float | None
    strom_ampere: float | None
    energie_wattstunden: float
    stand: datetime | None
    seriennummer: str
    hinter_smartbox: bool
    smartbox_matter_aktiv: bool

    # ------------------------------------------------------------- Umrechnen

    @property
    def leistung_angezeigt(self) -> float:
        """Leistung in W — ``None`` wird zu ``0``.

        **``null`` heißt „es lädt nicht", nicht „unbekannt".** Das Portal
        gibt Leistung und Strom nur während eines Ladevorgangs heraus, weil
        die Spalten danach stehen bleiben und sonst eine stundenalte Messung
        behaupten würden. Für eine Messgröße in Home Assistant ist **0 W**
        deshalb die richtige Anzeige — ein ``unknown`` risse eine Lücke in
        die Statistik des Energiearmaturenbretts, obwohl der Wert bekannt
        ist: es fließt nichts.
        """
        return float(self.leistung_watt or 0)

    @property
    def strom_angezeigt(self) -> float:
        """Größter Phasenstrom in A — nach derselben Regel wie die Leistung."""
        return float(self.strom_ampere or 0)

    @property
    def energie_kwh(self) -> float:
        """Energie der laufenden Sitzung in kWh.

        Sie **springt auf 0 zurück**, wenn ein neuer Ladevorgang beginnt.
        Das ist kein Fehler, sondern die Natur der Zahl; die Entität trägt
        deshalb ``total_increasing`` und nicht ``total``.
        """
        return round(self.energie_wattstunden / 1000, 3)

    # ------------------------------------------------------------- Einlesen

    @classmethod
    def aus_json(cls, zeile: dict) -> Ladepunkt:
        """Baut einen Ladepunkt aus einer Zeile der Portalantwort."""
        return cls(
            id=int(zeile["id"]),
            name=str(zeile.get("name") or zeile.get("seriennummer") or ""),
            an=bool(zeile.get("an")),
            laedt=bool(zeile.get("laedt")),
            wartet_auf_freigabe=bool(zeile.get("wartetAufFreigabe")),
            erreichbar=bool(zeile.get("erreichbar")),
            leistung_watt=_zahl(zeile.get("leistungWatt")),
            strom_ampere=_zahl(zeile.get("stromAmpere")),
            energie_wattstunden=float(_zahl(zeile.get("energieWattstunden")) or 0),
            stand=_zeitpunkt(zeile.get("stand")),
            seriennummer=str(zeile.get("seriennummer") or ""),
            hinter_smartbox=bool(zeile.get("hinterSmartbox")),
            smartbox_matter_aktiv=bool(zeile.get("smartboxMatterAktiv")),
        )


def _zahl(wert: object) -> float | None:
    """Eine Zahl oder ``None`` — und ``None`` bleibt ``None``.

    Nicht ``float(wert or 0)``: das machte aus einem fehlenden Wert eine
    Null, und der Unterschied zwischen beiden ist hier die ganze Aussage.
    """
    if wert is None:
        return None
    try:
        return float(wert)
    except (TypeError, ValueError):
        return None


def _zeitpunkt(wert: object) -> datetime | None:
    """Der Zeitstempel des Portals, oder ``None``.

    **Er kommt ohne Zeitzone** (die Anwendung rechnet durchgehend in
    Ortszeit). Hier wird er deshalb auch keiner zugeordnet — wer ihn
    anzeigt, zeigt ihn als das, was er ist: die Uhr des Portals.
    """
    if not isinstance(wert, str) or not wert:
        return None
    try:
        return datetime.fromisoformat(wert)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class Karte:
    """Eine Karte, wie sie das Portal zur Auswahl liefert.

    **Ohne Nummer im Klartext.** ``nummer`` ist die verdeckte Fassung, wie
    sie auch im Portal steht — eine Kartennummer ist ein Ausweis, und zur
    Auswahl genügt der Name.
    """

    id: int
    name: str
    nummer: str

    @property
    def beschriftung(self) -> str:
        """Was in der Auswahlliste steht."""
        if self.name and self.name != self.nummer:
            return f"{self.name} ({self.nummer})"
        return self.nummer or str(self.id)

    @classmethod
    def aus_json(cls, zeile: dict) -> "Karte":
        return cls(
            id=int(zeile["id"]),
            name=str(zeile.get("name") or ""),
            nummer=str(zeile.get("nummer") or ""),
        )
