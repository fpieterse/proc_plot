DEBUG=False

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
        QMessageBox,
        QTabWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,)

class TagInfoRule():
    def __init__(self,expr,color,sub=r'\1'):
        self.expr = expr
        self.rexpr = re.compile(expr)
        self.sub = sub
        self.color = color

    def get_groupid(self,tagname):
        m = self.rexpr.match(tagname)
        if m:
            if self.sub:
                return True, self.rexpr.sub(self.sub,tagname)
            else:
                return True, None
        else:
            return False, None
        
        
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
        TagInfoRule(expr=r'(.*)\.PV',color='C0'),
        TagInfoRule(expr=r'(.*)\.MEAS',color='C0'),
        TagInfoRule(expr=r'(.*)\.SP',color='C1'),
        TagInfoRule(expr=r'(.*)\.SPT',color='C1'),
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
            match, gid = rule.get_groupid(self.name)
            if match:
                self.groupid=gid
                self.color = rule.color
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

        self._fig.tight_layout()

    def add_plot(self,tag):
        taginfo = self._taginfo[tag]

        if taginfo.plotinfo != None:
            sys.stderr.write("Tag {} already plotted.\n".format(tag))
            return

        # check if the groupid has a trend
        # but only if groupid is not None
        groupid = taginfo.groupid
        if groupid and groupid in self._groupid_plots.keys():
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
            if groupid:
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
            if taginfo.groupid in self._groupid_plots:
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

    @QtCore.pyqtSlot()
    def showme(self):
        '''
        Show python code to generate the current figure.
        '''

        nrows = len(self._plotinfo)
        code = ''

        if nrows > 0:
            code += 'fig,ax = plt.subplots(nrows={},sharex=True)\n'.format(nrows)

            i = 0 
            for plotinfo in self._plotinfo:
                color = []
                for tag in plotinfo.tagnames:
                    color.append( self._taginfo[tag].color )

                xlim = plotinfo.ax.get_xlim()
                x0 = pandas.Timestamp(xlim[0],unit='m')
                x1 = pandas.Timestamp(xlim[1],unit='m')
                ylim = plotinfo.ax.get_ylim()

                code += 'df.plot(\n' + \
                        '    y={},\n'.format(plotinfo.tagnames) + \
                        '    color={},\n'.format(color) + \
                        '    xlim=("' + x0.strftime('%Y-%m-%d %H:%M') +'",\n' + \
                        '          "' + x1.strftime('%Y-%m-%d %H:%M') + '"),\n' + \
                        '    ylim={},\n'.format(ylim)

                if nrows > 1:
                    code += '    ax=ax[{}],\n'.format(i)
                else:
                    code += '    ax=ax,\n'
                    
                code += ')\n'

                i += 1


            code += 'fig.tight_layout()\n'

        print(code)

        QMessageBox.information(None, "Show Me",
                                      code,
                                      QMessageBox.Ok, QMessageBox.Ok)


        

    
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



