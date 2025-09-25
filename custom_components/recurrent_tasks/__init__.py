"""The Recurrent Tasks integration."""

from __future__ import annotations

import dataclasses
import datetime
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    CALLBACK_TYPE,
    HomeAssistant,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JsonValueType

from .const import (
    ATTR_DESCRIPTION,
    ATTR_DUE,
    ATTR_DUE_DATE,
    ATTR_DUE_DATETIME,
    ATTR_ITEM,
    ATTR_RENAME,
    ATTR_STATUS,
    DATA_COMPONENT,
    DOMAIN,
    RecurrentTasksItemStatus,
    RecurrentTasksEntityFeature,
    RecurrentTasksServices,
)

_LOGGER = logging.getLogger(__name__)

ENTITY_ID_FORMAT = DOMAIN + ".{}"
PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA
PLATFORM_SCHEMA_BASE = cv.PLATFORM_SCHEMA_BASE
SCAN_INTERVAL = datetime.timedelta(seconds=60)


@dataclasses.dataclass
class RecurrentTasksItemFieldDescription:
    """A description of Recurrent Tasks item fields and validation requirements."""

    service_field: str
    recurrent_item_field: str
    validation: Any
    required_feature: RecurrentTasksEntityFeature


RECUR_ITEM_FIELDS = [
    RecurrentTasksItemFieldDescription(
        service_field=ATTR_DUE_DATE,
        validation=vol.Any(cv.date, None),
        recurrent_item_field=ATTR_DUE,
        required_feature=RecurrentTasksEntityFeature.SET_DUE_DATE_ON_ITEM,
    ),
    RecurrentTasksItemFieldDescription(
        service_field=ATTR_DUE_DATETIME,
        validation=vol.Any(vol.All(cv.datetime, dt_util.as_local), None),
        recurrent_item_field=ATTR_DUE,
        required_feature=RecurrentTasksEntityFeature.SET_DUE_DATETIME_ON_ITEM,
    ),
    RecurrentTasksItemFieldDescription(
        service_field=ATTR_DESCRIPTION,
        validation=vol.Any(cv.string, None),
        recurrent_item_field=ATTR_DESCRIPTION,
        required_feature=RecurrentTasksEntityFeature.SET_DESCRIPTION_ON_ITEM,
    ),
]

RECUR_ITEM_FIELD_SCHEMA = {
    vol.Optional(desc.service_field): desc.validation for desc in RECUR_ITEM_FIELDS
}
RECUR_ITEM_FIELD_VALIDATIONS = [
    cv.has_at_most_one_key(ATTR_DUE_DATE, ATTR_DUE_DATETIME)
]
RECUR_SERVICE_GET_ITEMS_SCHEMA = {
    vol.Optional(ATTR_STATUS): vol.All(
        cv.ensure_list,
        [vol.In({RecurrentTasksItemStatus.NEEDS_ACTION, RecurrentTasksItemStatus.COMPLETED})],
    ),
}


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Recurrent Tasks entities."""
    component = hass.data[DATA_COMPONENT] = EntityComponent[RecurrentTasksListEntity](
        _LOGGER, DOMAIN, hass, SCAN_INTERVAL
    )

    frontend.async_register_built_in_panel(
        hass, "recurrent_tasks", "Recurrent Tasks", "mdi:clipboard-list"
    )

    # ⚠️ Elimino los websocket handlers porque aún no están implementados
    # websocket_api.async_register_command(hass, websocket_handle_subscribe_recurrent_items)
    # websocket_api.async_register_command(hass, websocket_handle_recurrent_item_list)
    # websocket_api.async_register_command(hass, websocket_handle_recurrent_item_move)

    await component.async_setup(config)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    return await hass.data[DATA_COMPONENT].async_setup_entry(entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.data[DATA_COMPONENT].async_unload_entry(entry)


@dataclasses.dataclass
class RecurrentTasksItem:
    """A Recurrent Task item."""

    summary: str | None = None
    uid: str | None = None
    status: RecurrentTasksItemStatus | None = None
    due: datetime.date | datetime.datetime | None = None
    description: str | None = None


class RecurrentTasksListEntity(Entity):
    """An entity that represents a Recurrent Tasks list."""

    _attr_recurrent_items: list[RecurrentTasksItem] | None = None

    @property
    def state(self) -> int | None:
        """Return the entity state as the count of incomplete items."""
        items = self._attr_recurrent_items
        if items is None:
            return None
        return sum([item.status == RecurrentTasksItemStatus.NEEDS_ACTION for item in items])
