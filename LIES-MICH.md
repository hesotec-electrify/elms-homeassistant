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

> **Für den Betrieb gibt es ein eigenes Heft:**
> [`BEWAEHRTE-PRAXIS.md`](BEWAEHRTE-PRAXIS.md) — die drei Fälle von
> „lädt nicht", vier Automatisierungen zum Abschreiben, und was man
> besser lässt.

## Einrichten

1. Im Portal anmelden, **Mein Zugang → Meine Integrationen**, einen
   Schlüssel anlegen. Er wird **genau einmal** angezeigt.
2. **Einbauen.** Ab Home Assistant 2026.11 unter *Einstellungen →
   Marketplace → Von Link hinzufügen*, davor in HACS unter
   *⋮ → Benutzerdefinierte Repositories*, jeweils mit
   `https://github.com/hesotec-electrify/elms-homeassistant` (Art
   *Integration*). Sonst den Ordner `custom_components/hesotec_elms` von Hand
   nach `<config>/custom_components/` kopieren.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen →
   hesotec electrify.** Adresse (`https://elms.hesotec.de`) und
   Schlüssel eintragen.

Die Einrichtung **probiert den Schlüssel sofort aus**. Nimmt das Portal ihn
nicht an, sagt die Maske es dort, statt hinterher eine kaputte Integration
anzulegen.

### Wie die Dateien auf das Gerät kommen

**Home Assistant OS hat keinen eingebauten Dateizugriff.** Man braucht eines
der Zusatzprogramme — sie heißen in neueren Fassungen **„Apps“** und nicht
mehr „Add-ons“: *Einstellungen → Apps → Store*.

| | |
|---|---|
| **Samba share** | der einfachste Weg von einem Windows-Rechner: danach liegt `\\homeassistant\config` im Explorer |
| **Studio Code Server** oder **File editor** | im Browser bearbeiten und hochladen |
| **Advanced SSH & Web Terminal** | für `scp` |

Beim Austausch den alten Ordner **löschen** statt darüberzukopieren — sonst
bleiben Dateien liegen, die es in der neuen Fassung nicht mehr gibt.

