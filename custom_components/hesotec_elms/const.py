"""Feste Werte der Integration."""

from __future__ import annotations

from typing import Final

BEREICH: Final = "hesotec_elms"

# Die Einstellungsfelder — die Namen landen so im Eintrag und dürfen sich
# danach nicht mehr ändern, sonst verliert eine bestehende Einrichtung ihre
# Werte.
FELD_ADRESSE: Final = "adresse"
FELD_SCHLUESSEL: Final = "schluessel"
FELD_TAKT: Final = "takt"
FELD_AUCH_HINTER_MATTER: Final = "auch_hinter_matter"

# Die Karte je Ladepunkt, als {Seriennummer: Karten-Id}. Ueber die
# SERIENNUMMER und nicht ueber die ControllerId -- dieselbe Ueberlegung wie
# bei den Entitaetskennungen.
FELD_KARTEN: Final = "karten"

# DIE VORGABE IST NUR EIN VORSCHLAG IM FELD -- aber ein falscher Vorschlag
# kostet mehr als keiner. Hier stand ":8443", und dieser Port ist seit dem
# Umzug des Portals am 04.11.2026 zu (gemessen am 10.11.2026: 443 antwortet
# mit 401, 8443 gar nicht). Wer die Integration nach der Anleitung einrichtet,
# bekommt dann "das Portal antwortet nicht" -- und das sieht aus wie ein
# Fehler am Portal, nicht wie eine veraltete Zahl in einem Textfeld.
VORGABE_ADRESSE: Final = "https://elms.hesotec.de"

# DREISSIG SEKUNDEN, UND DAS IST KEIN KOMPROMISS. Die Messdaten kommen
# höchstens alle 20 Sekunden — der Dienst drängt schnelleren Geräten dieses
# Intervall auf. Ein engerer Takt fragt dieselbe Zahl zweimal ab; ein
# weiterer lässt den Schalter träge wirken.
VORGABE_TAKT: Final = 30
KLEINSTER_TAKT: Final = 10
GROESSTER_TAKT: Final = 600

HERSTELLER: Final = "HESOTEC"
