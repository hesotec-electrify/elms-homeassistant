"""Einrichten über die Oberfläche — Adresse und Schlüssel, einmal geprüft."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    BEREICH,
    FELD_ADRESSE,
    FELD_AUCH_HINTER_MATTER,
    FELD_SCHLUESSEL,
    FELD_TAKT,
    GROESSTER_TAKT,
    KLEINSTER_TAKT,
    VORGABE_ADRESSE,
    VORGABE_TAKT,
)
from .portal import Portal, Portalfehler

MASKE = vol.Schema(
    {
        vol.Required(FELD_ADRESSE, default=VORGABE_ADRESSE): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
        # PASSWORT UND NICHT TEXT: der Schlüssel ist ein Geheimnis, und die
        # Einrichtung findet oft im Beisein von jemandem statt, der auf den
        # Bildschirm sieht.
        vol.Required(FELD_SCHLUESSEL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
    }
)


class Einrichtung(ConfigFlow, domain=BEREICH):
    """Fragt nach Adresse und Schlüssel und probiert beides aus."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Der erste und einzige Schritt."""
        fehler: dict[str, str] = {}

        if user_input is not None:
            adresse = user_input[FELD_ADRESSE].rstrip("/")
            schluessel = user_input[FELD_SCHLUESSEL]

            schlimm = await self._probieren(adresse, schluessel)

            if schlimm is None:
                # EINE EINRICHTUNG JE ADRESSE. Zwei Einträge auf dasselbe
                # Portal legten jeden Ladepunkt doppelt an — mit derselben
                # Seriennummer, also mit kollidierenden Kennungen.
                await self.async_set_unique_id(adresse)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="hesotec electrify",
                    data={FELD_ADRESSE: adresse, FELD_SCHLUESSEL: schluessel},
                )

            fehler["base"] = schlimm

        return self.async_show_form(
            step_id="user", data_schema=MASKE, errors=fehler
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Der Schlüssel gilt nicht mehr — nach einem neuen fragen."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Nur der Schlüssel; die Adresse bleibt, wie sie war."""
        eintrag = self._get_reauth_entry()
        fehler: dict[str, str] = {}

        if user_input is not None:
            adresse = eintrag.data[FELD_ADRESSE]
            schlimm = await self._probieren(adresse, user_input[FELD_SCHLUESSEL])

            if schlimm is None:
                return self.async_update_reload_and_abort(
                    eintrag,
                    data_updates={FELD_SCHLUESSEL: user_input[FELD_SCHLUESSEL]},
                )

            fehler["base"] = schlimm

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(FELD_SCHLUESSEL): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=fehler,
        )

    async def _probieren(self, adresse: str, schluessel: str) -> str | None:
        """Ruft die Liste einmal ab. ``None`` heißt: alles in Ordnung.

        **Erst probieren, dann speichern.** Ein Eintrag, der mit einem
        falschen Schlüssel entsteht, meldet sich hinterher als kaputte
        Integration — und niemand weiß dann noch, ob die Adresse, der
        Schlüssel oder das Netz schuld war.
        """
        portal = Portal(async_get_clientsession(self.hass), adresse, schluessel)

        try:
            await portal.ladepunkte()
        except Portalfehler as fehler:
            if fehler.schluessel_gilt_nicht:
                return "schluessel"
            if fehler.status == 0:
                return "nicht_erreichbar"
            return "unbekannt"

        return None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return Einstellungen()


class Einstellungen(OptionsFlow):
    """Takt und der Matter-Sonderfall."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={
                    FELD_TAKT: int(user_input[FELD_TAKT]),
                    FELD_AUCH_HINTER_MATTER: user_input[FELD_AUCH_HINTER_MATTER],
                }
            )

        jetzt = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        FELD_TAKT, default=jetzt.get(FELD_TAKT, VORGABE_TAKT)
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=KLEINSTER_TAKT,
                            max=GROESSTER_TAKT,
                            step=5,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        FELD_AUCH_HINTER_MATTER,
                        default=jetzt.get(FELD_AUCH_HINTER_MATTER, False),
                    ): BooleanSelector(),
                }
            ),
        )
