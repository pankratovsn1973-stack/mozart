# -*- coding: utf-8 -*-
"""
Реестр функций трансляции значений low-code свойств в Qt/Python и обратно.
В БД (class_property_bridge, class_version_properties) хранятся ТОЛЬКО имена функций.
Реализации регистрируются при старте приложения.
"""
import inspect
from enum import Enum
from typing import Callable, Optional, Tuple


class BridgeFunctionKind(Enum):
    TO_RUNTIME   = "to_runtime"    # bridgecalcset:  (widget, prop_key, value) -> None
    FROM_RUNTIME = "from_runtime"  # bridgecalcget:  (widget, prop_key) -> str
    SELECT       = "select"        # fuuncselectionvalue: (parent) -> str | None


class BridgeFunctionRegistry:
    """Имена из БД -> callable. Валидация сигнатур при регистрации."""

    def __init__(self):
        self._functions: dict[str, tuple[BridgeFunctionKind, Callable]] = {}

    # ------------------------------------------------------------------
    # Регистрация
    # ------------------------------------------------------------------
    def register(self, name: str, kind: BridgeFunctionKind, fn: Callable):
        if not name:
            raise ValueError("Имя функции не может быть пустым")
        if name in self._functions:
            raise ValueError(f"Функция '{name}' уже зарегистрирована")
        self._assert_signature(kind, fn)
        self._functions[name] = (kind, fn)

    def _assert_signature(self, kind: BridgeFunctionKind, fn: Callable):
        sig = inspect.signature(fn)
        params = [
            p for p in sig.parameters.values()
            if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        ]
        min_args = {
            BridgeFunctionKind.TO_RUNTIME:   3,   # widget, prop_key, value
            BridgeFunctionKind.FROM_RUNTIME: 2,   # widget, prop_key
            BridgeFunctionKind.SELECT:       1,   # parent
        }[kind]
        if len(params) < min_args:
            raise TypeError(
                f"{fn.__name__}: {kind.value} требует минимум {min_args} аргументов, "
                f"получено {len(params)}"
            )

    # ------------------------------------------------------------------
    # Доступ
    # ------------------------------------------------------------------
    def get_to_runtime(self, name: Optional[str]) -> Optional[Callable]:
        return self._get_typed(name, BridgeFunctionKind.TO_RUNTIME)

    def get_from_runtime(self, name: Optional[str]) -> Optional[Callable]:
        return self._get_typed(name, BridgeFunctionKind.FROM_RUNTIME)

    def get_select(self, name: Optional[str]) -> Optional[Callable]:
        return self._get_typed(name, BridgeFunctionKind.SELECT)

    def _get_typed(self, name: Optional[str], kind: BridgeFunctionKind) -> Optional[Callable]:
        if not name:
            return None
        entry = self._functions.get(name)
        if entry is None:
            return None
        entry_kind, fn = entry
        if entry_kind != kind:
            return None
        return fn

    # ------------------------------------------------------------------
    # Диагностика
    # ------------------------------------------------------------------
    def known_names(self) -> list[str]:
        return sorted(self._functions.keys())

    def has_missing(self, names: list[str]) -> list[str]:
        """Возвращает имена, которых нет в реестре (для лога при старте)."""
        return [n for n in names if n and n not in self._functions]