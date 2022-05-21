"""Support for Innova 2.0 Heat Pump."""
from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity,
    HVACMode,
    HVACAction,
    ClimateEntityFeature,
)
from homeassistant.components.climate.const import (
    SWING_ON,
    SWING_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_HOST,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from innova_controls import Innova, Mode

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Innova entity."""
    host_ip = config.get(CONF_HOST)

    innova = Innova(host=host_ip)
    innova.update()

    add_entities([InnovaEntity(innova)], True)


class InnovaEntity(ClimateEntity):
    """Representation of an Innova AC Unit controls."""

    def __init__(self, innova: Innova):
        """Initialize the thermostat."""
        self._innova = innova
        self._name = None
        self._id = None

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.SWING_MODE
            | ClimateEntityFeature.FAN_MODE
        )

    @property
    def should_poll(self):
        """Set up polling needed for thermostat."""
        return True

    def update(self):
        """Update the data from the thermostat."""
        self._innova.update()
        self._name = self._innova.name
        self._id = self._innova.id

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def unique_id(self):
        """Return the serial number of the system"""
        return self._id

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._innova.ambient_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._innova.target_temperature

    @property
    def target_temperature_step(self) -> float | None:
        """Return the temperature step by which it can be increased/decreased."""
        return 1.0

    @property
    def min_temp(self) -> float:
        return self._innova.min_temperature

    @property
    def max_temp(self) -> float:
        return self._innova.max_temperature

    @property
    def hvac_action(self):
        """Return the current state of the thermostat."""
        mode = self._innova.mode

        if not self._innova.power:
            return HVACAction.OFF
        if mode == Mode.HEATING:
            return HVACAction.HEATING
        if mode == Mode.COOLING:
            return HVACAction.COOLING
        if mode == Mode.DEHUMIDIFICATION:
            return HVACAction.DRYING
        if mode == Mode.FAN_ONLY:
            return HVACAction.FAN
        if mode == Mode.AUTO:
            if self.current_temperature > self.target_temperature + 1:
                return HVACAction.COOLING
            elif self.current_temperature < self.target_temperature - 1:
                return HVACAction.HEATING
            else:
                return HVACAction.IDLE
        return HVACAction.IDLE

    @property
    def hvac_mode(self):
        """Return the current state of the thermostat."""
        if not self._innova.power:
            return HVACMode.OFF

        if self._innova.mode == Mode.COOLING:
            return HVACMode.COOL
        if self._innova.mode == Mode.HEATING:
            return HVACMode.HEAT
        if self._innova.mode == Mode.DEHUMIDIFICATION:
            return HVACMode.DRY
        if self._innova.mode == Mode.FAN_ONLY:
            return HVACMode.FAN_ONLY
        if self._innova.mode == Mode.AUTO:
            return HVACMode.AUTO
        return HVACMode.OFF

    @property
    def hvac_modes(self):
        """Return available HVAC modes."""
        return [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            HVACMode.AUTO,
        ]

    @property
    def fan_modes(self) -> list[str] | None:
        return [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]

    @property
    def fan_mode(self) -> str | None:
        if self._innova.fan_speed == 0:
            return FAN_AUTO
        if self._innova.fan_speed == 1:
            return FAN_LOW
        if self._innova.fan_speed == 2:
            return FAN_MEDIUM
        if self._innova.fan_speed == 3:
            return FAN_HIGH
        return None

    @property
    def swing_modes(self) -> list[str] | None:
        return [SWING_OFF, SWING_ON]

    @property
    def swing_mode(self) -> str | None:
        if self._innova.rotation:
            return SWING_ON
        else:
            return SWING_OFF

    def set_hvac_mode(self, hvac_mode: str) -> None:
        if hvac_mode == HVACMode.OFF:
            self._innova.power_off()
        if hvac_mode == HVACMode.COOL:
            self._innova.set_mode(Mode.COOLING)
        if hvac_mode == HVACMode.HEAT:
            self._innova.set_mode(Mode.HEATING)
        if hvac_mode == HVACMode.DRY:
            self._innova.set_mode(Mode.DEHUMIDIFICATION)
        if hvac_mode == HVACMode.FAN_ONLY:
            self._innova.set_mode(Mode.FAN_ONLY)
        if hvac_mode == HVACMode.AUTO:
            self._innova.set_mode(Mode.AUTO)

    def set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode == FAN_AUTO:
            self._innova.set_fan_speed(0)
        if fan_mode == FAN_LOW:
            self._innova.set_fan_speed(1)
        if fan_mode == FAN_MEDIUM:
            self._innova.set_fan_speed(2)
        if fan_mode == FAN_HIGH:
            self._innova.set_fan_speed(3)

    def set_swing_mode(self, swing_mode: str) -> None:
        if swing_mode == SWING_ON:
            self._innova.rotation_on()
        if swing_mode == SWING_OFF:
            self._innova.rotation_off()

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._innova.set_temperature(temperature)
