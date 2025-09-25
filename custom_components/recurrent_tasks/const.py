"""Constants for the Recurrent Tasks integration."""

from __future__ import annotations

from enum import IntFlag, StrEnum
from typing import TYPE_CHECKING

from homeassistant.util.hass_dict import HassKey

if TYPE_CHECKING:
    from homeassistant.helpers.entity_component import EntityComponent
    from . import RecurrentTasksListEntity

DOMAIN = "recurrent_tasks"
DATA_COMPONENT: HassKey[EntityComponent["RecurrentTasksListEntity"]] = HassKey(DOMAIN)

ATTR_DUE = "due"
ATTR_DUE_DATE = "due_date"
ATTR_DUE_DATETIME = "due_datetime"
ATTR_DESCRIPTION = "description"
ATTR_ITEM = "item"
ATTR_RENAME = "rename"
ATTR_STATUS = "status"


class RecurrentTasksServices(StrEnum):
    """Services for the Recurrent Tasks integration."""

    ADD_ITEM = "add_item"
    UPDATE_ITEM = "update_item"
    REMOVE_ITEM = "remove_item"
    GET_ITEMS = "get_items"
    REMOVE_COMPLETED_ITEMS = "remove_completed_items"


class RecurrentTasksEntityFeature(IntFlag):
    """Supported features of the Recurrent Tasks list entity."""

    CREATE_TODO_ITEM = 1
    DELETE_TODO_ITEM = 2
    UPDATE_TODO_ITEM = 4
    MOVE_TODO_ITEM = 8
    SET_DUE_DATE_ON_ITEM = 16
    SET_DUE_DATETIME_ON_ITEM = 32
    SET_DESCRIPTION_ON_ITEM = 64


class RecurrentTasksItemStatus(StrEnum):
    """Status or confirmation of a Recurrent Tasks item."""

    NEEDS_ACTION = "needs_action"
    COMPLETED = "completed"
