# widgets/form_designer_old/focus_registry.py
# -*- coding: utf-8 -*-

class FocusRegistry:
    """Централизованный диспетчер фокуса: связывает контейнеры и дочерние ERP-виджеты."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FocusRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance.clear_registry()
        return cls._instance

    def clear_registry(self):
        self._active_container = None
        self._selected_children = []

    def register_focus(self, container_item, child_widgets: list):
        """Мгновенно фиксирует в памяти новый активный контекст."""
        if self._active_container and self._active_container != container_item:
            self.reset_active_context()

        self._active_container = container_item
        self._selected_children = list(child_widgets)

    def get_active_container(self):
        return self._active_container

    def get_selected_children(self):
        return self._selected_children

    def reset_active_context(self):
        """Атомарный сброс фокуса старого контейнера за O(1) без сквозных переборов."""
        if self._active_container:
            try:
                if hasattr(self._active_container, 'clear_internal_selection'):
                    self._active_container.clear_internal_selection()
            except:
                pass
        self.clear_registry()