**Die Datei dafür liefert das Portal aus** (<https://elms.hesotec.de/anleitungen/home-assistant.html#dateien>), nicht dieses
Repository und auch nicht das Release auf GitHub. Gebaut wird sie drüben mit
`entwicklung/ha-paket.py` im Repository `elms-Web`: es liest die Fassung aus
`manifest.json`, packt **nur** `custom_components/hesotec_elms` und schreibt
Fassung, Größe und SHA-256 selbst in die Anleitungsseite. **Also nach jeder
neuen Fassung dort laufen lassen** — sonst steht im Portal eine alte Datei
mit einer Nummer, die der Kunde für die neue hält.

> **Von Hand ist seit dem 10.11.2026 der letzte Ausweg** — der Weg, den ein
> Kunde nehmen sollte, geht über den Katalog: Aktualisieren kostet danach
> zwei Klicks statt eines Dateitauschs über Samba. Geholt wird von der
> Spiegelung `hesotec-electrify/elms-homeassistant` auf GitHub; gearbeitet
> wird weiter hier auf Forgejo. Wie eine neue Fassung dorthin kommt, steht
> unter *Ausliefern über den Katalog*.
>
> **Hier stand bis dahin, HACS sei kein Weg** — und davor stand sogar, es
> ginge einfach so. Beides war falsch, in entgegengesetzte Richtungen.

> **Und der Katalog hat am 04.11.2026 den Namen gewechselt.** Mit Home
> Assistant **2026.11** ist HACS in Home Assistant eingezogen und heißt dort
> **Marketplace**: *Einstellungen → Marketplace*, nicht mehr in der
> Seitenleiste. Derselbe Katalog, dieselben Repositories, dieselbe
> `hacs.json` — für dieses Repository ändert sich **nichts**. Für die
> Anleitung schon: das eigenständige HACS lässt sich ab 2026.11 **nicht mehr
> installieren**, Home Assistant blockiert es. Ein Kunde ohne HACS wird also
> nicht mehr dorthin geschickt, sondern zum Aktualisieren.
>
> **Ein eigenes Repository verlangt im Marketplace eine GitHub-Anmeldung**
> (Gerätecode, liest nur Öffentliches). Für den Katalog selbst verlangt er
> keine — die Hürde steht also genau auf unserem Weg und nicht auf dem der
> mitgelieferten Integrationen.

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

## Ausliefern über den Katalog

**Nicht von hier, sondern von einer Spiegelung auf GitHub.** Der Katalog —
HACS bis 2026.10, der eingebaute Marketplace ab 2026.11 — holt ausschließlich
über die GitHub-Schnittstelle; dieses Repository liegt auf dem hauseigenen
Forgejo. Die Spiegelung ist der Auslieferungsweg, nicht der Arbeitsort —
gearbeitet wird weiter hier. **Beide lesen dieselbe `hacs.json`**, es gibt
also nur einen Stand zu pflegen.

**Was dafür im Repository stehen muss**, und was davon schon steht:

| | |
|---|---|
| `custom_components/hesotec_elms/` mit allen Dateien | ✓ |
| `manifest.json` mit `domain`, `name`, `version`, `codeowners`, `documentation`, `issue_tracker` | ✓ |
| `hacs.json` mit `name` | ✓ |
| `README.md` — der Katalog zeigt sie in der Übersicht (`render_readme`) | ✓ |
| `brand/icon.png` | ✓, 256 px, dazu `icon@2x.png` mit 512 px |
| ein **Release** auf GitHub | ✓, `v1.1.0` vom 10.11.2026 |

**Die beiden Adressen im Manifest zeigen auf die Spiegelung** und nicht mehr
auf Forgejo — ein `documentation`, das von außen nicht erreichbar ist, ist für
einen Kunden dasselbe wie keines. Festgelegt am 10.11.2026:

```
https://github.com/hesotec-electrify/elms-homeassistant
```

**Die Spiegelung steht seit dem 10.11.2026** unter genau diesem Namen,
öffentlich, mit den Schlagwörtern `home-assistant`, `hacs`, `ev-charging`
und `homeassistant-integration`. Ein anderer Name wäre kein kleiner
Unterschied gewesen: die beiden Adressen im Manifest zeigten dann ins Leere,
und sichtbar würde das erst, wenn ein Kunde in Home Assistant auf
„Dokumentation" klickt.

### Die Symbole kommen aus dem Portal

`brand/icon.png` und `brand/icon@2x.png` sind **erzeugt**, nicht gemalt:
derselbe Erzeuger, der das Webseiten-Symbol des Portals schreibt
(`entwicklung/symbol-erzeugen.py` im Repository `elms-Web`), mit 256 und
512 px. Dasselbe Zeichen, dieselben Farben, derselbe Eckradius — von Hand
nachgezeichnet würden sie beim ersten Nachziehen auseinanderlaufen.

### Eine neue Fassung herausgeben

1. `version` in `custom_components/hesotec_elms/manifest.json` hochzählen.
   **Das ist die Zahl, an der der Katalog ein Update erkennt** — ohne sie
   merkt niemand, dass es etwas Neues gibt.
2. Hierher committen, dann nach GitHub spiegeln (**über SSH**: ESET
   blockiert von den Arbeitsplätzen aus HTTPS zu fremden Git-Diensten).
3. Auf GitHub ein **Release** anlegen, nicht nur ein Tag — ein Tag allein
   genügt nicht.

**Ohne Release geht es auch**, dann wird der Standardzweig ausgeliefert. Das
ist aber kein Zustand für Kunden: sie bekämen jeden Zwischenstand, auch einen
halbfertigen.

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
