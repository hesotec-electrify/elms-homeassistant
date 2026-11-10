# Bewährte Praxis — hesotec electrify in Home Assistant

Für Anwender, die ihre Ladepunkte schon im Portal betreiben und sie jetzt im
eigenen Haus automatisieren wollen. Die Einrichtung steht in
[`LIES-MICH.md`](LIES-MICH.md); hier geht es darum, was sich im Betrieb
bewährt — und was man besser lässt.

## Zuerst: wofür die Integration da ist

| sie kann | sie kann nicht |
|---|---|
| zusehen (lädt, Leistung, Strom, Energie der Sitzung) | **den Ladestrom regeln** |
| **pausieren und fortsetzen** (Schalter *Laden erlaubt*) | Ladepunkte anlegen oder konfigurieren |
| eine **hinterlegte Karte freigeben** (Taste *Freigabe senden*) | Karten anlegen oder Freigaben vergeben |

> **Der Ladestrom gehört dem Lastmanagement des Portals.** Ladegruppen,
> Anschlussleistung, Mindestströme — das rechnet eLMS, und zwar über alle
> Ladepunkte einer Gruppe hinweg. Home Assistant sieht immer nur einen
> Ladepunkt und kennt die Nachbarn nicht. **Wer von hier aus gegenregelt,
> kämpft gegen eine Rechnung, die mehr weiß als er.**
>
> Was von hier aus richtig ist: **ganz anhalten und wieder freigeben**. Das
> ist eine Aussage, die das Lastmanagement versteht und einplant.

## Zwei Zugänge statt einem

Der Schlüssel **erbt die Rolle des Zugangs**, zu dem er gehört. Lesen darf
jeder, schalten nur eine verwaltende Rolle.

- **Dashboard, Diagramme, Benachrichtigungen** → Schlüssel eines einfachen
  Zugangs. Dann kann auch ein verlorenes Home Assistant nichts umlegen.
- **Automatisierungen, die schalten** → dafür und nur dafür ein Schlüssel mit
  verwaltender Rolle.

Der Schlüssel wird im Portal **genau einmal angezeigt**. Ins Passwortfach
damit — sonst kostet schon ein Adresswechsel einen neuen Schlüssel.

## Die drei Fälle von „lädt nicht"

Das ist die eine Sache, an der sich entscheidet, ob eine Automatisierung
taugt. *Laden erlaubt* ist **die Pause, nicht die Autorisierung.**

| was Sie sehen | was los ist | was hilft |
|---|---|---|
| *Laden erlaubt* **aus** | von Hand (oder von einer Automatisierung) pausiert | Schalter einschalten |
| *Laden erlaubt* **an**, *Lädt* aus, *Wartet auf Freigabe* **aus** | das **Fahrzeug** pausiert — voll, Zeitprogramm, Klimatisierung | nichts tun, es geht von selbst weiter |
| *Wartet auf Freigabe* **an** | ein Fahrzeug steht an und wartet auf die Karte | Taste *Freigabe senden* |

**Im dritten Fall ändert der Schalter nichts** — und sagt das auch nicht. Wer
seine Automatisierung auf „Schalter an, also lädt es gleich" baut, wartet
vergebens.

## Takt: 30 Sekunden, und das ist richtig so

Die Messdaten entstehen im Portal höchstens alle 20 Sekunden. Ein engerer
Takt fragt dieselbe Zahl zweimal ab; ein weiterer lässt den Schalter träge
wirken.

Daraus folgt für jede Automatisierung: **sie sieht die Welt mit bis zu einer
halben Minute Verzug.** Wer darauf Sekundenlogik baut, baut auf Sand.

## Vier Automatisierungen, die sich bewähren

> Die Entitätskennungen unten sind Platzhalter. Die richtigen stehen auf der
> Geräteseite des Ladepunkts — **Einstellungen → Geräte & Dienste →
> hesotec electrify → der Ladepunkt**, dort je Entität das Zahnrad.

### 1. Es wartet jemand auf die Freigabe

Der häufigste Fall im Alltag, und der, bei dem jemand vor der Säule steht.

```yaml
alias: Ladepunkt wartet auf Freigabe
triggers:
  - trigger: state
    entity_id: binary_sensor.LADEPUNKT_wartet_auf_freigabe
    to: "on"
    # Dreißig Sekunden Geduld: beim Einstecken blinkt der Zustand kurz
    # durch, und eine Meldung je Steckvorgang will niemand.
    for: "00:00:30"
actions:
  - action: notify.mobile_app_DEIN_TELEFON
    data:
      title: Ladepunkt wartet
      message: >-
        An {{ trigger.to_state.name }} steht ein Fahrzeug und wartet auf die
        Freigabe.
      data:
        actions:
          - action: FREIGABE_SENDEN
            title: Freigabe senden
mode: single
```

Und die Gegenseite — die Taste aus der Meldung heraus:

```yaml
alias: Freigabe aus der Meldung senden
triggers:
  - trigger: event
    event_type: mobile_app_notification_action
    event_data:
      action: FREIGABE_SENDEN
actions:
  - action: button.press
    target:
      entity_id: button.LADEPUNKT_freigabe_senden
mode: single
```

**Die Taste gibt es nur dort, wo eine Karte zugeordnet ist** — in den
Einstellungen der Integration unter *Karten für die Freigabe*. Das Portal
kennt keinen kartenlosen Weg.

### 2. Laden nur bei PV-Überschuss — anhalten statt regeln

