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


## %matplotlib magic
The intended use of the tool is to call it from a jupyter notebook.  The way the qt gui loop runs in jupyter is tricky.  proc_plot checks the current backend (plt.get_backend) to tell if the notebook is using `%matplotlib qt` or `%matplotlib notebook` before matplotlib was imported.  It is possible to switch the backend after the %matplotlib magic, which could break the application.  I recommend using %matplotlib qt and then switching the backend with `plt.switch_backend('nbagg')` if you want interactive notebook plots later.

## Show Me
The tool has a button "Show Me" that will show you python code to generate the current trend.  The code assumes your dataframe is called `df` and that you imported `matplotlib.pyplot as plt`. 
