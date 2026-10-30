"""Probe auf die Auslegung der Portalantwort.

OHNE HOME ASSISTANT UND OHNE PORTAL. Geprüft wird das Stück, in dem die
Entscheidungen stecken: was ``null`` bedeutet, wie aus Wattstunden
Kilowattstunden werden, was bei fehlenden Feldern passiert. Dafür braucht
es keine Testbibliothek und keinen Server — ``python
pruefung/ladepunkt_pruefen.py`` genügt, auf jedem Rechner.

Was hier NICHT geprüft wird, und das steht hier, damit es niemand für
geprüft hält: ob Home Assistant die Entitäten so anlegt, wie gedacht. Das
zeigt nur eine laufende Instanz.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

# UNMITTELBAR AUS DER DATEI, NICHT ÜBER DAS PAKET. Ein `from
# hesotec_elms.ladepunkt import …` führte zuerst `__init__.py` aus, und das
# holt Home Assistant herein — die Probe wäre damit genau an das gebunden,
# wovon sie sich freihalten soll.
_DATEI = (
    Path(__file__).resolve().parent.parent
    / "custom_components" / "hesotec_elms" / "ladepunkt.py"
)
_SPEZIFIKATION = importlib.util.spec_from_file_location("ladepunkt", _DATEI)
_MODUL = importlib.util.module_from_spec(_SPEZIFIKATION)

# VOR dem Ausführen in `sys.modules` eintragen: `@dataclass` sieht dort
# nach, um den Namensraum seiner eigenen Klasse aufzulösen. Ohne diese
# Zeile scheitert schon der Import, und zwar mit einer Meldung aus den
# Innereien von `dataclasses`, die nichts mit der Ursache zu tun hat.
sys.modules[_SPEZIFIKATION.name] = _MODUL
_SPEZIFIKATION.loader.exec_module(_MODUL)

Ladepunkt = _MODUL.Ladepunkt

FEHLER: list[str] = []


def gleich(was: str, ist: object, soll: object) -> None:
    if ist != soll:
        FEHLER.append(f"{was}: {ist!r} statt {soll!r}")


# Eine Zeile, wie das Portal sie liefert (camelCase, Zeit ohne Zone).
LAEDT = {
    "id": 17,
    "name": "LP 8",
    "an": True,
    "laedt": True,
    "erreichbar": True,
    "leistungWatt": 11040.0,
    "stromAmpere": 16.0,
    "energieWattstunden": 21288.0,
    "stand": "2026-10-30T09:25:23",
    "seriennummer": "15061724",
    "hinterSmartbox": False,
    "smartboxMatterAktiv": False,
}

# Derselbe Ladepunkt, wenn nichts lädt: Leistung und Strom fehlen.
RUHT = dict(LAEDT, laedt=False, leistungWatt=None, stromAmpere=None,
            energieWattstunden=0.0)


def main() -> int:
    # -------------------------------------------------------------- Einlesen
    p = Ladepunkt.aus_json(LAEDT)

    gleich("Kennung", p.id, 17)
    gleich("Name", p.name, "LP 8")
    gleich("Seriennummer", p.seriennummer, "15061724")
    gleich("Leistung", p.leistung_watt, 11040.0)
    gleich("Zeitpunkt", p.stand, datetime(2026, 10, 30, 9, 25, 23))
    gleich("Zeitpunkt ohne Zone", p.stand.tzinfo if p.stand else "?", None)

    # ------------------------------------------------- null heisst nicht null
    r = Ladepunkt.aus_json(RUHT)

    # Roh bleibt der Unterschied erhalten …
    gleich("ruhend: Leistung roh", r.leistung_watt, None)
    gleich("ruhend: Strom roh", r.strom_ampere, None)

    # … und erst für die Anzeige wird daraus eine 0.
    gleich("ruhend: Leistung angezeigt", r.leistung_angezeigt, 0.0)
    gleich("ruhend: Strom angezeigt", r.strom_angezeigt, 0.0)

    # ------------------------------------------------------------- Umrechnen
    gleich("Energie in kWh", p.energie_kwh, 21.288)
    gleich("Energie gerundet", Ladepunkt.aus_json(
        dict(LAEDT, energieWattstunden=1234.5678)).energie_kwh, 1.235)

    # ------------------------------------------------------- Fehlende Felder
    karg = Ladepunkt.aus_json({"id": 3, "seriennummer": "99"})

    gleich("karg: Name faellt auf die Seriennummer zurueck", karg.name, "99")
    gleich("karg: an", karg.an, False)
    gleich("karg: erreichbar", karg.erreichbar, False)
    gleich("karg: Energie", karg.energie_wattstunden, 0.0)
    gleich("karg: Zeitpunkt", karg.stand, None)

    # ---------------------------------------------------------- Unfug im Feld
    wirr = Ladepunkt.aus_json(dict(LAEDT, leistungWatt="viel", stand="gestern"))

    gleich("wirrer Zahlenwert wird None", wirr.leistung_watt, None)
    gleich("wirrer Zeitpunkt wird None", wirr.stand, None)

    # -------------------------------------------------------------- Ergebnis
    if FEHLER:
        for f in FEHLER:
            print("FEHLER:", f)
        print(f"\n{len(FEHLER)} Abweichung(en).")
        return 1

    print("Portalantwort: 16 Prüfungen, keine Abweichung.")
    print("In Ordnung.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
