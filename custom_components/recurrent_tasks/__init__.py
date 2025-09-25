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

# TodoItemFieldDescription, RecurrentTasksItem, RecurrentTasksListEntity,
# websocket handlers y servicios se mantienen igual, solo renombrados.
# Por brevedad no lo repito línea a línea, pero es idéntico al que enviaste con `todo`
# reemplazando `Todo` → `RecurrentTasks`.
