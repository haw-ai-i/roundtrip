[ENH]: pickle (or save) matplotlib figure with insteractive slider
### Problem

I'd like to save/pickle a matplotlib figure containing a `matplotlib.widgets.Widget` object to send it to a colleague without him having to run the code I use to generate it.

I know since matplotlib version 1.2 `matplotlib.figure.Figure` are pickable. However, when the figure contains a `matplotlib.widgets.Widget`, pickle fails to save it.

For example consider this class:

```
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets

import numpy as np

import pickle as pkl

class interactive_plot():

    def __init__(self, add_slider):

        self.fig, self.axs = plt.subplots(2,1, gridspec_kw={'height_ratios':[10,1]})

        self.x_plot = np.linspace(0,10,1000)
        self.line = self.axs[0].plot(self.x_plot, self.x_plot*0)[0]
        self.axs[0].set_ylim((0,10))
        self.axs[0].grid()
        self.axs[0].set_title(r'$y = x^\alpha$')

        if add_slider:
            self.slider= widgets.Slider(
                self.axs[1],
                label   = r'$\alpha$',
                valmin  = 0,
                valmax  = 5,
                valinit = 0,
                valstep = .01
                )
            self.slider.on_changed(self.update)

    def update(self, val):
        self.line.set_ydata(self.x_plot**val)
```

If I run

```
h = interactive_plot(add_slider=False)
with open('test.pkl','wb') as f: pkl.dump(h, f)
```
all works properly. However
```
h = interactive_plot(add_slider=True)
with open('test.pkl','wb') as f: pkl.dump(h, f)
```
returns
```
Traceback (most recent call last):

  File "C:\Users\user\Desktop\test.py", line 47, in <module>
    with open('test.pkl','wb') as f: pkl.dump(h, f)

TypeError: cannot pickle 'FigureCanvasQTAgg' object
```

Is there a way to workaround this?

DISCLAIMER: The same question was posted here https://stackoverflow.com/questions/71145817/pickle-or-save-matplotlib-figure-with-insteractive-slider

### Proposed solution

_No response_
