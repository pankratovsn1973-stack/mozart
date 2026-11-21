# core/bridge_resolver.py
# -*- coding: utf-8 -*-
"""
BridgeResolver — трёхуровневый резолвер функций моста.

Порядок поиска для bridgecalcset / bridgecalcget / fuuncselectionvalue:

  1. Метод класса из БД (class_erp.method_version.txt_method) через
     f_find_class_method(version_id, func_name). Ищется по линии крови:
     сам класс → donor_object_id → c_base_class (если ERP) → i_base_class.
     Не вызываем super() — первый найденный метод побеждает.

  2. SuperLibre (goProject.superlibre) — библиотека простых ERP-методов.

  3. Возвращаем None (вызывающий код решает, что делать).

v7.2 (Этап 0) — КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ:
  - _safe_call(fn, *args, **kwargs) с кэшем сигнатур:
      • Сигнатура недоступна (C-функция)  → вызов как есть.
      • Есть **kwargs в сигнатуре         → передаём все kwargs.
      • Иначе                             → фильтруем kwargs по sig.parameters.
      • Fallback на «голый» вызов (без новых kwargs) допускается ТОЛЬКО если
        TypeError содержит 'unexpected keyword argument' И имя одного из
        наших новых kwargs (prop_id_col, element_id_col, idcol_elem, idcol_prop).
        Иначе — проброс исключения наверх.
  - resolve_to_runtime / resolve_from_runtime / resolve_select принимают
    prop_id_col и element_id_col и прокидывают их в _safe_call.
  - invalidate() очищает и _sig_cache.
"""
import inspect
from typing import Optional, Callable, Dict, Tuple


# Наши «новые» kwargs — только из-за них допустим fallback на старую сигнатуру.
_OUR_KWARGS = frozenset({'prop_id_col', 'element_id_col', 'idcol_elem', 'idcol_prop'})


