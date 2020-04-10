#!/usr/bin/python3

import df_plot
df_plot.DEBUG = True

import pandas
import pickle

test_count = 0
pass_count = 0

with open('data.pkl','rb') as f:
    df = pickle.load(f)

df_plot.set_dataframe(df)

# Setup: get some gui elements
tagtool_list = None
plot_window = None
plot_manager = None

for c in df_plot.main_window.children():
    if type(c) == df_plot.PlotWindow:
        plot_window = c
    elif type(c) == df_plot.TagToolList:
        tagtool_list = c
    elif type(c) == df_plot.PlotManager:
        plot_manager = c

assert plot_window != None, "Fail: couldn't find plot_window"
assert tagtool_list != None, "Fail: couldn't find tagtool_list"
assert plot_manager != None, "Fail: couldn't find plot_manager"


############################################################################
# --- TEST:  press button to add plot, press button again to remove it --- #
############################################################################
############################################################################

print("Test: press button to add plot")

plotvars = ['1LIQCV02.READVALUE',
            '1LIQCV02.SSVALUE',
            '1LIQCV03.READVALUE',
            '1LIQCV03.SSVALUE',]
buttons = [None]*4
for t in tagtool_list._tools:
    if t.name in plotvars:
        i = plotvars.index(t.name)
        buttons[i] = t.plot_button
        continue

        
buttons[0].click()

assert len(plot_manager._plotinfo) == 1, \
    "Incorrect number of elements in _plotinfo."

assert len(plot_manager._plotinfo[0].tagnames) == 1, \
    "Incorrect number of tags in _plotinfo.tagnames"

assert plot_manager._plotinfo[0].tagnames[0] == plotvars[0], \
    "Incorrect tag in _plotinfo.tagnames"

assert plot_manager._taginfo[plotvars[0]].plotinfo == plot_manager._plotinfo[0], \
    "_taginfo.plotinfo is not correct"

gid = plot_manager._taginfo[plotvars[0]].groupid
assert gid in plot_manager._groupid_plots.keys(), \
    "Groupid not in _groupid_plots"

print("Test: press button to remove plot")
buttons[0].click()

assert len(plot_manager._plotinfo) == 0, \
    "Incorrect number of elements in _plotinfo."

assert plot_manager._taginfo[plotvars[0]].plotinfo == None, \
    "_taginfo.plotinfo is not None"

assert gid not in plot_manager._groupid_plots.keys(), \
    "Groupid still in _groupid_plots"


print("Test: add 2 axes, remove one")
for b in buttons:
    b.click()

if len(plot_manager._plotinfo) != 2:
    print("Fail: wrong number of axes in _plotinfo ({})" \
        .format(len(plot_manager._plotinfo))
    )
    exit(1)
if len(plot_manager._plotinfo[0].tagnames) != 2:
    print("Fail: wrong number of tags in _plotinfo.tagnames")
    print(_plotinfo.tagnames)
    exit(1)
if len(plot_manager._plotinfo[1].tagnames) != 2:
    print("Fail: wrong number of tags in _plotinfo.tagnames")
    print(_plotinfo.tagnames)
    exit(1)

if len(plot_manager._groupid_plots) != 2:
    print("Fail: wrong number of _groupid_plots entries")
    print(plot_manager._groupid_plots)
    exit(1)

for var in plotvars:
    assert plot_manager._taginfo[var].plotinfo != None, \
        "{} plotinfo is None".format(var)
    assert plot_manager._taginfo[var].plotinfo in plot_manager._plotinfo, \
        "{} plotinfo not in plot_manager._plotinfo".format(var)

buttons[0].click()
if len(plot_manager._plotinfo) != 2:
    print("Fail: wrong number of axes in _plotinfo ({})" \
        .format(len(plot_manager._plotinfo))
    )
    exit(1)

    assert plot_manager._taginfo[plotvars[0]].plotinfo == None, \
        "{} plotinfo is not None".format(plotvars[0])

buttons[1].click()
if len(plot_manager._plotinfo) != 1:
    print("Fail: wrong number of axes in _plotinfo ({})" \
        .format(len(plot_manager._plotinfo))
    )
    exit(1)
if len(plot_manager._groupid_plots) != 1:
    print("Fail: wrong number of _groupid_plots entries")
    print(plot_manager._groupid_plots)
    exit(1)


df_plot.show()

print("All tests passed")
input("Press enter to continue")
