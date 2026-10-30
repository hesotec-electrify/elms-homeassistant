# hesotec electrify für Home Assistant

Ladepunkte aus dem hesotec-electrify-Portal in **Home Assistant** —
freigeben, pausieren, Leistung und Energie sehen.

Je Ladepunkt entsteht ein **Gerät** mit:

| Entität | heißt hier |
|---|---|
| Schalter *Freigabe* | an = freigegeben, aus = **von Hand pausiert** |
| *Lädt* | es fließt gerade Strom |
| *Leistung*, *Strom* | W und A, nur während eines Ladevorgangs |
| *Energie der Sitzung* | kWh des laufenden Ladevorgangs |
| *Zuletzt gemeldet* | wann sich das Gerät zuletzt gemeldet hat (standardmäßig aus) |

> **„An" heißt freigegeben, nicht „lädt".** Eine Säule kann freigegeben
> sein, ohne dass jemand ansteckt. Was wirklich fließt, sagt *Lädt*.

## Einrichten

1. Im Portal anmelden, **Mein Zugang → Meine Integrationen**, einen
   Schlüssel anlegen. Er wird **genau einmal** angezeigt.
2. Den Ordner `custom_components/hesotec_elms` nach
   `<config>/custom_components/` kopieren — oder das Repository in HACS als
   eigene Quelle hinzufügen.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen →
   hesotec electrify.** Adresse (`https://elms.hesotec.de:8443`) und
   Schlüssel eintragen.

Die Einrichtung **probiert den Schlüssel sofort aus**. Nimmt das Portal ihn
nicht an, sagt die Maske es dort, statt hinterher eine kaputte Integration
anzulegen.

### Was der Schlüssel darf

Er erbt die Rolle des Zugangs, zu dem er gehört. **Lesen kann jeder,
schalten nur eine verwaltende Rolle.** Wer Home Assistant nur zum Anschauen
anbindet, nimmt dafür besser einen einfachen Zugang — dann kann ein Token
in einer Konfigurationsdatei im schlimmsten Fall nichts anrichten.

Versucht ein Schlüssel ohne diese Rolle zu schalten, erscheint in Home
Assistant genau der Satz, den auch das Portal zeigt.

## Einstellungen

| | Vorgabe | |
|---|---|---|
| Abstand zwischen zwei Abrufen | **30 s** | |
| Auch hinter Matter | aus | siehe unten |

**Dreißig Sekunden sind kein Kompromiss.** Die Messdaten kommen höchstens
alle 20 Sekunden — der Dienst drängt schnelleren Geräten dieses Intervall
auf. Ein engerer Takt fragt dieselbe Zahl zweimal ab.

**Push gibt es hier nicht, und es fehlt auch nicht.** Für Google Home musste
das Portal von sich aus melden, weil Google sonst gar nicht nachfragt. Home
Assistant fragt selbst, und zwar genau im Takt der Daten.

### „Auch hinter Matter"

Hinter einer SmartBox kann eine **eigene Matter-Brücke** laufen, und Home
Assistant spricht Matter von sich aus. Dann stünde derselbe Ladepunkt
zweimal da — einmal über diese Integration, einmal über Matter —, und wer
an einem schaltet, wundert sich über den anderen.

Solche Ladepunkte werden deshalb **weggelassen** und einmal im Protokoll
benannt. Wer sie trotzdem will, schaltet die Einstellung ein.

## Zwei Dinge, die absichtlich so sind

**Ein Ladepunkt ohne Netz ist `unavailable`, nicht „aus".** Er ist nicht
pausiert — wir wissen gerade nur nichts über ihn. Ihn als „aus" zu zeigen
wäre dieselbe Verwechslung, die im Portal selbst einmal auf dem Dashboard
stand: eine Pause sah aus wie eine Störung.

**Leistung und Strom stehen auf 0, wenn nichts lädt.** Das Portal liefert
dort `null`, und das heißt „es lädt nicht" — nicht „unbekannt". Die Spalten
bleiben nach einem Ladevorgang stehen; würde man sie weiterreichen,
behaupteten sie eine Messung, die Stunden alt ist. Für eine Messgröße in
Home Assistant ist 0 W die richtige Anzeige; ein `unknown` risse eine Lücke
in die Statistik.

## Die Schnittstelle dahinter

`/api/integration/v1` im Portal — **drei Wege und kein vierter**: auflisten,
einen lesen, schalten. Dieselbe Schnittstelle benutzt das
Homebridge-Plugin für Apple Home (Repository `elms-Plugin`).

**Ihre Antwortform ist veröffentlicht.** Wer dort ein Feld umbenennt oder
seine Bedeutung ändert, ändert sie für Programme, die auf Rechnern von
Kunden laufen und beim Ausrollen des Portals nicht mitkommen. Erweitern ja,
ändern nein.

## Prüfen

```bash
python pruefung/ladepunkt_pruefen.py
```

Prüft die Auslegung der Portalantwort — **ohne Home Assistant und ohne
Portal**: was `null` bedeutet, wie aus Wattstunden Kilowattstunden werden,
was bei fehlenden oder unsinnigen Feldern passiert. Dafür braucht es keine
Testbibliothek; die Probe läuft auf jedem Rechner mit Python.

## Was noch nicht geprüft ist

**Die Integration ist noch nicht in einer laufenden Home-Assistant-Instanz
geladen worden.** Geprüft sind: Syntax aller Dateien, Gültigkeit aller
JSON-Dateien, und die Auslegung der Portalantwort (16 Prüfungen). Nicht
geprüft ist, ob Home Assistant die Entitäten so anlegt wie gedacht und ob
jede benutzte Schnittstelle in der installierten Fassung noch so heißt.

Dafür spricht `hacs.json` eine Mindestfassung aus (**2024.12**); sie ist
hergeleitet aus den benutzten Bausteinen (`entry.runtime_data`,
`_get_reauth_entry`, `config_entry` am Koordinator) und sollte an einer
echten Instanz nachgezogen werden.
