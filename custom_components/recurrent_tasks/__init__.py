"""Integración Recurrent Tasks."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from .const import DOMAIN


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configura Recurrent Tasks usando configuration.yaml (no soportado)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Configura Recurrent Tasks desde Config Flow (no aplica en v1.0.0)."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["todo"])
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Desinstala Recurrent Tasks."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["todo"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
