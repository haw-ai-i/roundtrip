## django/forms/widgets.py
This is a complete natural-language specification of the `django/forms/widgets.py` file.

### 1. Module-Level Preamble

**Imports:**
*   `copy`
*   `datetime`
*   `re`
*   `warnings`
*   `chain` from `itertools`
*   `settings` from `django.conf`
*   `to_current_timezone` from `django.forms.utils`
*   `static` from `django.templatetags.static`
*   `datetime_safe`, `formats` from `django.utils`
*   `MONTHS` from `django.utils.dates`
*   `get_format` from `django.utils.formats`
*   `format_html`, `html_safe` from `django.utils.html`
*   `mark_safe` from `django.utils.safestring`
*   `gettext_lazy as _` from `django.utils.translation`
*   `get_default_renderer` from `.renderers`

**Constants & Globals:**
*   `__all__`: A tuple containing the names of all public classes and functions exported by the module (e.g., `'Media'`, `'MediaDefiningClass'`, `'Widget'`, `'TextInput'`, etc.).
*   `MEDIA_TYPES`: A tuple `('css', 'js')`.
*   `FILE_INPUT_CONTRADICTION`: An `object()` instance used as a sentinel value to indicate that a file input was both cleared and provided with new data.

### 2. Code Objects (Classes and Functions)

#### `MediaOrderConflictWarning(RuntimeWarning)`
*   **Header:** `class MediaOrderConflictWarning(RuntimeWarning):`
*   **Implementation Logic:** An empty exception class used to warn about conflicts when merging `Media` objects.

#### `Media`
*   **Header:** `@html_safe class Media:`
*   **Implementation Logic:** Represents CSS and JavaScript media required by a widget.
    *   `__init__(self, media=None, css=None, js=None)`: Initializes `_css_lists` and `_js_lists`. If `media` is provided, copies its lists. Otherwise, wraps `css` and `js` in lists if provided.
    *   `render(self)`: Returns a concatenated list of HTML tags for all CSS and JS.
    *   `render_js(self)`: Returns a list of `<script>` tags for all JS files.
    *   `render_css(self)`: Returns a list of `<link>` tags for all CSS files.
    *   `absolute_path(self, path)`: Returns the absolute path for a given media path using `static()` if it doesn't start with `http://`, `https://`, or `/`.
    *   `__getitem__(self, name)`: Returns a new `Media` object containing only the specified media type (`'css'` or `'js'`).
    *   `merge(list_1, list_2)` (staticmethod): Merges two lists of media files, preserving order and removing duplicates. Raises `MediaOrderConflictWarning` if a strict topological sort fails.
    *   `__add__(self, other)`: Returns a new `Media` object combining the CSS and JS of `self` and `other` using `merge()`.

#### `media_property(cls)`
*   **Header:** `def media_property(cls):`
*   **Implementation Logic:** A class decorator/function that returns a property to dynamically evaluate and return a `Media` object for a class, looking at its inner `Media` class and its bases.

#### `MediaDefiningClass(type)`
*   **Header:** `class MediaDefiningClass(type):`
*   **Implementation Logic:** A metaclass that automatically adds a `media` property to classes using `media_property()`.

#### `Widget(metaclass=MediaDefiningClass)`
*   **Header:** `class Widget(metaclass=MediaDefiningClass):`
*   **Attributes:**
    *   `needs_multipart_form = False`
    *   `is_localized = False`
    *   `is_required = False`
    *   `supports_microseconds = True`
    *   `use_fieldset = False`
