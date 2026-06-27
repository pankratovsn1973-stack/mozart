# widgets/form_designer_old/property_applier.py
# -*- coding: utf-8 -*-

class PropertyApplier:
    """Сервис атомарного применения измененных свойств к бланку или виджетам."""

    @classmethod
    def apply_to_form(cls, form_obj, prop_name: str, value):
        """Запись параметров геометрии и метаданных в холст формы."""
        if not form_obj:
            return

        if prop_name == "title":
            form_obj.title = str(value)
        elif prop_name == "form_alias":
            form_obj.form_alias = str(value)
        elif prop_name == "x":
            form_obj.setPos(float(value), form_obj.pos().y())
        elif prop_name == "y":
            form_obj.setPos(form_obj.pos().x(), float(value))

        # ОБНОВЛЕНИЕ РАЗМЕРОВ БЛАНКА ФОРМЫ С ПЕРЕРИСОВКОЙ ГРАФИКИ QT
        elif prop_name == "width":
            if hasattr(form_obj, 'set_width'):
                form_obj.set_width(float(value))
            else:
                form_obj._width = float(value)
                if hasattr(form_obj, 'prepareGeometryChange'):
                    form_obj.prepareGeometryChange()
        elif prop_name == "height":
            if hasattr(form_obj, 'set_height'):
                form_obj.set_height(float(value))
            else:
                form_obj._height = float(value)
                if hasattr(form_obj, 'prepareGeometryChange'):
                    form_obj.prepareGeometryChange()

        if form_obj.scene():
            form_obj.scene().update()
        if hasattr(form_obj, 'update_handles_position'):
            form_obj.update_handles_position()

    @classmethod
    def apply_to_control(cls, proxy_obj, prop_name: str, value):
        """Запись геометрических параметров в прокси и ERP-свойств во внутренний виджет."""
        if prop_name in ("x", "y", "width", "height"):
            cls._apply_proxy_geometry(proxy_obj, prop_name, value)
            return

        inner_widget = proxy_obj.widget()
        if not inner_widget:
            return

        if inner_widget.metaObject().indexOfProperty(prop_name) >= 0:
            inner_widget.setProperty(prop_name, value)

        for attr in (prop_name, f"_{prop_name}"):
            if hasattr(inner_widget, attr):
                setattr(inner_widget, attr, value)

        if hasattr(inner_widget, 'properties') and isinstance(inner_widget.properties, dict):
            inner_widget.properties[prop_name] = value

        if prop_name == "label" and hasattr(inner_widget, '_update_label'):
            inner_widget._update_label()

        proxy_obj.updateGeometry()
        if hasattr(proxy_obj, 'update_handles_position'):
            proxy_obj.update_handles_position()

    @classmethod
    def _apply_proxy_geometry(cls, proxy_obj, prop_name: str, value):
        """Безопасный пересчет размеров и координат графического прокси."""
        try:
            rect, pos = proxy_obj.rect(), proxy_obj.pos()
            if prop_name == "x":
                proxy_obj.setPos(float(value), pos.y())
            elif prop_name == "y":
                proxy_obj.setPos(pos.x(), float(value))
            elif prop_name == "width":
                proxy_obj.setWidgetSize(float(value), rect.height())
            elif prop_name == "height":
                proxy_obj.setWidgetSize(rect.width(), float(value))
        except:
            pass