class BridgeResolver:
    """Резолвер функций моста: метод класса → SuperLibre."""

    def __init__(self, go_project):
        self.go = go_project
        # Кэш скомпилированных методов класса:
        # ключ = (version_id, func_name) → callable | None
        self._compiled_cache: dict[tuple[int, str], Optional[Callable]] = {}
        # Кэш сигнатур:
        # ключ = (id(fn), qualname) → inspect.Signature | None
        self._sig_cache: Dict[Tuple[int, str], Optional[inspect.Signature]] = {}

    # =====================================================================
    # _safe_call: фильтрация kwargs по сигнатуре + точный fallback
    # =====================================================================
    def _get_cached_signature(self, fn: Callable) -> Optional[inspect.Signature]:
        key = (id(fn), getattr(fn, '__qualname__', getattr(fn, '__name__', '?')))
        if key in self._sig_cache:
            return self._sig_cache[key]
        try:
            sig = inspect.signature(fn)
        except (ValueError, TypeError):
            # C-функции / builtins без сигнатуры — работаем как есть
            sig = None
        self._sig_cache[key] = sig
        return sig

    def _safe_call(self, fn: Callable, *args, **kwargs):
        """
        Вызывает fn(*args, **kwargs), отфильтровывая kwargs, которых нет
        в сигнатуре. Fallback на «голый» вызов — ТОЛЬКО если TypeError
        явно указывает на unexpected keyword argument из нашего набора.
        """
        sig = self._get_cached_signature(fn)
        if sig is None:
            # Нет сигнатуры (C-функция) — пробуем как есть.
            return fn(*args, **kwargs)

        params = sig.parameters
        has_var_kw = any(p.kind == p.VAR_KEYWORD for p in params.values())

        if has_var_kw:
            return fn(*args, **kwargs)

        filtered = {k: v for k, v in kwargs.items() if k in params}

        try:
            return fn(*args, **filtered)
        except TypeError as e:
            msg = str(e)
            # Понижаем строгость ТОЛЬКО если виноват наш новый kwarg.
            if ('unexpected keyword argument' in msg
                    and any(kw in msg for kw in _OUR_KWARGS)):
                return fn(*args, **filtered)
            raise

    # =====================================================================
    # SET: bridgecalcset
    # =====================================================================
    def resolve_to_runtime(self, func_name: Optional[str],
                           version_id: int,
                           widget,
                           collection,
                           cname: str,
                           value,
                           prop_id_col: Optional[int] = None,
                           element_id_col: Optional[int] = None) -> bool:
        """
        Применяет значение свойства к живому Qt-виджету.

        Контракт вызова:
          • метод класса в БД → method_fn(self, collection, cname, value, ...)
          • SuperLibre        → fn(widget, collection, cname, value, ...)
        """
        if not func_name or widget is None:
            return False

        method_fn = self._resolve_class_method(version_id, func_name)
        if method_fn is not None:
            try:
                self._safe_call(
                    method_fn, widget, collection, cname, value,
                    prop_id_col=prop_id_col, element_id_col=element_id_col,
                )
                return True
            except Exception as e:
                print(f"[Resolver] Ошибка метода класса '{func_name}': {e}")
                return False

        if hasattr(self.go, 'superlibre'):
            fn = getattr(self.go.superlibre, func_name, None)
            if callable(fn):
                try:
                    self._safe_call(
                        fn, widget, collection, cname, value,
                        prop_id_col=prop_id_col, element_id_col=element_id_col,
                    )
                    return True
                except Exception as e:
                    print(f"[Resolver] Ошибка SuperLibre '{func_name}': {e}")
                    return False

        return False

    # =====================================================================
    # GET: bridgecalcget
    # =====================================================================
    def resolve_from_runtime(self, func_name: Optional[str],
                             version_id: int,
                             widget,
                             collection,
                             cname: str,
                             prop_id_col: Optional[int] = None,
                             element_id_col: Optional[int] = None) -> Optional[str]:
        """
        Читает значение свойства из живого Qt-виджета.

        Контракт вызова:
          • метод класса в БД → method_fn(self, collection, cname, ...)
          • SuperLibre        → fn(widget, collection, cname, ...)
        """
        if not func_name or widget is None:
            return None

        method_fn = self._resolve_class_method(version_id, func_name)
        if method_fn is not None:
            try:
                result = self._safe_call(
                    method_fn, widget, collection, cname,
                    prop_id_col=prop_id_col, element_id_col=element_id_col,
                )
                return str(result) if result is not None else ""
            except Exception as e:
                print(f"[Resolver] Ошибка метода класса '{func_name}': {e}")
                return None

        if hasattr(self.go, 'superlibre'):
            fn = getattr(self.go.superlibre, func_name, None)
            if callable(fn):
                try:
                    result = self._safe_call(
                        fn, widget, collection, cname,
                        prop_id_col=prop_id_col, element_id_col=element_id_col,
                    )
                    return str(result) if result is not None else ""
                except Exception as e:
                    print(f"[Resolver] Ошибка SuperLibre '{func_name}': {e}")
                    return None

        return None

    # =====================================================================
    # SELECT: fuuncselectionvalue
    # =====================================================================
    def resolve_select(self, func_name: Optional[str],
                       version_id: int,
                       widget,
                       collection,
                       cname: str,
                       current_value=None,
                       prop_id_col: Optional[int] = None,
                       element_id_col: Optional[int] = None) -> Optional[str]:
        """
        Открывает диалог выбора значения свойства.

        Контракт вызова:
          • метод класса в БД → method_fn(self, collection, cname, current_value, ...)
          • SuperLibre        → fn(widget, collection, cname, current_value, ...)
        """
        if not func_name:
            return None

        method_fn = self._resolve_class_method(version_id, func_name)
        if method_fn is not None:
            try:
                result = self._safe_call(
                    method_fn, widget, collection, cname, current_value,
                    prop_id_col=prop_id_col, element_id_col=element_id_col,
                )
                return str(result) if result is not None else None
            except Exception as e:
                print(f"[Resolver] Ошибка метода класса '{func_name}': {e}")
                return None

        if hasattr(self.go, 'superlibre'):
            fn = getattr(self.go.superlibre, func_name, None)
            if callable(fn):
                try:
                    result = self._safe_call(
                        fn, widget, collection, cname, current_value,
                        prop_id_col=prop_id_col, element_id_col=element_id_col,
                    )
                    return str(result) if result is not None else None
                except Exception as e:
                    print(f"[Resolver] Ошибка SuperLibre '{func_name}': {e}")
                    return None

        return None

    # =====================================================================
    # Внутреннее: поиск и компиляция метода класса из БД
    # =====================================================================
    def _resolve_class_method(self, version_id: int,
                              func_name: str) -> Optional[Callable]:
        """
        Возвращает скомпилированный callable метода класса или None.
        Кэширует результат, чтобы не дёргать БД повторно.
        """
        if version_id is None or version_id <= 0:
            return None

        cache_key = (version_id, func_name)
        if cache_key in self._compiled_cache:
            return self._compiled_cache[cache_key]

        code = self._find_method_in_db(version_id, func_name)
        if not code:
            self._compiled_cache[cache_key] = None
            return None

        fn = self._compile_method(code, func_name)
        self._compiled_cache[cache_key] = fn
        return fn

    def _find_method_in_db(self, version_id: int, func_name: str) -> Optional[str]:
        """
        Ищет txt_method метода класса по линии крови через f_find_class_method.

        v9 FIX (количество параметров):
        Раньше вызов шёл с 3 параметрами (%s, %s, %s), а SQL-функция
        f_find_class_method принимала только 2 → psycopg2.ProgrammingError
        при каждом резолве. Методы класса никогда не находились, всё уходило
        в SuperLibre, нарушая контракт приоритета.

        v9 FIX (машина времени):
        Добавлен третий параметр p_session_date. SQL-функция обновлена
        отдельно (ALTER FUNCTION) и теперь фильтрует method_class_relation
        и method_version по dt_start/dt_end на дату сессии. Без этого
        резолв игнорировал хронологию и мог вернуть закрытую версию метода.

        Кэширование результата выполняется на уровне _resolve_class_method;
        этот метод — чистый DB-вызов без собственного кэша.
        """
        if not getattr(self.go, 'db_conn', None):
            return None
        try:
            session_date = self.go.system_date.toPython()
            with self.go.db_conn.cursor() as cur:
                cur.execute(
                    "SELECT class_erp.f_find_class_method(%s, %s, %s);",
                    (version_id, func_name, session_date)
                )
                row = cur.fetchone()
                return row[0] if row and row[0] else None
        except Exception as e:
            print(f"[Resolver] Ошибка БД при поиске '{func_name}': {e}")
            return None

    def _compile_method(self, code: str,
                        func_name: str) -> Optional[Callable]:
        """
        Компилирует текст метода (def func_name(self, ...): ...) в callable.
        Возвращает функцию, которую нужно вызвать как fn(widget, ...).
        """
        namespace = {}
        try:
            exec(code, namespace)
        except Exception as e:
            print(f"[Resolver] Ошибка компиляции '{func_name}': {e}")
            return None

        fn = namespace.get(func_name)
        if callable(fn):
            return fn

        # Fallback: ищем первую функцию в namespace
        for name, obj in namespace.items():
            if callable(obj) and not name.startswith('__'):
                return obj

        print(f"[Resolver] В коде метода '{func_name}' не найдено ни одной функции")
        return None

    # =====================================================================
    # Сброс кэшей
    # =====================================================================
    def invalidate(self, version_id: Optional[int] = None):
        """Сбрасывает кэш скомпилированных методов и кэш сигнатур."""
        if version_id is None:
            self._compiled_cache.clear()
            self._sig_cache.clear()
        else:
            for key in list(self._compiled_cache.keys()):
                if key[0] == version_id:
                    del self._compiled_cache[key]
            # _sig_cache не привязан к version_id — чистим целиком
            self._sig_cache.clear()