*   **Implementation Logic:** The base class for all HTML widgets.
    *   `__init__(self, attrs=None)`: Initializes `self.attrs` with a copy of `attrs` or an empty dict.
    *   `__deepcopy__(self, memo)`: Returns a deep copy of the widget, ensuring `attrs` are copied.
    *   `is_hidden(self)` (property): Returns `True` if `self.input_type == 'hidden'`, else `False`.
    *   `subwidgets(self, name, value, attrs=None)`: Yields a dictionary representing the widget for rendering.
    *   `format_value(self, value)`: Returns the value as a string, or `None` if empty.
    *   `get_context(self, name, value, attrs)`: Returns a dictionary containing the context for rendering the widget template (includes `widget` dict with `name`, `is_hidden`, `required`, `value`, `attrs`, `template_name`).
    *   `render(self, name, value, attrs=None, renderer=None)`: Renders the widget to HTML using the specified `renderer` (or default) and `template_name`.
    *   `build_attrs(self, base_attrs, extra_attrs=None)`: Combines `base_attrs` and `extra_attrs`.
    *   `value_from_datadict(self, data, files, name)`: Extracts the widget's value from the `data` dictionary.
    *   `value_omitted_from_data(self, data, files, name)`: Returns `True` if the widget's name is not in `data` or `files`.
    *   `id_for_label(self, id_)`: Returns the ID attribute for the widget's `<label>`.
    *   `use_required_attribute(self, initial)`: Returns `True` if the widget should have the `required` HTML attribute.

#### `Input(Widget)`
*   **Header:** `class Input(Widget):`
*   **Attributes:** `input_type = None`, `template_name = 'django/forms/widgets/input.html'`
*   **Implementation Logic:** Base class for `<input>` widgets. Adds `type` to the context attributes.

#### `TextInput`, `NumberInput`, `EmailInput`, `URLInput`, `PasswordInput`, `HiddenInput`
*   **Header:** Subclasses of `Input`.
*   **Implementation Logic:** Set specific `input_type` (e.g., `'text'`, `'number'`) and `template_name` attributes. `PasswordInput` overrides `get_context` to clear the value if `render_value` is `False`.

#### `MultipleHiddenInput(HiddenInput)`
*   **Header:** `class MultipleHiddenInput(HiddenInput):`
*   **Implementation Logic:** Handles multiple hidden inputs for a single name. Overrides `format_value` to return a list and `value_from_datadict` to use `getlist`.

#### `FileInput(Input)`
*   **Header:** `class FileInput(Input):`
*   **Attributes:** `input_type = 'file'`, `needs_multipart_form = True`
*   **Implementation Logic:** Overrides `format_value` to do nothing. `value_from_datadict` extracts from `files` instead of `data`.

#### `ClearableFileInput(FileInput)`
*   **Header:** `class ClearableFileInput(FileInput):`
*   **Attributes:** `clear_checkbox_label`, `initial_text`, `input_text`, `template_name`.
*   **Implementation Logic:** Adds a checkbox to clear the current file. `value_from_datadict` checks the clear checkbox and returns `FILE_INPUT_CONTRADICTION` if a new file is uploaded while the clear checkbox is checked.

#### `Textarea(Widget)`
*   **Header:** `class Textarea(Widget):`
*   **Attributes:** `template_name = 'django/forms/widgets/textarea.html'`
*   **Implementation Logic:** Renders a `<textarea>`. Sets default `cols` and `rows` attributes.

#### `DateTimeBaseInput(TextInput)`
*   **Header:** `class DateTimeBaseInput(TextInput):`
*   **Attributes:** `format_key = ''`, `format = None`
*   **Implementation Logic:** Base class for date/time inputs. Formats the value using `formats.localize_input`.

#### `DateInput`, `DateTimeInput`, `TimeInput`
*   **Header:** Subclasses of `DateTimeBaseInput`.
*   **Implementation Logic:** Set specific `format_key` (e.g., `'DATE_INPUT_FORMATS'`) and `template_name`.

#### `CheckboxInput(Input)`
*   **Header:** `class CheckboxInput(Input):`
*   **Attributes:** `input_type = 'checkbox'`
*   **Implementation Logic:** Renders a checkbox. `value_from_datadict` returns `True` or `False` based on the presence of the value in `data`. `get_context` sets the `checked` attribute.

