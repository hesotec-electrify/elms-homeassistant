# hesotec electrify für Home Assistant

<img src="brand/icon.png" alt="" width="72" align="right">

Ladepunkte aus dem **hesotec-electrify-Portal** in Home Assistant — zusehen,
pausieren, fortsetzen und eine hinterlegte Karte freigeben.

Je Ladepunkt entsteht ein Gerät mit sechs Entitäten: *Laden erlaubt* (Schalter),
*Lädt*, *Wartet auf Freigabe*, *Freigabe senden* (Taste), *Leistung* und *Strom*,
*Energie der Sitzung* sowie *Zuletzt gemeldet* (ab Werk abgeschaltet).

> **Die ausführliche Anleitung liefert das Portal selbst aus:**
> **<https://elms.hesotec.de/anleitungen/home-assistant.html>** — Einrichtung,
> die drei Fälle von „lädt nicht", vier Automatisierungen zum Abschreiben und
> was man besser lässt.

## Einbauen

**Seit Home Assistant 2026.11 steckt HACS in Home Assistant drin und heißt
Marketplace.** Welche Fassung läuft, steht unter *Einstellungen → Über* —
danach richtet sich der Weg.

### Ab 2026.11: über den Marketplace

1. **Einstellungen → Marketplace** (in der Seitenleiste steht er nicht),
   **Von Link hinzufügen**:
   `https://github.com/hesotec-electrify/elms-homeassistant`
2. Einmalig **mit GitHub anmelden** (Gerätecode). Für den Katalog braucht es
   das nicht, für ein eigenes Repository schon; gelesen wird nur Öffentliches.
3. „hesotec electrify" herunterladen, Home Assistant neu starten.

### Bis 2026.10: über HACS

1. In HACS **⋮ → Benutzerdefinierte Repositories** eintragen, Art
   **Integration**, dieselbe Adresse.
2. „hesotec electrify" herunterladen.
3. Home Assistant neu starten.

**HACS nachzuinstallieren lohnt nicht mehr**: ab 2026.11 blockiert Home
Assistant es, weil der Marketplace an seine Stelle tritt. Wer es heute nicht
hat, aktualisiert besser gleich Home Assistant — eine bestehende
HACS-Einrichtung wird dabei übernommen.

Über beide Wege meldet sich jede neue Fassung von selbst, und das
Aktualisieren kostet zwei Klicks statt eines Dateitauschs über Samba.

### Von Hand

Ohne beides den Ordner `custom_components/hesotec_elms` nach
`<config>/custom_components/` kopieren und Home Assistant neu starten. Wie die Dateien auf ein Home
Assistant OS kommen, steht in der Anleitung oben — kurz: es braucht eines der
Zusatzprogramme unter *Einstellungen → Apps*, etwa **Samba share**.

## Einrichten

1. Im Portal anmelden, **Mein Zugang → Meine Integrationen**, einen Schlüssel
   anlegen. Er wird **genau einmal** angezeigt.
2. **Einstellungen → Geräte & Dienste → Integration hinzufügen →
   hesotec electrify**, Adresse `https://elms.hesotec.de` und den Schlüssel
   eintragen.

Der Schlüssel erbt die Rolle seines Zugangs: **lesen kann jeder, schalten nur
eine verwaltende Rolle.** Wer Home Assistant nur zum Anschauen anbindet, nimmt
dafür besser einen einfachen Zugang.

## „Laden erlaubt" ist die Pause, nicht die Autorisierung

Das ist die eine Unterscheidung, an der sich jede Automatisierung entscheidet.
*„Lädt nicht"* kann dreierlei heißen:

| Was Sie sehen | Was los ist | Was hilft |
|---|---|---|
| *Laden erlaubt* **aus** | von Hand pausiert | Schalter einschalten |
| *Laden erlaubt* an, *Lädt* aus, *Wartet auf Freigabe* aus | das **Fahrzeug** pausiert | nichts tun, es geht weiter |
| *Wartet auf Freigabe* **an** | ein Fahrzeug wartet auf die Karte | Taste *Freigabe senden* |

Im dritten Fall ändert der Schalter nichts — und sagt das auch nicht.

## Mehr

| | |
|---|---|
| [`LIES-MICH.md`](LIES-MICH.md) | Entscheidungen, Einstellungen, Schnittstelle, Messwerte |
| [`BEWAEHRTE-PRAXIS.md`](BEWAEHRTE-PRAXIS.md) | vier Automatisierungen und was man besser lässt |
| `pruefung/ladepunkt_pruefen.py` | prüft die Auslegung der Portalantwort, ohne Home Assistant und ohne Portal |

Die Integration spricht `/api/integration/v1` des Portals an — dieselbe
Schnittstelle benutzt das Homebridge-Plugin für Apple Home. Zwischen Home
Assistant und dem Portal steht keine Cloud.

---

© hesotec electrify GmbH
