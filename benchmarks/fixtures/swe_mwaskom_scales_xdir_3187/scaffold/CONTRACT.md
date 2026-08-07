# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `seaborn/_core/scales.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Continuous`
- `ContinuousBase`
- `Discrete`
- `Nominal`
- `Ordinal`
- `PseudoAxis`
- `Scale`
- `Temporal`

## `seaborn/utils.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `_default_color`
- `_draw_figure`
- `_normal_quantile_func`
- `adjust_legend_subtitles`
- `axes_ticklabels_overlap`
- `axis_ticklabels_overlap`
- `axlabel`
- `ci`
- `ci_to_errsize`
- `desaturate`
- `despine`
- `get_color_cycle`
- `get_data_home`
- `get_dataset_names`
- `load_dataset`
- `locator_to_legend_entries`
- `move_legend`
- `relative_luminance`
- `remove_na`
- `saturate`
- `set_hls_values`
- `to_utf8`

Implement them to satisfy the specification. Do not write tests.
