"""Soporte para la lista de tareas Recurrent Tasks."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from homeassistant.components import todo
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list[todo.TodoListEntity], bool], Awaitable[None]],
) -> None:
    """Configura la lista de tareas desde la entrada de configuración."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    tasks: list[dict[str, Any]] = await store.async_load() or []

    entity = RecurrentTasksEntity(hass, store, entry.title, tasks)
    async_add_entities([entity], True)


class RecurrentTasksEntity(todo.TodoListEntity):
    """Entidad de lista de tareas."""

    _attr_has_entity_name = True

    def __init__(
        self, hass: HomeAssistant, store: Store, name: str, tasks: list[dict[str, Any]]
    ) -> None:
        """Inicializa la lista de tareas."""
        self.hass = hass
        self._store = store
        self._attr_name = name
        self._tasks: list[dict[str, Any]] = tasks

    @property
    def todo_items(self) -> list[dict[str, Any]]:
        """Retorna las tareas actuales."""
        return self._tasks

    async def async_create_todo_item(self, item: dict[str, Any]) -> None:
        """Crea una nueva tarea."""
        self._tasks.append(item)
        await self._store.async_save(self._tasks)
        self.async_write_ha_state()

    async def async_update_todo_item(self, item: dict[str, Any]) -> None:
        """Actualiza una tarea existente."""
        for idx, existing in enumerate(self._tasks):
            if existing["uid"] == item["uid"]:
                self._tasks[idx] = item
                break
        await self._store.async_save(self._tasks)
        self.async_write_ha_state()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Elimina tareas por UID."""
        self._tasks = [task for task in self._tasks if task["uid"] not in uids]
        await self._store.async_save(self._tasks)
        self.async_write_ha_state()
