"""Constantes para la integración Recurrent Tasks."""

from __future__ import annotations

from enum import Enum, IntFlag
from typing import TYPE_CHECKING

from homeassistant.util.hass_dict import HassKey

if TYPE_CHECKING:
    from homeassistant.helpers.entity_component import EntityComponent
    from homeassistant.components.todo import TodoListEntity


DOMAIN = "recurrent_tasks"
DATA_COMPONENT: HassKey[EntityComponent["TodoListEntity"]] = HassKey(DOMAIN)

ATTR_DUE = "due"
ATTR_DUE_DATE = "due_date"
ATTR_DUE_DATETIME = "due_datetime"
ATTR_DESCRIPTION = "description"
ATTR_ITEM = "item"
ATTR_RENAME = "rename"
ATTR_STATUS = "status"


class StrEnum(str, Enum):
    """Compatibilidad con Python < 3.11."""

    pass


class TodoServices(StrEnum):
    """Servicios soportados por la integración de tareas."""

    ADD_ITEM = "add_item"
    UPDATE_ITEM = "update_item"
    REMOVE_ITEM = "remove_item"
    GET_ITEMS = "get_items"
    REMOVE_COMPLETED_ITEMS = "remove_completed_items"


class TodoListEntityFeature(IntFlag):
    """Características soportadas por la entidad de lista de tareas."""

    CREATE_TODO_ITEM = 1
    DELETE_TODO_ITEM = 2
    UPDATE_TODO_ITEM = 4
    MOVE_TODO_ITEM = 8
    SET_DUE_DATE_ON_ITEM = 16
    SET_DUE_DATETIME_ON_ITEM = 32
    SET_DESCRIPTION_ON_ITEM = 64


class TodoItemStatus(StrEnum):
    """Estado de un ítem en la lista de tareas (subset de RFC5545)."""

    NEEDS_ACTION = "needs_action"
    COMPLETED = "completed"
