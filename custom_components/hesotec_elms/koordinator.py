"""Holt den Stand aller Ladepunkte im Takt — einmal für alle Entitäten."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BEREICH
from .ladepunkt import Ladepunkt
from .portal import Portal, Portalfehler

_LOG = logging.getLogger(__name__)


class Ladepunktkoordinator(DataUpdateCoordinator[dict[int, Ladepunkt]]):
    """Ein Abruf je Takt, aus dem sich alle Entitäten bedienen.

    **Nicht eine Abfrage je Entität.** Ein Ladepunkt trägt fünf Entitäten;
    bei vierzehn Ladepunkten wären das siebzig Abrufe je Takt für eine
    Antwort, die alles auf einmal enthält.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        eintrag: ConfigEntry,
        portal: Portal,
        takt: int,
    ) -> None:
        super().__init__(
            hass,
            _LOG,
            name=BEREICH,
            config_entry=eintrag,
            update_interval=timedelta(seconds=takt),
        )
        self._portal = portal

        # Einmal je Sitzung gesagt, nicht in jedem Takt: ein Hinweis, der
        # alle 30 Sekunden wiederkommt, ist nach einer Stunde Rauschen.
        self._gesagt: set[str] = set()

    @property
    def portal(self) -> Portal:
        """Der Zugang, über den auch geschaltet wird.

        Öffentlich, weil der Schalter ihn braucht: er stellt, der
        Koordinator liest. Beide über denselben Zugang, damit nicht zwei
        Sitzungen mit demselben Schlüssel nebeneinander laufen.
        """
        return self._portal

    async def _async_update_data(self) -> dict[int, Ladepunkt]:
        try:
            punkte = await self._portal.ladepunkte()
        except Portalfehler as fehler:
            if fehler.schluessel_gilt_nicht:
                # ConfigEntryAuthFailed und nicht UpdateFailed: Home
                # Assistant fragt dann nach einem neuen Schlüssel, statt den
                # alten im Takt weiter abzulehnen.
                raise ConfigEntryAuthFailed(fehler.text) from fehler
            raise UpdateFailed(str(fehler)) from fehler

        for p in punkte:
            self._matterhinweis(p)

        return {p.id: p for p in punkte}

    def _matterhinweis(self, p: Ladepunkt) -> None:
        """Warnt, wenn ein Ladepunkt doppelt in Home Assistant stehen könnte.

        **Hinter einer SmartBox kann eine eigene Matter-Brücke laufen**, und
        Home Assistant spricht Matter von sich aus. Dann steht derselbe
        Ladepunkt zweimal da — einmal über diese Integration, einmal über
        Matter —, und wer an einem der beiden schaltet, wundert sich über
        den anderen. Dieselbe Falle kennt das Homebridge-Plugin.
        """
        if not p.smartbox_matter_aktiv:
            return

        marke = f"matter:{p.id}"
        if marke in self._gesagt:
            return

        self._gesagt.add(marke)
        _LOG.warning(
            "Ladepunkt %s (%s) hängt hinter einer SmartBox mit eigener "
            "Matter-Brücke. Er kann dadurch zweimal in Home Assistant stehen. "
            "Mit der Einstellung „auch hinter Matter“ wird er hier trotzdem "
            "angelegt.",
            p.name,
            p.seriennummer,
        )
