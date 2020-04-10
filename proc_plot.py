DEBUG=True

import pandas

import matplotlib
import matplotlib.pyplot as plt
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavBar

import re

from PyQt5 import QtCore
from PyQt5.QtCore import QObject

from PyQt5.QtWidgets import (
        QApplication,
        QWidget,
        QMainWindow,
        QTabWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QScrollArea)

class TagInfoRule():
    def __init__(self,expr,color,sub=None):
        self.expr = expr
        self.rexpr = re.compile(expr)
        self.sub = sub
        self.color = color

    def get_groupid(self,tagname):
        if DEBUG:
            print('Evaluating rule {}'.format(self.expr))

        m = self.rexpr.match(tagname)
        if m:
            if self.sub:
                return self.rexpr.sub(self.sub,tagname)
            else:
                return m.group(1)
        else:
            return None
        
    def get_color(self,tagname):
        return self.color
        
        
class PlotInfo():
    def __init__(self,tagname,groupid,ax):
        self.tagnames = [tagname]
        self.ax = ax
        self.groupid = groupid

class TagInfo():
    '''
    Info about tags (columns in dataframe)

    Attributes:
    -----------
    name : str
        tagname
    plotinfo : PlotInfo
        info about plot, None if not plotted
    groupid : str
        tag group id
    color : str
        color of plot

    '''

    taginfo_rules = [
        TagInfoRule(expr=r'(.*)\.READVALUE',color='C0'),
        TagInfoRule(expr=r'(.*)\.SSVALUE',color='cyan'),
        TagInfoRule(expr=r'(.*)\.HIGHLIMIT',color='red'),
        TagInfoRule(expr=r'(.*)\.LOWLIMIT',color='red'),
    ]

    def __init__(self,tagname):
        self.name = tagname
        self.plotinfo = None # points to a plotinfo if tag is plotted

        self.groupid = None
        self.color = 'black'
        for rule in self.taginfo_rules:
            gid = rule.get_groupid(self.name)
            if gid != None:
                self.groupid=gid
                self.color = rule.get_color(self.name)
                break


    def set_color(self,color):
        sys.stderr.write("changing colors is not implemeted yet.\n'")
        return


class PlotManager(QObject):
    '''
    Class that manages all the plots.

    '''
    def __init__(self,df,plot_window,parent=None):
        QObject.__init__(self,parent)
        '''
        Parameters:
        -----------
        df : pandas.core.frame.DataFrame
            dataframe with plot data
        plot_window : PlotWindow
            window where plotting happens

        '''
        self._df = df
        self._fig = plot_window.fig
        self._canvas = plot_window.canvas

        self._plotinfo = [] # list of info about plot
        self._groupid_plots = {} # dictionary of plotted groupids
        self._taginfo = {} # dictionary of tags

        for tag in self._df:
            self._taginfo[tag] = TagInfo(tag)


    def replot(self,plotinfo):
        '''
        Replot the ax in plotinfo.  Used when adding/removing tags
        '''
        plotinfo.ax.clear()
        color = []
        for tag in plotinfo.tagnames:
            color.append( self._taginfo[tag].color )
        self._df[plotinfo.tagnames].plot(
            color=color,
            ax=plotinfo.ax)

    def add_plot(self,tag):
        taginfo = self._taginfo[tag]

        if taginfo.plotinfo != None:
            sys.stderr.write("Tag {} already plotted.\n".format(tag))
            return

        # check if the groupid has a trend
        groupid = taginfo.groupid
        if groupid in self._groupid_plots.keys():
            # add trend to existing axis
            plotinfo = self._groupid_plots[groupid]
            plotinfo.tagnames.append(tag)
            taginfo.plotinfo = plotinfo
        else:
            nplots = len(self._plotinfo)

            # make a new trend
            if nplots > 0:
                sharex = self._plotinfo[0].ax
            else:
                sharex = None

            # resize existing axes
            gs = matplotlib.gridspec.GridSpec(nplots+1,1)
            for i in range(nplots):
                self._plotinfo[i].ax.set_position( gs[i].get_position(self._fig) )
                self._plotinfo[i].ax.set_subplotspec( gs[i] )


            ax = self._fig.add_subplot(
                nplots+1,1,nplots+1,
                sharex=sharex
            )
            plotinfo = PlotInfo(tag,groupid,ax)
            self._plotinfo.append(plotinfo)
            self._taginfo[tag].plotinfo = plotinfo
            self._groupid_plots[groupid] = plotinfo
        
        self.replot(plotinfo)


    def remove_plot(self,tag):
        taginfo = self._taginfo[tag]
        plotinfo = taginfo.plotinfo
        if plotinfo == None:
            sys.stderr.write("Tag {} is not plotted.\n".format(tag))
            return

        # check if there are other plots in group
        if len(plotinfo.tagnames) > 1:
            # remove only one line
            plotinfo.tagnames.remove(tag)
            if DEBUG:
                print("Removing one variable from list")
                print("Remaining tags:")
                print(plotinfo.tagnames)

            self.replot(plotinfo)

        else:
            # remove whole axes
            if DEBUG:
                print("Removing axis")
            plotinfo.ax.remove()
            self._plotinfo.remove(plotinfo)
            del self._groupid_plots[taginfo.groupid] 

            nplots = len(self._plotinfo)
            gs = matplotlib.gridspec.GridSpec(nplots,1)
            for i in range(nplots):
                self._plotinfo[i].ax.set_position( gs[i].get_position(self._fig) )
                self._plotinfo[i].ax.set_subplotspec( gs[i] )

        taginfo.plotinfo = None


    @QtCore.pyqtSlot(str,bool)
    def add_remove_plot(self,tag,add):
        '''
        Add/Remove a plot.

        Parameters:
        -----------
        tag : str
            column in dataframe to plot
        add : bool
            True = add plot, False = remove plot
        '''

        if DEBUG:
            print("PlotManager::add_remove_plot({},{})".format(tag,add))

        interactive = plt.isinteractive()
        if interactive:
            plt.ioff()

        if add:
            self.add_plot(tag)
        else:
            self.remove_plot(tag)

        self._canvas.draw()

        if interactive:
            plt.ion()
        

    