```yaml
alias: Laden nur bei PV-Überschuss
triggers:
  - trigger: numeric_state
    entity_id: sensor.PV_UEBERSCHUSS
    below: 1000
    for: "00:05:00"
    id: zu_wenig
  - trigger: numeric_state
    entity_id: sensor.PV_UEBERSCHUSS
    above: 2500
    for: "00:05:00"
    id: genug
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: zu_wenig
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.LADEPUNKT_laden_erlaubt
      - conditions:
          - condition: trigger
            id: genug
        sequence:
          - action: switch.turn_on
            target:
              entity_id: switch.LADEPUNKT_laden_erlaubt
mode: single
```

**Zwei verschiedene Schwellen und fünf Minuten Geduld** — das ist der ganze
Trick. Mit einer Schwelle klappert der Schalter bei jeder Wolke, und jedes
Anhalten kostet das Fahrzeug einen neuen Anlauf. Die Zahlen sind ein
Ausgangspunkt, kein Gesetz: 1.000 W unten, 2.500 W oben passen zu einem
einphasigen Ladepunkt mit 6 A Mindeststrom.

### 3. Nur im Nachtfenster laden

```yaml
alias: Laden nur zwischen 22 und 6 Uhr
triggers:
  - trigger: time
    at: "22:00:00"
    id: frei
  - trigger: time
    at: "06:00:00"
    id: pause
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: frei
        sequence:
          - action: switch.turn_on
            target:
              entity_id: switch.LADEPUNKT_laden_erlaubt
      - conditions:
          - condition: trigger
            id: pause
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.LADEPUNKT_laden_erlaubt
mode: single
```

> Ausgeschrieben statt mit einem Ausdruck wie
> `switch.turn_{{ 'on' if … }}` — das geht zwar, aber ein Tippfehler darin
> fällt erst nachts um zehn auf, wenn nichts passiert. Zwei Zeilen mehr sind
> hier billiger.

**Das ersetzt kein Ladeprofil im Portal.** Dort hinterlegte Zeitfenster
gelten für alle, die an dem Gerät laden, und auch dann, wenn Home Assistant
gerade aus ist. Der Weg hier ist der kurze für den eigenen Haushalt.

### 4. Der Ladepunkt meldet sich nicht mehr

```yaml
alias: Ladepunkt still
triggers:
  - trigger: template
    value_template: >-
      {{ has_value('sensor.LADEPUNKT_zuletzt_gemeldet')
         and (now() - states('sensor.LADEPUNKT_zuletzt_gemeldet') | as_datetime)
             > timedelta(minutes=30) }}
actions:
  - action: notify.mobile_app_DEIN_TELEFON
    data:
      message: Der Ladepunkt hat sich seit einer halben Stunde nicht gemeldet.
mode: single
```

**Der Sensor *Zuletzt gemeldet* ist von Haus aus abgeschaltet** und muss
erst eingeschaltet werden (Geräteseite → Entität → Zahnrad → *Aktiviert*).
Er ist das einzige Mittel, um ein stilles Gerät von einem ruhigen zu
unterscheiden: ein Ladepunkt, an dem niemand lädt, sieht genauso aus wie
einer, der nicht mehr antwortet.

## Energie-Dashboard

*Energie der Sitzung* zählt die kWh des **laufenden** Ladevorgangs und
springt beim nächsten auf 0 zurück. Genau dafür trägt der Sensor
`total_increasing` — Home Assistant hält den Rücksprung also nicht für einen
Fehler, sondern für einen neuen Zyklus. Damit lässt er sich im
Energie-Dashboard als **einzelnes Gerät** eintragen.

> **Für die Abrechnung gilt er nicht.** Die Zahl kommt aus dem Portal und ist
> so gut wie die Meldung des Geräts. Was abgerechnet wird, steht im Portal —
> und bei eichrechtlich relevanten Vorgängen zählt allein der geeichte
> Zähler, nicht das Hausdashboard.

## Was man besser lässt

- **Gegen das Lastmanagement regeln.** Siehe oben: Home Assistant kennt die
  Nachbarn in der Ladegruppe nicht.
- **Den Takt auf zehn Sekunden stellen.** Die Daten entstehen alle 20
  Sekunden; es kommt nichts Neues dabei heraus, nur mehr Last auf dem Portal.
- **Den Schalter für die Autorisierung halten.** Er ist die Pause. Wer
  *Wartet auf Freigabe* ignoriert, baut eine Automatisierung, die manchmal
  grundlos nichts tut.
- **Die Integration auf ein anderes Portal umbiegen.** Die Entitäten heißen
  nach den Ladepunkten des alten und zeigten dann die Werte des neuen.
- **Den Schlüssel in eine Automatisierung schreiben.** Er steht im Eintrag
  der Integration und gehört sonst nirgendwohin.

## Wenn etwas nicht geht

| Bild | meist |
|---|---|
| Alle Entitäten „nicht verfügbar" | Adresse oder Schlüssel. Seit dem 04.11.2026 ist `https://elms.hesotec.de` die ganze Adresse — ohne `:8443`. Ändern unter *Neu konfigurieren*, siehe `LIES-MICH.md`. |
| Home Assistant fragt von selbst nach dem Schlüssel | Das Portal hat ihn abgelehnt — widerrufen, oder der Zugang ist gesperrt. Im Portal einen neuen anlegen. |
| Schalter geht, aber nichts passiert | *Wartet auf Freigabe* ansehen. Oder der Ladepunkt hat sich länger nicht gemeldet. |
| Taste *Freigabe senden* fehlt | Dem Ladepunkt ist keine Karte zugeordnet — Einstellungen der Integration, *Karten für die Freigabe*. |
| Ein Ladepunkt steht doppelt da | Er hängt hinter einer SmartBox mit eigener Matter-Brücke. In den Einstellungen gibt es dafür den Schalter *Auch Ladepunkte hinter einer SmartBox …*. |
