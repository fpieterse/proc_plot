#!/usr/bin/python3

import sys
sys.path.insert(0,'..')
import proc_plot
from proc_plot.pp import PlotWindow, ToolPanel, PlotManager

proc_plot.pp.DEBUG = True

import pandas
import pickle

test_count = 0
pass_count = 0

# Setup: get some gui elements
tagtool_list = proc_plot.pp.tool_panel
plot_manager = proc_plot.pp.plot_manager

with open('../data.pkl','rb') as f:
    df = pickle.load(f)

############################################################################
# --- TEST:  colors, groupids, rules                                   --- #
############################################################################
############################################################################

print("Testing adding/removing grouping rules.",
      "There should be a message warning you that it will not have",
      "an effect until the dataframe is set again")
n_rules = len(proc_plot.pp.TagInfo.taginfo_rules)
rule_0 = proc_plot.pp.TagInfo.taginfo_rules[0]
rule_n = proc_plot.pp.TagInfo.taginfo_rules[-1]

proc_plot.remove_grouping_rules(1)
assert len(proc_plot.pp.TagInfo.taginfo_rules) == n_rules - 1, \
    'One rule should have been removed'
assert proc_plot.pp.TagInfo.taginfo_rules[0] == rule_0, \
    'First rule has changed'

assert proc_plot.pp.TagInfo.taginfo_rules[-1] == rule_n, \
    'Last rule has changed'

try:
    proc_plot.remove_grouping_rules(n_rules)
except Exception as e:
    print(e)

assert len(proc_plot.pp.TagInfo.taginfo_rules) == n_rules-1, \
    'Number of rules changed when incorrect index was specified'

proc_plot.remove_grouping_rules()
assert len(proc_plot.pp.TagInfo.taginfo_rules) == 0, \
    'Number of rules must be zero after remove'

proc_plot.add_grouping_rule(r'(.*)\.READVALUE$','C0')
proc_plot.add_grouping_rule(r'(.*)\.SSVALUE$','cyan')
proc_plot.add_grouping_rule(r'(.*)\.HIGHLIMIT$','red')
proc_plot.add_grouping_rule(r'(.*)\.LOWLIMIT$','red')
proc_plot.add_grouping_rule(r'.*\.CONSTRAINTTYPE$',None,'CONSTRAINTTYPE')
proc_plot.add_grouping_rule(r'1LIQCV02.READVALUE','yellow',None)

proc_plot.set_dataframe(df)

test_config = [
    ('1LIQCV01.READVALUE','C0','1LIQCV01'),
    ('1LIQCV11.READVALUE','C0','1LIQCV11'),
    ('1LIQCV12.READVALUE','C0','1LIQCV12'),
    ('1LIQCV13.HIGHLIMIT','red','1LIQCV13'),
    ('1LIQCV13.CONSTRAINTTYPE', None, 'CONSTRAINTTYPE'),
    ('1LIQ_CTL.COMMON.CONTROLLERMODE',None,None),
    ('1LIQCV02.READVALUE','yellow', None)
]

for t in test_config:
    var = t[0]
    col = t[1]
    gid = t[2]
    taginfo = plot_manager._taginfo[var]
    assert taginfo.groupid == gid, \
        '{} groupid is {}'.format(var,taginfo.groupid)
    assert taginfo.color == col, \
        '{} color is {}'.format(var,taginfo.color)





############################################################################
# --- TEST:  press button to add plot, press button again to remove it --- #
############################################################################
############################################################################

print("Test: press button to add plot")

plotvars = ['1LIQCV04.READVALUE',
            '1LIQCV04.SSVALUE',
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


proc_plot.show()

print("All tests passed")
