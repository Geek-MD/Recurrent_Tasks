"""Intents for the Recurrent Tasks integration."""

from __future__ import annotations
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

from . import RecurrentTasksItem, RecurrentTasksItemStatus, RecurrentTasksListEntity
from .const import DATA_COMPONENT, DOMAIN

INTENT_LIST_ADD_ITEM = "HassListAddItem"
INTENT_LIST_COMPLETE_ITEM = "HassListCompleteItem"

# El resto es igual, solo cambiando nombres y referencias a RecurrentTasks
