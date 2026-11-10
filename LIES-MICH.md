# hesotec electrify für Home Assistant

Ladepunkte aus dem hesotec-electrify-Portal in **Home Assistant** —
freigeben, pausieren, Leistung und Energie sehen.

Je Ladepunkt entsteht ein **Gerät** mit:

| Entität | heißt hier |
|---|---|
| Schalter *Laden erlaubt* | aus = **von Hand pausiert** |
| *Lädt* | es fließt gerade Strom |
| *Wartet auf Freigabe* | ein Fahrzeug steht an und wartet auf die Autorisierung |
| Taste *Freigabe senden* | schickt die hinterlegte Karte (nur wo eine zugeordnet ist) |
| *Leistung*, *Strom* | W und A, nur während eines Ladevorgangs |
| *Energie der Sitzung* | kWh des laufenden Ladevorgangs |
| *Zuletzt gemeldet* | wann sich das Gerät zuletzt gemeldet hat (standardmäßig aus) |

> **„Laden erlaubt" ist die Pause, nicht die Autorisierung.** Das sind zwei
> verschiedene Dinge, und sie brauchen zwei verschiedene Handgriffe:
> *„lädt nicht"* kann heißen **von Hand pausiert** (Schalter umlegen),
> **vom Fahrzeug pausiert** (nichts tun, es geht weiter) oder **wartet auf
> Autorisierung** (Freigabe senden). Beim letzten ändert der Schalter
> nichts — und sagt das auch nicht.

## Einrichten

1. Im Portal anmelden, **Mein Zugang → Meine Integrationen**, einen
   Schlüssel anlegen. Er wird **genau einmal** angezeigt.
2. Den Ordner `custom_components/hesotec_elms` nach
   `<config>/custom_components/` kopieren — oder das Repository in HACS als
   eigene Quelle hinzufügen.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen →
   hesotec electrify.** Adresse (`https://elms.hesotec.de`) und
   Schlüssel eintragen.

Die Einrichtung **probiert den Schlüssel sofort aus**. Nimmt das Portal ihn
nicht an, sagt die Maske es dort, statt hinterher eine kaputte Integration
anzulegen.

> **Hier stand bis zum 10.11.2026 `:8443`.** Das Portal lief eine Zeit lang
> auf einem zweiten Port neben dem Altportal; seit dem Umzug am 04.11.2026
> ist dieser Port zu, und `https://elms.hesotec.de` ist die ganze Adresse.
> **Eine bestehende Einrichtung zieht nicht von selbst um** — die Adresse
> steht im Eintrag. Ändern lässt sie sich unter *Neu konfigurieren*, siehe
> unten; Entitäten, Verlauf und Kartenzuordnung bleiben dabei erhalten.

### Adresse oder Schlüssel später ändern

**Einstellungen → Geräte & Dienste → hesotec electrify → ⋮ → Neu
konfigurieren.** Entitäten, Verlauf und die Kartenzuordnung bleiben.

- Das **Schlüsselfeld darf leer bleiben** — dann gilt der bisherige. Das
  Portal zeigt einen Schlüssel nur einmal an; wer ihn nicht aufgehoben hat,
  müsste sonst einen neuen anlegen, nur um die Adresse zu ändern.
- Die neue Adresse muss auf **dasselbe Portal** zeigen. Prüfen kann das
  niemand — eine Adresse sagt es nicht. Wer auf ein fremdes Portal biegt,
  bekommt Entitäten, die nach den alten Ladepunkten heißen und die Werte
  der neuen zeigen.
- Lehnt das Portal den Schlüssel ab, meldet sich die Integration von
  selbst mit der **erneuten Anmeldung** — das ist ein anderer Weg und
  fragt nur nach dem Schlüssel.

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

## Gemessen am 30.10.2026

Geladen in **Home Assistant OS 2026.10.4** auf einem Raspberry Pi, gegen
das Livesystem mit vierzehn Ladepunkten.

| | |
|---|---|
| Geräte | **12** — vierzehn Ladepunkte minus zwei hinter Matter |
| Entitäten | **72** = 12 × 6, davon 12 abgeschaltet (*Zuletzt gemeldet*) |
| Fehler beim Laden | keine |

Drei Dinge waren dabei an echten Daten zu sehen, und jedes ist eine
Entscheidung aus diesem Repository:

- **Wo nichts lädt, steht 0,0 W** — kein `unknown`, keine Lücke in der
  Statistik. Die ladenden Ladepunkte standen zur selben Zeit auf 11.160 W,
  10.900 W, 7.310 W und 3.130 W.
- **Zwei nicht erreichbare SmartBoxen standen auf `unavailable`**, nicht
  auf „aus".
- **Ein Ladepunkt stand auf *Freigabe an* und *Lädt aus* zugleich.** Kein
  Widerspruch, sondern die ganze Unterscheidung: er ist freigegeben, und
  das Fahrzeug pausiert. Das Portal nannte denselben Vorgang zur selben
  Zeit „Pause (Fahrzeug)".

Die Warnung zu den beiden Ladepunkten hinter Matter stand mit Namen und
Seriennummer im Protokoll — einmal, nicht in jedem Takt.

**Die Mindestfassung in `hacs.json` (2024.12) ist weiterhin hergeleitet und
nicht gemessen**; gelaufen ist es auf 2026.10. Wer eine ältere Instanz
bedienen muss, prüft sie dort nach.
