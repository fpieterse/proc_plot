'''
Process Plots

Create an interactive Qt5 widget to plot timeseries data.  Data must be in a
time-indexed dataframe.  Tagnames (columns in dataframe) are analysed to group
related tags (e.g. SP and PV) to plot on the same subplot.
'''

from .pp import add_grouping_rule, \
                remove_grouping_rules, \
                print_grouping_rules, \
                set_dataframe, show

__all__ = ['add_grouping_rule',
           'remove_grouping_rules',
           'print_grouping_rules',
           'set_dataframe',
           'show']


#show = proc_plot.pp.show