#### `ChoiceWidget(Widget)`
*   **Header:** `class ChoiceWidget(Widget):`
*   **Attributes:** `allow_multiple_selected = False`, `input_type = None`, `template_name = None`, `option_template_name = None`
*   **Implementation Logic:** Base class for widgets with choices (selects, radios).
    *   `__init__(self, attrs=None, choices=())`: Initializes `self.choices`.
    *   `subwidgets(self, name, value, attrs=None)`: Yields dictionaries for each option/group.
    *   `options(self, name, value, attrs=None)`: Yields option dictionaries.
    *   `optgroups(self, name, value, attrs=None)`: Groups options into optgroups.
    *   `create_option(self, name, value, label, selected, index, subindex=None, attrs=None)`: Creates a dictionary representing a single `<option>` or radio button.

#### `Select(ChoiceWidget)`
*   **Header:** `class Select(ChoiceWidget):`
*   **Attributes:** `input_type = 'select'`, `template_name = 'django/forms/widgets/select.html'`, `option_template_name = 'django/forms/widgets/select_option.html'`
*   **Implementation Logic:** Renders a `<select>` dropdown.

#### `NullBooleanSelect(Select)`
*   **Header:** `class NullBooleanSelect(Select):`
*   **Implementation Logic:** A `<select>` widget for `NullBooleanField` with 'Unknown', 'Yes', and 'No' choices.

#### `SelectMultiple(Select)`
*   **Header:** `class SelectMultiple(Select):`
*   **Attributes:** `allow_multiple_selected = True`
*   **Implementation Logic:** Renders a `<select multiple>`. `value_from_datadict` uses `getlist`.

#### `RadioSelect(ChoiceWidget)`
*   **Header:** `class RadioSelect(ChoiceWidget):`
*   **Attributes:** `input_type = 'radio'`, `template_name = 'django/forms/widgets/radio.html'`, `option_template_name = 'django/forms/widgets/radio_option.html'`
*   **Implementation Logic:** Renders a list of radio buttons.

#### `CheckboxSelectMultiple(ChoiceWidget)`
*   **Header:** `class CheckboxSelectMultiple(ChoiceWidget):`
*   **Attributes:** `allow_multiple_selected = True`, `input_type = 'checkbox'`, `template_name = 'django/forms/widgets/checkbox_select.html'`, `option_template_name = 'django/forms/widgets/checkbox_option.html'`
*   **Implementation Logic:** Renders a list of checkboxes for multiple selection.

#### `MultiWidget(Widget)`
*   **Header:** `class MultiWidget(Widget):`
*   **Implementation Logic:** A widget composed of multiple sub-widgets.
    *   `__init__(self, widgets, attrs=None)`: Initializes `self.widgets` from a sequence or dictionary of widgets.
    *   `decompress(self, value)`: Must be implemented by subclasses to split a single value into a list of values for the sub-widgets.
    *   `get_context(self, name, value, attrs)`: Builds context by calling `get_context` on each sub-widget.
    *   `value_from_datadict(self, data, files, name)`: Extracts values for all sub-widgets and returns a list.

#### `SplitDateTimeWidget(MultiWidget)`
*   **Header:** `class SplitDateTimeWidget(MultiWidget):`
*   **Implementation Logic:** Combines a `DateInput` and a `TimeInput`. `decompress` splits a `datetime` object into a date and a time.

#### `SplitHiddenDateTimeWidget(SplitDateTimeWidget)`
*   **Header:** `class SplitHiddenDateTimeWidget(SplitDateTimeWidget):`
*   **Implementation Logic:** Same as `SplitDateTimeWidget` but uses `HiddenInput` for both date and time.

#### `SelectDateWidget(Widget)`
*   **Header:** `class SelectDateWidget(Widget):`
*   **Implementation Logic:** Renders three `<select>` widgets for year, month, and day. Handles leap years and custom year/month choices. `value_from_datadict` combines the three select values into a date string.