class ToolPanel(QWidget):
    '''
    Widget that contains all the plotting tools.


    Signals:
    --------
    showme_clicked
        Show Me button clicked
    '''

    showme_clicked = QtCore.Signal()

    def __init__(self,parent=None):
        QWidget.__init__(self,parent)
        self._tools = []

        showme_button = QPushButton('Show Me')
        showme_button.clicked.connect(self.showme_clicked)


        self.filter_textbox = QLineEdit()
        self.filter_textbox.textChanged.connect(self.filter_changed)


        # scroll_area is the scroll area that
        # will contain all the tools
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # scroll_widget is the widget in the scroll area
        scroll_widget = QWidget(scroll_area)
        scroll_area.setWidget(scroll_widget)

        # scroll_layout is the scroll area layout, it contains
        # tool_layout where all the tools are and a bit of stretch
        # tool_layout is saved so you can add tools to it later
        self.tool_layout = QVBoxLayout()
        self.tool_layout.setContentsMargins(0,0,0,0)
        self.tool_layout.setSpacing(0)
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(0,0,0,0)
        scroll_layout.setSpacing(0)
        scroll_layout.addLayout(self.tool_layout)
        scroll_layout.addStretch(1)

        scroll_widget.setLayout(scroll_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(showme_button)
        main_layout.addWidget(self.filter_textbox)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def add_tagtool(self,tagtool):
        if tagtool.parent() != self:
            if DEBUG:
                print("Changing parent of TagTool")
                print("{} -> {}".format(tagtool.parent,self))
            tagtool.parent = self

        self._tools.append(tagtool)
        self.tool_layout.addWidget(tagtool)

    QtCore.pyqtSlot(str)
    def filter_changed(self,filter_text):
        for tool in self._tools:
            if filter_text in tool.name:
                tool.show()
            else:
                tool.hide()
        


class TagTool(QWidget):
    '''
    A Widget that contain buttons to add tags to trends

    Signals:
    --------
    add_remove_plot : QtCore.Signal(str,bool)
        Signal to add/remove a plot from a plot window.
    '''

    add_remove_plot = QtCore.Signal(str,bool)

    def __init__(self,name,parent_toollist):
        '''
        Constructing a tool also adds it to its parent ToolPanel's layout

        Parameters:
        -----------
        name : str
            tagname
        parent_toollist : ToolPanel
            Qt parent, this tool is also added to the toollist's layout

        '''
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

def add_grouping_rule(expr,color,sub=r'\1'):
    '''
    Add a rule to group trends.

    Each tag (column in dataframe) is passed through a regular expression
    defined in each rule.  When a rule expression matches the tag, then the tag groupid and color is set
    as specified by the rule.  Tags with the same groupid is plotted on the same
    axis.

    The regular expressions are evaluated by the 're' library.  It is advised to
    set expr and sub as raw strings.

    Some defaults are configured already, try to run print_grouping_rules to see
    all the defined rules.

    Examples:
    ---------

    Example 1:
    The default is to return the first regex group as the groupid.  This example
    returns a tag's stem as the groupid for SP and PV (note OP is not part of
    the group

    expr: r'(.*)\.PV'
    color: 'blue'
    sub: r'\\1' (default)
    
    expr: r'(.*)\.SP'
    color: 'yellow'
    sub: r'\\1' (default)
   

    Example 2:
    If you want to trend experion tags in the same group:

    expr:  r'(.*)\.(DACA|PIDA)\.PV'
    color: 'blue'
    sub: r'\\1' (default)

    expr:  r'(.*)\.(DACA|PIDA)\.SP'
    color: 'yellow'
    sub: r'\\1' (default)


    Example 3:
    Suppose you have indicators e.g. 00TI1234 that would be the PV of e.g.
    00TC1234.SP.  In this example, the groupid is set to 00TC1234 for both the
    TI and the TC.  You need to make use of the substitute string because the
    first re group is not the groupid.

    expr:   r'([0-9]{2,}.)I([0-9]{4,})'
    sub:    r'\\1C\\2'
    color: 'blue'

    expr:   r'([0-9]{2,}.)C([0-9]{4,})\.SP'
    sub:    r'\\1C\\2'
    color: 'blue'

    tag          groupid
    ------------------------------
    00TI1234     00TC1234
    00TC1234.SP  00TC1234
    11TC1234.OP  None
    22FI1001     22FC1234
    22FC5005.SP  22FC5005
    33AI1111     33AC1111


    

    Parameters:
    -----------
    expr : str
        regular expression to evaluate
    color : str
        matplotlib color of trend where tag matches expr
    sub : str, optional
        regular expression replacement str to return groupid.  Default is r'\\1'
        which returns the first group in expr.  If set to None, then a groupid
        of None is returned (tag is ungrouped).

    '''

    TagInfo.taginfo_rules.insert(0,
        TagInfoRule(expr,color,sub)
    )

def print_grouping_rules():
    '''
    Print all grouping rules.
    '''
    print("{:<3} {:<60} {:^10} {}".format("","expr","color","sub"))
    print("{:->80}".format(''))
    for i in range(len(TagInfo.taginfo_rules)):
        rule = TagInfo.taginfo_rules[i]
        if rule.sub == None:
            sub = 'None'
        else:
            sub = rule.sub
        print("{:<3} {:<60} {:^10} {}"\
            .format(i, rule.expr, rule.color, sub )
        )
        
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
    tool_list = ToolPanel(main_window)

    layout = QHBoxLayout()
    layout.addWidget(tool_list,0)
    layout.addWidget(plot_window,1)
    main_window.setLayout(layout)

    plot_manager = PlotManager(df,plot_window,main_window)

    showme_dialog = QMessageBox(main_window)


    tool_list.showme_clicked.connect(plot_manager.showme)

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

    if DEBUG:
        print("Showing main window")

    if _execApp:
        app.exec_()
        app.exit()


_isInit = False # has the window been initialised with a dataframe?
_execApp = False # if started with qt, gui loop is running
if plt.get_backend().lower() == 'nbagg':
    _execApp = True
    if DEBUG:
        print("Explicitly running gui loop for nbAgg")

app = QtCore.QCoreApplication.instance()
if app is None:
    app = QApplication([])
    if DEBUG:
        print("app was None")

main_window = None


