"""Der Zugriff auf die Integrationsschnittstelle des Portals.

Drei Wege und kein vierter — auflisten, einen lesen, schalten. Mehr gibt
``/api/integration/v1`` nicht her, und das ist dort eine Entscheidung: ein
Schlüssel in einer Konfigurationsdatei soll nicht freischalten, neu starten
oder konfigurieren können.
"""

from __future__ import annotations

import asyncio
import logging

import aiohttp

from .ladepunkt import Ladepunkt

_LOG = logging.getLogger(__name__)

PFAD = "/api/integration/v1"
ZEITLIMIT = aiohttp.ClientTimeout(total=10)


class Portalfehler(Exception):
    """Das Portal hat nicht mit 2xx geantwortet."""

    def __init__(self, status: int, text: str) -> None:
        super().__init__(f"Das Portal antwortete mit {status}: {text}")
        self.status = status
        self.text = text

    @property
    def schluessel_gilt_nicht(self) -> bool:
        """401 — nachfragen hilft nicht.

        Der Schlüssel ist zurückgezogen, der Zugang gesperrt oder er wurde
        falsch abgetippt. Home Assistant soll daraufhin die Einrichtung neu
        anstoßen (Reauth) und nicht alle 30 Sekunden denselben Fehler ins
        Protokoll schreiben.
        """
        return self.status == 401

    @property
    def darf_nicht_schalten(self) -> bool:
        """403 — der Schlüssel darf lesen, aber nicht schalten.

        Schalten verlangt im Portal eine verwaltende Rolle, und der Dienst
        prüft das selbst. ``text`` trägt dann die Begründung im Klartext,
        dieselbe wie in der Maske.
        """
        return self.status == 403


class Portal:
    """Spricht mit einem Portal, mit einem Schlüssel."""

    def __init__(
        self,
        sitzung: aiohttp.ClientSession,
        adresse: str,
        schluessel: str,
    ) -> None:
        # Einen abschließenden Schrägstrich wegnehmen, sonst entsteht beim
        # Zusammensetzen ein doppelter — manche Vermittler stolpern darüber.
        self._wurzel = adresse.rstrip("/") + PFAD
        self._sitzung = sitzung
        self._kopf = {
            "Authorization": f"Bearer {schluessel}",
            "Accept": "application/json",
        }

    # ----------------------------------------------------------------- Lesen

    async def ladepunkte(self) -> list[Ladepunkt]:
        """Alle Ladepunkte des Zugangs.

        **Ein Aufruf für alle**, nicht einer je Ladepunkt: die Liste trägt
        dieselben Messwerte wie die Einzelabfrage, und ein
        Hausautomationssystem fragt im Takt.
        """
        rohdaten = await self._holen("/ladepunkte")

        if not isinstance(rohdaten, list):
            raise Portalfehler(0, "Die Antwort war keine Liste von Ladepunkten.")

        return [Ladepunkt.aus_json(z) for z in rohdaten]

    # --------------------------------------------------------------- Stellen

    async def schalten(self, kennung: int, an: bool) -> None:
        """Gibt frei (``an``) oder pausiert (``aus``).

        **„Vorgang beenden" gibt es hier nicht**, und das ist im Portal so
        gewollt: ein Abbruch ist kein Zustand und gehört nicht auf einen
        Schalter, der sich jederzeit zurückdrehen lässt.
        """
        await self._senden(f"/ladepunkte/{kennung}/schalten", {"an": an})

    # ---------------------------------------------------------------- intern

    async def _holen(self, weg: str) -> object:
        try:
            async with self._sitzung.get(
                self._wurzel + weg, headers=self._kopf, timeout=ZEITLIMIT
            ) as antwort:
                return await self._auswerten(antwort)
        except asyncio.TimeoutError as fehler:
            raise Portalfehler(0, "Das Portal hat nicht rechtzeitig geantwortet.") from fehler
        except aiohttp.ClientError as fehler:
            raise Portalfehler(0, f"Das Portal war nicht erreichbar: {fehler}") from fehler

    async def _senden(self, weg: str, rumpf: dict) -> object:
        try:
            async with self._sitzung.post(
                self._wurzel + weg, headers=self._kopf, json=rumpf, timeout=ZEITLIMIT
            ) as antwort:
                return await self._auswerten(antwort)
        except asyncio.TimeoutError as fehler:
            raise Portalfehler(0, "Das Portal hat nicht rechtzeitig geantwortet.") from fehler
        except aiohttp.ClientError as fehler:
            raise Portalfehler(0, f"Das Portal war nicht erreichbar: {fehler}") from fehler

    @staticmethod
    async def _auswerten(antwort: aiohttp.ClientResponse) -> object:
        if antwort.status >= 400:
            raise Portalfehler(antwort.status, await _begruendung(antwort))

        # 202 auf das Schalten, und der Rumpf ist leer. `json()` darauf
        # loszulassen wäre ein Fehler aus Gewohnheit.
        if antwort.status == 204 or antwort.content_length == 0:
            return None

        try:
            return await antwort.json()
        except (aiohttp.ContentTypeError, ValueError):
            return None


async def _begruendung(antwort: aiohttp.ClientResponse) -> str:
    """Der Klartext hinter einem Fehler.

    Das Portal antwortet auf eine abgewiesene Schaltung mit einem
    ProblemDetails-Rumpf, und dessen ``title`` ist der Satz, den auch die
    Maske zeigt — etwa „Für diese Änderung fehlt die Berechtigung." Ihn
    durchzureichen ist mehr wert als ein nacktes „403".
    """
    try:
        rumpf = await antwort.json()
    except (aiohttp.ContentTypeError, ValueError):
        rumpf = None

    if isinstance(rumpf, dict):
        for feld in ("title", "detail"):
            if isinstance(rumpf.get(feld), str) and rumpf[feld]:
                return rumpf[feld]

    try:
        text = (await antwort.text()).strip()
    except Exception:  # noqa: BLE001 — hier ist jeder Fehler gleich uninteressant
        return antwort.reason or ""

    return text[:200] or antwort.reason or ""
