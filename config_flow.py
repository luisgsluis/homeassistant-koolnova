"""Config flow for Koolnova integration."""
import asyncio
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.components.climate import HVACMode

from koolnova_api.client import KoolnovaAPIRestClient
from koolnova_api.exceptions import KoolnovaError

from .const import (
    DOMAIN,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
    DEFAULT_PROJECT_HVAC_MODES,
    DEFAULT_ZONE_HVAC_MODES,
    DEFAULT_MIN_TEMP,
    MIN_CONFIGURABLE_TEMP,
    DEFAULT_MAX_TEMP,
    MAX_CONFIGURABLE_TEMP,
    DEFAULT_TEMP_PRECISION,
    AVAILABLE_HVAC_MODES,
    AVAILABLE_TEMP_PRECISIONS,
    CONF_UPDATE_INTERVAL,
    CONF_PROJECT_HVAC_MODES,
    CONF_ZONE_HVAC_MODES,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_TEMP_PRECISION,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Koolnova."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await self._validate_input(user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()
            
            # Configuracion inicial con valores por defecto
            config_data = {
                CONF_EMAIL: user_input[CONF_EMAIL],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                CONF_PROJECT_HVAC_MODES: [mode.value for mode in DEFAULT_PROJECT_HVAC_MODES],
                CONF_ZONE_HVAC_MODES: [mode.value for mode in DEFAULT_ZONE_HVAC_MODES],
                CONF_MIN_TEMP: DEFAULT_MIN_TEMP,
                CONF_MAX_TEMP: DEFAULT_MAX_TEMP,
                CONF_TEMP_PRECISION: DEFAULT_TEMP_PRECISION,
            }

            return self.async_create_entry(title=info["title"], data=config_data)

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors
        )

    async def _validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the user input allows us to connect."""
        try:
            client = KoolnovaAPIRestClient(data[CONF_EMAIL], data[CONF_PASSWORD])
            
            # Test connection
            await self.hass.async_add_executor_job(client.get_project)
            
        except KoolnovaError as err:
            if "401" in str(err) or "authentication" in str(err).lower():
                raise InvalidAuth
            raise CannotConnect
        except Exception as err:
            _LOGGER.error("Unexpected error validating credentials: %s", err)
            raise CannotConnect

        return {"title": f"Koolnova ({data[CONF_EMAIL]})"}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Koolnova."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            # Validar rangos
            if user_input[CONF_MIN_TEMP] >= user_input[CONF_MAX_TEMP]:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_options_schema(),
                    errors={"base": "temp_range_invalid"}
                )

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_options_schema()
        )

    def _get_options_schema(self):
        """Return options schema."""
        current_data = self.config_entry.data
        current_options = self.config_entry.options

        # Obtener valores actuales o por defecto
        current_interval = current_options.get(CONF_UPDATE_INTERVAL, current_data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
        current_project_modes = current_options.get(CONF_PROJECT_HVAC_MODES, current_data.get(CONF_PROJECT_HVAC_MODES, [mode.value for mode in DEFAULT_PROJECT_HVAC_MODES]))
        current_zone_modes = current_options.get(CONF_ZONE_HVAC_MODES, current_data.get(CONF_ZONE_HVAC_MODES, [mode.value for mode in DEFAULT_ZONE_HVAC_MODES]))
        current_min_temp = current_options.get(CONF_MIN_TEMP, current_data.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP))
        current_max_temp = current_options.get(CONF_MAX_TEMP, current_data.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP))
        current_precision = current_options.get(CONF_TEMP_PRECISION, current_data.get(CONF_TEMP_PRECISION, DEFAULT_TEMP_PRECISION))

        return vol.Schema({
            vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                cv.positive_int, 
                vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)
            ),
            vol.Required(CONF_PROJECT_HVAC_MODES, default=current_project_modes): cv.multi_select({
                mode.value: mode.value.title() for mode in AVAILABLE_HVAC_MODES
            }),
            vol.Required(CONF_ZONE_HVAC_MODES, default=current_zone_modes): cv.multi_select({
                mode.value: mode.value.title() for mode in AVAILABLE_HVAC_MODES
            }),
            vol.Required(CONF_MIN_TEMP, default=current_min_temp): vol.All(
                vol.Coerce(float),
                vol.Range(min=MIN_CONFIGURABLE_TEMP, max=MAX_CONFIGURABLE_TEMP)
            ),
            vol.Required(CONF_MAX_TEMP, default=current_max_temp): vol.All(
                vol.Coerce(float),
                vol.Range(min=MIN_CONFIGURABLE_TEMP, max=MAX_CONFIGURABLE_TEMP)
            ),
            vol.Required(CONF_TEMP_PRECISION, default=current_precision): vol.In(AVAILABLE_TEMP_PRECISIONS),
        })

class CannotConnect(Exception):
    """Error to indicate we cannot connect."""

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
