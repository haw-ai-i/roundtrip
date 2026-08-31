[Bug]: (Tight) layout engine breaks for 3D patches
### Bug summary

The tight layout sometimes breaks for plots with 3D patches because 'PathPatch3D' object has no attribute '_path2d'.

### Code for reproduction

```python
import matplotlib.pyplot as plt
import matplotlib.patches as pat
import mpl_toolkits.mplot3d.art3d as art3d

fig, ax = plt.subplots(subplot_kw={"projection": "3d"}, layout="tight") # , dpi=300)

p = pat.Rectangle((0, 0), 1.0, 1.0)
ax.add_patch(p)
art3d.pathpatch_2d_to_3d(p)

# fig.set_dpi(300)
# fig.tight_layout()

fig.savefig("test.pdf")  #, dpi=300)
```


### Actual outcome
```
Traceback (most recent call last):
  File "/home/tobias/mne3.py", line 11, in <module>
    fig.savefig("test.pdf")  #, dpi=300)
    ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/figure.py", line 3343, in savefig
    self.canvas.print_figure(fname, **kwargs)
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/backends/backend_qtagg.py", line 75, in print_figure
    super().print_figure(*args, **kwargs)
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/backend_bases.py", line 2342, in print_figure
    self.figure.draw(renderer)
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/artist.py", line 95, in draw_wrapper
    result = draw(artist, renderer, *args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/artist.py", line 72, in draw_wrapper
    return draw(artist, renderer)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/figure.py", line 3134, in draw
    self.get_layout_engine().execute(self)
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/layout_engine.py", line 178, in execute
    kwargs = get_tight_layout_figure(
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/_tight_layout.py", line 266, in get_tight_layout_figure
    kwargs = _auto_adjust_subplotpars(fig, renderer,
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/_tight_layout.py", line 82, in _auto_adjust_subplotpars
    bb += [martist._get_tightbbox_for_layout_only(ax, renderer)]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/artist.py", line 1415, in _get_tightbbox_for_layout_only
    return obj.get_tightbbox(*args, **{**kwargs, "for_layout_only": True})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/mpl_toolkits/mplot3d/axes3d.py", line 3189, in get_tightbbox
    ret = super().get_tightbbox(renderer,
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/axes/_base.py", line 4408, in get_tightbbox
    bbox = a.get_tightbbox(renderer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/artist.py", line 367, in get_tightbbox
    bbox = self.get_window_extent(renderer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/matplotlib/patches.py", line 604, in get_window_extent
    return self.get_path().get_extents(self.get_transform())
           ^^^^^^^^^^^^^^^
  File "/home/tobias/.local/lib/python3.11/site-packages/mpl_toolkits/mplot3d/art3d.py", line 420, in get_path
    return self._path2d
           ^^^^^^^^^^^^
AttributeError: 'PathPatch3D' object has no attribute '_path2d'
```
### Expected outcome

The following code actually produces (something that is at least close enough to) the expected outcome. It does **NOT** produce an error even though I would expect it to be equivalent.
```python
import matplotlib.pyplot as plt
import matplotlib.patches as pat
import mpl_toolkits.mplot3d.art3d as art3d

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

p = pat.Rectangle((0, 0), 1.0, 1.0)
ax.add_patch(p)
art3d.pathpatch_2d_to_3d(p)

fig.tight_layout()

fig.savefig("test.pdf")
```
The result is different compared to the case without the tight layout engine, so I assume it is doing something. However I am not sure if it is fully doing it's job.

### Additional information

Whether I get an error or not depends on some weird circumstances (e.g. the behaviour depends on dpi settings). I left some possible modifications as comments in the minimal example above. Here is a short summary of some test I did:

- `layout="tight"` works with `fig.savefig("test.png")` but **NOT** with `fig.savefig("test.png", dpi=300)`.
- Similarly if I use `plt.subplots(..., dpi=300)` or `fig.set_dpi(300)` the call to `fig.tight_layout()` already gives an error and **NOT** the call to `fig.savefig()`.
- In most cases where it breaks for `layout="tight"` it also breaks for `"compressed"` or `"constrained"`.

### Operating system

Arch

### Matplotlib Version

3.7.1

### Matplotlib Backend

QtAgg

### Python version

Python 3.11.5

### Jupyter version

_No response_

### Installation

Linux package manager
