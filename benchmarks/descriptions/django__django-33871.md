## django/forms/boundfield.py
```markdown
# Specification for `django/forms/boundfield.py`

## 1. Module-Level Preamble

### Imports
*   `import re`
*   `from django.core.exceptions import ValidationError`
*   `from django.forms.utils import pretty_name`
*   `from django.forms.widgets import MultiWidget, Textarea, TextInput`
*   `from django.utils.functional import cached_property`
*   `from django.utils.html import format_html, html_safe`
*   `from django.utils.translation import gettext_lazy as _`

### Constants & Globals
*   `__all__ = ("BoundField",)`

---

## 2. Code Objects

### Class: `BoundField`
Decorated with `@html_safe`. Represents a form field bound to data.

#### Methods

*   **`__init__(self, form, field, name)`**
    *   Initializes instance attributes:
        *   `self.form = form`
        *   `self.field = field`
        *   `self.name = name`
        *   `self.html_name = form.add_prefix(name)`
        *   `self.html_initial_name = form.add_initial_prefix(name)`
        *   `self.html_initial_id = form.add_initial_prefix(self.auto_id)`
        *   `self.label`: If `self.field.label` is `None`, set to `pretty_name(name)`. Otherwise, set to `self.field.label`.
        *   `self.help_text`: Set to `field.help_text` if truthy, else `""`.

*   **`__str__(self)`**
    *   If `self.field.show_hidden_initial` is `True`, returns the concatenation of `self.as_widget()` and `self.as_hidden(only_initial=True)`.
    *   Otherwise, returns `self.as_widget()`.

*   **`subwidgets(self)`**
    *   Decorated with `@cached_property`.
    *   Retrieves `id_` as `self.field.widget.attrs.get("id")` or `self.auto_id`.
    *   Creates `attrs` dictionary: `{"id": id_}` if `id_` is truthy, else `{}`.
    *   Updates `attrs` by calling `self.build_widget_attrs(attrs)`.
    *   Returns a list of `BoundWidget` instances. Each instance is initialized with `(self.field.widget, widget, self.form.renderer)` for every `widget` yielded by `self.field.widget.subwidgets(self.html_name, self.value(), attrs=attrs)`.

*   **`__bool__(self)`**
    *   Returns `True`.

*   **`__iter__(self)`**
    *   Returns `iter(self.subwidgets)`.

*   **`__len__(self)`**
    *   Returns `len(self.subwidgets)`.

*   **`__getitem__(self, idx)`**
    *   Checks if `idx` is an instance of `int` or `slice`. If not, raises a `TypeError` with the message `"BoundField indices must be integers or slices, not %s." % type(idx).__name__`.
    *   Returns `self.subwidgets[idx]`.

*   **`errors(self)`**
    *   Decorated with `@property`.
    *   Returns `self.form.errors.get(self.name, self.form.error_class(renderer=self.form.renderer))`.

*   **`as_widget(self, widget=None, attrs=None, only_initial=False)`**
    *   Sets `widget` to the provided `widget` or `self.field.widget`.
    *   If `self.field.localize` is `True`, sets `widget.is_localized = True`.
    *   Sets `attrs` to the provided `attrs` or `{}`.
    *   Updates `attrs` by calling `self.build_widget_attrs(attrs, widget)`.
    *   If `self.auto_id` is truthy and `"id"` is not in `widget.attrs`, uses `setdefault` on `attrs` to set `"id"` to `self.html_initial_id` (if `only_initial` is `True`) or `self.auto_id` (if `only_initial` is `False`).
    *   Returns the result of `widget.render()`, passing:
        *   `name`: `self.html_initial_name` if `only_initial` else `self.html_name`
        *   `value`: `self.value()`
        *   `attrs`: `attrs`
        *   `renderer`: `self.form.renderer`

*   **`as_text(self, attrs=None, **kwargs)`**
    *   Returns `self.as_widget(TextInput(), attrs, **kwargs)`.

*   **`as_textarea(self, attrs=None, **kwargs)`**
    *   Returns `self.as_widget(Textarea(), attrs, **kwargs)`.

*   **`as_hidden(self, attrs=None, **kwargs)`**
    *   Returns `self.as_widget(self.field.hidden_widget(), attrs, **kwargs)`.

*   **`data(self)`**
    *   Decorated with `@property`.
    *   Returns `self.form._widget_data_value(self.field.widget, self.html_name)`.

*   **`value(self)`**
    *   Initializes `data` to `self.initial`.
    *   If `self.form.is_bound` is `True`, updates `data` to `self.field.bound_data(self.data, data)`.
    *   Returns `self.field.prepare_value(data)`.

*   **`_has_changed(self)`**
    *   If `self.field.show_hidden_initial` is `True`:
        *   Gets `hidden_widget = self.field.hidden_widget()`.
        *   Gets `initial_value = self.form._widget_data_value(hidden_widget, self.html_initial_name)`.
        *   Attempts to convert `initial_value` using `self.field.to_python(initial_value)`.
        *   If a `ValidationError` is raised during conversion, returns `True`.
    *   Otherwise, sets `initial_value = self.initial`.
    *   Returns `self.field.has_changed(initial_value, self.data)`.

*   **`label_tag(self, contents=None, attrs=None, label_suffix=None, tag=None)`**
    *   Sets `contents` to the provided `contents` or `self.label`.
    *   If `label_suffix` is `None`, sets it to `self.field.label_suffix` if it is not `None`, otherwise `self.form.label_suffix`.
    *   If `label_suffix` and `contents` are both truthy, and the last character of `contents` is not in `_(":?.!")`, updates `contents` to `format_html("{}{}", contents, label_suffix)`.
    *   Retrieves `id_` as `self.field.widget.attrs.get("id")` or `self.auto_id`.
    *   If `id_` is truthy:
        *   Gets `id_for_label = self.field.widget.id_for_label(id_)`.
        *   If `id_for_label` is truthy, updates `attrs` to `{**(attrs or {}), "for": id_for_label}`.
        *   If `self.field.required` is `True` and `hasattr(self.form, "required_css_class")` is `True`:
            *   Ensures `attrs` is a dictionary (defaults to `{}`).
            *   If `"class"` is in `attrs`, appends `" " + self.form.required_css_class` to it.
            *   Otherwise, sets `attrs["class"] = self.form.required_css_class`.
    *   Constructs a `context` dictionary:
        *   `"field"`: `self`
        *   `"label"`: `contents`
        *   `"attrs"`: `attrs`
        *   `"use_tag"`: `bool(id_)`
        *   `"tag"`: `tag` or `"label"`
    *   Returns `self.form.render(self.form.template_name_label, context)`.

*   **`legend_tag(self, contents=None, attrs=None, label_suffix=None)`**
    *   Returns `self.label_tag(contents, attrs, label_suffix, tag="legend")`.

*   **`css_classes(self, extra_classes=None)`**
    *   If `extra_classes` has a `split` attribute, calls it to convert to a list.
    *   Converts `extra_classes` to a set (defaulting to an empty set if `None`).
    *   If `self.errors` is truthy and `hasattr(self.form, "error_css_class")` is `True`, adds `self.form.error_css_class` to the set.
    *   If `self.field.required` is `True` and `hasattr(self.form, "required_css_class")` is `True`, adds `self.form.required_css_class` to the set.
    *   Returns the set elements joined by a space `" ".join(...)`.

*   **`is_hidden(self)`**
    *   Decorated with `@property`.
    *   Returns `self.field.widget.is_hidden`.

*   **`auto_id(self)`**
    *   Decorated with `@property`.
    *   Retrieves `auto_id = self.form.auto_id`.
    *   If `auto_id` is truthy and the string `"%s"` is in `str(auto_id)`, returns `auto_id % self.html_name`.
    *   Else if `auto_id` is truthy, returns `self.html_name`.
    *   Otherwise, returns `""`.

*   **`id_for_label(self)`**
    *   Decorated with `@property`.
    *   Retrieves `id_` as `self.field.widget.attrs.get("id")` or `self.auto_id`.
    *   Returns `self.field.widget.id_for_label(id_)`.

*   **`initial(self)`**
    *   Decorated with `@cached_property`.
    *   Returns `self.form.get_initial_for_field(self.field, self.name)`.

*   **`build_widget_attrs(self, attrs, widget=None)`**
    *   Sets `widget` to the provided `widget` or `self.field.widget`.
    *   Creates a shallow copy of `attrs` as a dictionary: `attrs = dict(attrs)`.
    *   If `widget.use_required_attribute(self.initial)`, `self.field.required`, and `self.form.use_required_attribute` are all truthy:
        *   If `hasattr(self.field, "require_all_fields")` is `True`, `self.field.require_all_fields` is `False`, and `isinstance(self.field.widget, MultiWidget)` is `True`:
            *   Iterates over `zip(self.field.fields, widget.widgets)` as `(subfield, subwidget)`.
            *   Sets `subwidget.attrs["required"] = subwidget.use_required_attribute(self.initial) and subfield.required`.
        *   Otherwise, sets `attrs["required"] = True`.
    *   If `self.field.disabled` is truthy, sets `attrs["disabled"] = True`.
    *   Returns `attrs`.

*   **`widget_type(self)`**
    *   Decorated with `@property`.
    *   Returns the lowercase class name of `self.field.widget` with any trailing `"widget"` or `"input"` removed using `re.sub(r"widget$|input$", "", self.field.widget.__class__.__name__.lower())`.

*   **`use_fieldset(self)`**
    *   Decorated with `@property`.
    *   Returns `self.field.widget.use_fieldset`.

---

### Class: `BoundWidget`
Decorated with `@html_safe`. A container class used for iterating over widgets (e.g., choices in a radio select).

#### Methods

*   **`__init__(self, parent_widget, data, renderer)`**
    *   Initializes instance attributes:
        *   `self.parent_widget = parent_widget`
        *   `self.data = data`
        *   `self.renderer = renderer`

*   **`__str__(self)`**
    *   Returns `self.tag(wrap_label=True)`.

*   **`tag(self, wrap_label=False)`**
    *   Constructs a `context` dictionary: `{"widget": {**self.data, "wrap_label": wrap_label}}`.
    *   Returns `self.parent_widget._render(self.template_name, context, self.renderer)`.

*   **`template_name(self)`**
    *   Decorated with `@property`.
    *   If `"template_name"` is a key in `self.data`, returns `self.data["template_name"]`.
    *   Otherwise, returns `self.parent_widget.template_name`.

*   **`id_for_label(self)`**
    *   Decorated with `@property`.
    *   Returns `self.data["attrs"].get("id")`.

*   **`choice_label(self)`**
    *   Decorated with `@property`.
    *   Returns `self.data["label"]`.
```