class PlotWindow(QWidget):
    '''
    A single plot window.


    '''
    def __init__(self,parent=None):
        QWidget.__init__(self,parent)

        self.fig = plt.figure()
        self.canvas = FigCanvas(self.fig)
        self.toolbar = NavBar(self.canvas,self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)



class TagToolList(QWidget):
    def __init__(self,parent=None):
        QWidget.__init__(self,parent)
        self._tools = []


        # scroll_area is the scroll area that
        # will contain all the tools
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # scroll_widget is the widget in the scroll area
        scroll_widget = QWidget(scroll_area)
        scroll_area.setWidget(scroll_widget)

        # tool_layout is the scroll area layout.  Keep it
        # so that you can add tools to it.
        self.tool_layout = QVBoxLayout()
        self.tool_layout.setContentsMargins(0,0,0,0)
        self.tool_layout.setSpacing(0)
        scroll_widget.setLayout(self.tool_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def add_tagtool(self,tagtool):
        if tagtool.parent() != self:
            print("parent",tagtool.parent)
            print("self",self)
            print("Making me the parent")
            tagtool.parent = self

        self._tools.append(tagtool)
        self.tool_layout.addWidget(tagtool)

    def disconnect(self):
        for tool in self._tools:
            tool.plot_button.disconnect()

class TagTool(QWidget):
    '''
    A Widget that contain buttons to add tags to trends

    Attributes:
    -----------
    add_remove_plot : QtCore.Signal(str,bool)
    Signal to add/remove a plot from a plot window.
    '''

    add_remove_plot = QtCore.Signal(str,bool)

    def __init__(self,name,parent_toollist):
        QWidget.__init__(self,parent_toollist)


        self.name = name
        self.plot_button = QPushButton(name)
        self.plot_button.setCheckable(True)
        self.plot_button.toggled.connect(self.plot_clicked)

        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(self.plot_button,1)


        self.setLayout(layout)

        parent_toollist.add_tagtool(self)

    @QtCore.pyqtSlot(bool)
    def plot_clicked(self,is_clicked):
        self.add_remove_plot.emit(self.name,is_clicked)

   
def set_dataframe(df):
    '''
    Set the dataframe to use for plotting.

    The dataframe must be set before the tool will work.

    Parameters:
    -----------
    df : pandas.core.frame.DataFrame
        Dataframe to plot
    '''
    global _isInit
    global _df
    global main_window

    if _isInit:
        print("Dataframe is already initialised")
        print("TODO: enable re-initialising")
        return

    interactive = plt.isinteractive()
    if interactive:
        plt.ioff()

    main_window = QWidget()
    plot_window = PlotWindow(main_window)
    tool_list = TagToolList(main_window)

    layout = QHBoxLayout()
    layout.addWidget(tool_list,0)
    layout.addWidget(plot_window,1)
    main_window.setLayout(layout)

    plot_manager = PlotManager(df,plot_window,main_window)

    for tag in df.columns:
        tool = TagTool(tag,tool_list)
        tool.add_remove_plot.connect(plot_manager.add_remove_plot)
    _isInit = True

    if interactive:
        plt.ion()

def show():
    '''
    Show the plot window.
    '''
    global main_window
    global _isInit
    global _execApp

    if not _isInit:
        sys.stderr.write('Dataframe is not initialised, use set_dataframe to'
                        +' initialise dataframe\n')
        return

    main_window.show()

    print('Window is showing')

    if _execApp:
        app.exec_()
        app.exit()


_isInit = False # has the window been initialised with a dataframe?
_execApp = False # if started with qt, gui loop is running
if plt.get_backend().lower() == 'nbagg':
    print("Explicitly running gui loop for nbAgg")
    _execApp = True

app = QtCore.QCoreApplication.instance()
if app is None:
    print("app was None")
    app = QApplication([])
main_window = None
