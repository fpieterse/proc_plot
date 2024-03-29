# proc_plot
Quick interactive trending of time series data for process control data analysis.


## Usage
To start, read process data into a pandas Dataframe.  It will work best if the column names in the dataframe are DCS tagnames e.g. FIC101.SP.  Next, let proc_plot know which dataframe to use and call the show() function to show the main window.

```
%matplotlib qt
import matplotlib.pyplot as plt
import proc_plot
import pandas
df = pandas.read_excel('data.xlsx',parse_dates=True)
proc_plot.set_dataframe(df)
proc_plot.show()
```

## Grouping Rules
proc_plot uses regular expression rules to group tags that should be plotted on the same axis.
See `help(proc_plot.add_grouping_rule)` for examples if you want to customise grouping rules.
Since v1.4, the function load_grouping_template() makes it easy to load preconfigured grouping rules for different kinds of data.  v1.4 includes templates 'ProfCon' and 'DMC'.

## %matplotlib magic
The intended use of proc_plot is to call it from a jupyter notebook.  The way the qt gui loop runs in jupyter is tricky and proc_plot includes logic to check which backend is used (plt.get_backend) to tell if the notebook is using `%matplotlib qt` or `%matplotlib notebook`.

It is possible to switch the backend after the %matplotlib magic, if the backend is switched before proc_plot is imported then proc_plot could break the qt gui loop.  In previous versions of matplotlib I recommended using `%matplotlib qt`, and then switching the backend with `plt.switch_backend('nbagg')` after importing proc_plot if you want to use interactive notebook plots and proc_plot in the same notebook.

In current versions of jupyter notebook and matplotlib, using `%matplotlib notebook` works well.

## Show Me
The tool has a button "Show Me" that will show you python code to generate the current trend.  The code assumes your dataframe is called `df` and that you imported `matplotlib.pyplot as plt`. 
