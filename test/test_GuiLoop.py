#!/usr/bin/python3

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Qt5Agg")

import sys
sys.path.insert(0,'..')
import proc_plot
from proc_plot.pp import PlotWindow, ToolPanel, PlotManager


proc_plot.pp.DEBUG = True

import pandas
import pickle

test_count = 0
pass_count = 0

with open('../loopdata.pkl','rb') as f:
    df = pickle.load(f)

proc_plot.set_dataframe(df)

# Setup: get some gui elements
tool_panel = proc_plot.pp.tool_panel
plot_manager = proc_plot.pp.plot_manager

############################################################################
# --- TEST:  Gui loop should not be executed if %qt is magic is used   --- #
#            in a jupyter notebook.                                        #
#        I'm not sure anymore what this is supposed to test.  I think      #
#        the idea is that the plot should stay open and allow other        #
#        cells in notebook to execute.  This is only useful if you         #
#        are definitely never going to go back to qt window, so don't      #
#        use it.                                                           #
#                                                                          #
############################################################################
############################################################################

print("Main window is showing, it should block the code from executing")
proc_plot.show()

print("Main window is showing again, it should block code again")
proc_plot.show()

matplotlib.use("svg")
print("Main window is showing without gui loop, it should stay up")
proc_plot.show()

a = input('Write something to test if underlying code can continue: ')
print('You wrote',a)
a = input('Press enter to end program')



