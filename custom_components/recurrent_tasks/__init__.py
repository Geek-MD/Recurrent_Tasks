"""The Recurrent Tasks integration."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import dataclasses
import datetime
import logging
from typing import Any, final

from propcache.api import cached_property
import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.components.websocket_api import ERR_NOT_FOUND, ERR_NOT_SUPPORTED
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import (
    CALLBACK_TYPE,
    HomeAssistant,
    ServiceCall,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
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
    validation: Callable[[Any], Any]
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


def _validate_supported_features(
    supported_features: int | None, call_data: dict[str, Any]
) -> None:
    """Validate service call fields against entity supported features."""
    for desc in RECUR_ITEM_FIELDS:
        if desc.service_field not in call_data:
            continue
        if not supported_features or not supported_features & desc.required_feature:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="update_field_not_supported",
                translation_placeholders={"service_field": desc.service_field},
            )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Recurrent Tasks entities."""
    component = hass.data[DATA_COMPONENT] = EntityComponent[RecurrentTasksListEntity](
        _LOGGER, DOMAIN, hass, SCAN_INTERVAL
    )

    frontend.async_register_built_in_panel(
        hass, "recurrent_tasks", "recurrent_tasks", "mdi:clipboard-list"
    )

    websocket_api.async_register_command(
        hass, websocket_handle_subscribe_recurrent_items
    )
    websocket_api.async_register_command(hass, websocket_handle_recurrent_item_list)
    websocket_api.async_register_command(hass, websocket_handle_recurrent_item_move)

    component.async_register_entity_service(
        RecurrentTasksServices.ADD_ITEM,
        vol.All(
            cv.make_entity_service_schema(
                {
                    vol.Required(ATTR_ITEM): vol.All(
                        cv.string, str.strip, vol.Length(min=1)
                    ),
                    **RECUR_ITEM_FIELD_SCHEMA,
                }
            ),
            *RECUR_ITEM_FIELD_VALIDATIONS,
        ),
        _async_add_recurrent_item,
        required_features=[RecurrentTasksEntityFeature.CREATE_TODO_ITEM],
    )
    component.async_register_entity_service(
        RecurrentTasksServices.UPDATE_ITEM,
        vol.All(
            cv.make_entity_service_schema(
                {
                    vol.Required(ATTR_ITEM): vol.All(cv.string, vol.Length(min=1)),
                    vol.Optional(ATTR_RENAME): vol.All(
                        cv.string, str.strip, vol.Length(min=1)
                    ),
                    vol.Optional(ATTR_STATUS): vol.In(
                        {RecurrentTasksItemStatus.NEEDS_ACTION, RecurrentTasksItemStatus.COMPLETED},
                    ),
                    **RECUR_ITEM_FIELD_SCHEMA,
                }
            ),
            *RECUR_ITEM_FIELD_VALIDATIONS,
            cv.has_at_least_one_key(
                ATTR_RENAME,
                ATTR_STATUS,
                *[desc.service_field for desc in RECUR_ITEM_FIELDS],
            ),
        ),
        _async_update_recurrent_item,
        required_features=[RecurrentTasksEntityFeature.UPDATE_TODO_ITEM],
    )
    component.async_register_entity_service(
        RecurrentTasksServices.REMOVE_ITEM,
        cv.make_entity_service_schema(
            {
                vol.Required(ATTR_ITEM): vol.All(cv.ensure_list, [cv.string]),
            }
        ),
        _async_remove_recurrent_items,
        required_features=[RecurrentTasksEntityFeature.DELETE_TODO_ITEM],
    )
    component.async_register_entity_service(
        RecurrentTasksServices.GET_ITEMS,
        cv.make_entity_service_schema(RECUR_SERVICE_GET_ITEMS_SCHEMA),
        _async_get_recurrent_items,
        supports_response=SupportsResponse.ONLY,
    )
    component.async_register_entity_service(
        RecurrentTasksServices.REMOVE_COMPLETED_ITEMS,
        None,
        _async_remove_completed_items,
        required_features=[RecurrentTasksEntityFeature.DELETE_TODO_ITEM],
    )

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


CACHED_PROPERTIES_WITH_ATTR_ = {
    "recurrent_items",
}


class RecurrentTasksListEntity(Entity, cached_properties=CACHED_PROPERTIES_WITH_ATTR_):
    """An entity that represents a Recurrent Tasks list."""

    _attr_recurrent_items: list[RecurrentTasksItem] | None = None
    _update_listeners: list[Callable[[list[JsonValueType] | None], None]] | None = None

    @property
    def state(self) -> int | None:
        """Return the entity state as the count of incomplete items."""
        items = self.recurrent_items
        if items is None:
            return None
        return sum([item.status == RecurrentTasksItemStatus.NEEDS_ACTION for item in items])

    @cached_property
    def recurrent_items(self) -> list[RecurrentTasksItem] | None:
        """Return the Recurrent Task items."""
        return self._attr_recurrent_items

    async def async_create_recurrent_item(self, item: RecurrentTasksItem) -> None:
        raise NotImplementedError

    async def async_update_recurrent_item(self, item: RecurrentTasksItem) -> None:
        raise NotImplementedError

    async def async_delete_recurrent_items(self, uids: list[str]) -> None:
        raise NotImplementedError

    async def async_move_recurrent_item(
        self, uid: str, previous_uid: str | None = None
    ) -> None:
        raise NotImplementedError

    @final
    @callback
    def async_subscribe_updates(
        self,
        listener: Callable[[list[JsonValueType] | None], None],
    ) -> CALLBACK_TYPE:
        """Subscribe to Recurrent Task item updates."""
        if self._update_listeners is None:
            self._update_listeners = []
        self._update_listeners.append(listener)

        @callback
        def unsubscribe() -> None:
            if self._update_listeners:
                self._update_listeners.remove(listener)

        return unsubscribe

    @final
    @callback
    def async_update_listeners(self) -> None:
        """Push updated items to all listeners."""
        if not self._update_listeners:
            return

        items: list[JsonValueType] = [
            dataclasses.asdict(item) for item in self.recurrent_items or ()
        ]
        for listener in self._update_listeners:
            listener(items)

    @callback
    def _async_write_ha_state(self) -> None:
        """Notify subscribers."""
        super()._async_write_ha_state()
        self.async_update_listeners()


# Websocket handlers y servicios (_async_add_recurrent_item, etc.)
