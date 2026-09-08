Regression line not appearing over scatterplot when using .add(so.Line(), so.PolyFit())
I'm trying to create a scatterplot with a regression line over the top.  When I try to do this with `.add(so.Line(), so.PolyFit())` the trend line fails to appear.

Here is the code that I'm using to attempt to create the scatterplot + regression line:

```
import pandas as pd
import seaborn.objects as so

supercars = pd.read_csv('https://learn.sharpsightlabs.com/datasets/pdm/supercars.csv')


(so.Plot(data = supercars
         ,x = 'horsepower'
         ,y = 'top_speed'
         )
   .add(so.Dot())
   .add(so.Line(), so.PolyFit())
 )
```

And here is the output:

![seaborn-objects_scatter-with-regression-line_GITHUB-ISSUE](https://user-images.githubusercontent.com/115200284/196320891-98b01881-ad27-463b-9b33-fb1584236916.png)

As you can see, the scatterplot plots as expected, but the regression line is missing.

To show you what I'm expecting to appear, I'll create a "regplot" with 'sns.regplot':


```
import seaborn as sns

sns.regplot(data = supercars
         ,x = 'horsepower'
         ,y = 'top_speed'
         )

```

OUT:

![seaborn_regplot_GITHUB-ISSUE](https://user-images.githubusercontent.com/115200284/196321123-297470cd-78bb-4ba1-92ab-c6d01f74a78c.png)

As you can see, with the traditional "regplot" the scatterplot has a regression line over it.

I think that in my Seaborn Objects code is correct, but perhaps I've made a mistake.

If not, and my code is correct, then it seems that there's a bug in how Seaborn Objects is operating on this particular dataset.

