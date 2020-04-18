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
    def __init__(self,expr,color=None,sub=r'\1'):
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
        TagInfoRule(expr=r'(.*)\.PV$',color='C0'),
        TagInfoRule(expr=r'(.*)\.MEAS$',color='C0'),
        TagInfoRule(expr=r'(.*)\.SP$',color='C1'),
        TagInfoRule(expr=r'(.*)\.SPT$',color='C1'),
    ]

    def __init__(self,tagname):
        '''
        Constructor

        Parameters:
        -----------
        tagname : str
            name of tag
        '''

        self.name = tagname
        self.plotinfo = None # points to a plotinfo if tag is plotted

        self.groupid = None
        self.color = None
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

    def __init__(self,parent=None):
        QObject.__init__(self,parent)

        self._df = None
        self.plot_window = PlotWindow()
        self.plot_window.home_zoom_signal.connect(self.home_zoom)

        self._plotinfo = [] # list of info about plot
        self._groupid_plots = {} # dictionary of plotted groupids
        self._taginfo = {} # dictionary of tags

    def set_dataframe(self,df):
        self.clear_all_plots()

        self._df = df
        self._taginfo.clear()

        for tag in self._df:
            # Check if we can plot the tag
            dt = self._df[tag].dtype
            if dt in (float,int,bool,'int64'):
                self._taginfo[tag] = TagInfo(tag)
            else:
                if DEBUG:
                    print('Tag {} is not plottable'.format(tag))
                    print('    dtype is {}'.format(dt))
                continue


    def get_tagtools(self):
        '''
        Get tagtools of all validated _taginfos
        '''
        tools = [ TagTool(t) for t in self._taginfo ]
        for tool in tools:
            tool.add_remove_plot.connect(self.add_remove_plot)

        return tools
            

    @QtCore.pyqtSlot()
    def home_zoom(self):
        '''
        Sets the zoom level to default.
        '''
        if DEBUG:
            print('PlotManager::home_clicked()')

        try:
            #plt.margins(0,0.05)
            if len(self._plotinfo) > 0:
                for pi in self._plotinfo:
                    pi.ax.autoscale(axis='x',tight=True)
                    pi.ax.autoscale(axis='y',tight=False)
            self.plot_window.canvas.draw()

            
            
        except Exception as e:
            sys.stderr.write(e)

    @QtCore.pyqtSlot()
    def clear_all_plots(self):
        if DEBUG:
            print('PlotManager::clear_all_plots()')

        try:
            
            while len(self._plotinfo) > 0:
                p = self._plotinfo.pop()
                for t in p.tagnames:
                    self._taginfo[t].plotinfo = None
            
            self._plotinfo.clear()
            self._groupid_plots.clear()
            self.plot_window.fig.clear()
            self.plot_window.toolbar._nav_stack.clear()
            self.plot_window.canvas.draw()
        except Exception as e:
            sys.stderr.write(e)
            

  
    @QtCore.pyqtSlot()
    def refresh(self):
        try:
            if DEBUG:
                print("PlotManager::refresh()")

            for pi in self._plotinfo:
                self.replot(pi)

            self.plot_window.toolbar._nav_stack.clear()
            self.plot_window.fig.tight_layout()
            self.plot_window.canvas.draw()
        except Exception as e:
            sys.stderr.write(e)

    def replot(self,plotinfo,save_xlim=False):
        '''
        Replot the ax in plotinfo.  Used when adding/removing tags
        '''

        if save_xlim:
            xlim = plotinfo.ax.get_xlim()

        plotinfo.ax.clear()

        color = [ self._taginfo[t].color for t in plotinfo.tagnames ]
        self._df.plot(
            y=plotinfo.tagnames,
            color=color,
            ax=plotinfo.ax,
            legend=True,
            include_bool=True,
        )

        if save_xlim:
            plotinfo.ax.set_xlim(xlim)



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

            # Only plot new tag so that zoom doesn't change
            if DEBUG:
                print("Adding tag to axis")

            xlim = plotinfo.ax.get_xlim()

            self._df[tag].plot(color=taginfo.color,
                               ax=plotinfo.ax,
                               legend=True,
                               include_bool=True)

            plotinfo.ax.set_xlim(xlim)

        else:
            nplots = len(self._plotinfo)

            # make a new trend
            if nplots > 0:
                sharex = self._plotinfo[0].ax
            else:
                sharex = None

            # resize existing axes
            if DEBUG:
                print("Resize existing axes")
            gs = matplotlib.gridspec.GridSpec(nplots+1,1)
            for i in range(nplots):
                self._plotinfo[i].ax.set_position( gs[i].get_position(self.plot_window.fig) )
                self._plotinfo[i].ax.set_subplotspec( gs[i] )

            if DEBUG:
                print("Create new axes")
            ax = self.plot_window.fig.add_subplot(
                nplots+1,1,nplots+1,
                label=groupid,
                sharex=sharex
            )
            plotinfo = PlotInfo(tag,groupid,ax)
            self._plotinfo.append(plotinfo)
            self._taginfo[tag].plotinfo = plotinfo
            if groupid:
                self._groupid_plots[groupid] = plotinfo
       
            if DEBUG:
                print("Replotting new axis")

            self.replot(plotinfo,save_xlim=(sharex!=None))

            if DEBUG:
                print("Clearing navstack")
            self.plot_window.toolbar._nav_stack.clear()


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

            self.replot(plotinfo,save_xlim=True)

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
                self._plotinfo[i].ax.set_position( gs[i].get_position(self.plot_window.fig) )
                self._plotinfo[i].ax.set_subplotspec( gs[i] )

            if len(self._plotinfo) == 0:
                if DEBUG:
                    print("no more plots left")
                    self.plot_window.toolbar._nav_stack.clear()

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

        try:
            if add:
                self.add_plot(tag)
            else:
                self.remove_plot(tag)

            self.plot_window.canvas.draw()
        except Exception as e:
            sys.stderr.write(e)


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

    # signal is emitted when home is clicked but navstack
    # is empty
    home_zoom_signal = QtCore.Signal()
    

    def __init__(self,parent=None):
        QWidget.__init__(self,parent)

        self.fig = plt.figure()
        self.canvas = FigCanvas(self.fig)
        self.toolbar = NavBar(self.canvas,self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # find toolbar's home button
        home_action = None
        for action in self.toolbar.actions():
            if action.text() == 'Home':
                home_action = action
                break

        if home_action == None:
            sys.stderr.write('Home action in Qt Navbar not found')
        else:
            home_action.triggered.connect(self.home_clicked)

    @QtCore.pyqtSlot()
    def home_clicked(self):
        if self.toolbar._nav_stack.empty():
            self.home_zoom_signal.emit()
                



class ToolPanel(QWidget):
    '''
    Widget that contains all the plotting tools.


    Signals:
    --------
    showme_clicked
        Show Me button clicked
    '''

    showme_clicked = QtCore.Signal()
    clear_click_signal = QtCore.Signal()
    refresh_click_signal = QtCore.Signal()

    def __init__(self,parent=None):
        QWidget.__init__(self,parent)
        self._tools = []

        showme_button = QPushButton('Show Me')
        showme_button.clicked.connect(self.showme_clicked)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_clicked)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_click_signal)

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
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.addWidget(showme_button)
        main_layout.addWidget(clear_button)
        main_layout.addWidget(self.filter_textbox)
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(refresh_button)
        self.setLayout(main_layout)

    def add_tagtools(self,tagtools):
        for t in tagtools:
            self._tools.append(t)
            self.tool_layout.addWidget(t)

            assert t.parent() != None, 'tagtool has no parent'

    def remove_tagtools(self):
        while True:
            try:
                tool = self._tools.pop()
                tool.setParent(None)
            except IndexError:
                break


    @QtCore.pyqtSlot(str)
    def filter_changed(self,filter_text):
        for tool in self._tools:
            if filter_text.lower() in tool.name.lower():
                tool.show()
            else:
                tool.hide()

    @QtCore.pyqtSlot()
    def clear_clicked(self):
        if DEBUG:
            print("ToolPanel::clear_clicked")

        for tool in self._tools:
            try:
                tool.reset()
            except Exception as e:
                sys.stderr.write(e)

        if DEBUG:
            print("Emit clear clicked")
        self.clear_click_signal.emit()
        


class TagTool(QWidget):
    '''
    A Widget that contain buttons to add tags to trends

    Signals:
    --------
    add_remove_plot : QtCore.Signal(str,bool)
        Signal to add/remove a plot from a plot window.
    '''

    add_remove_plot = QtCore.Signal(str,bool)

    def __init__(self,name):
        '''
        Constructing a tool also adds it to its parent ToolPanel's layout

        Parameters:
        -----------
        name : str
            tagname
        parent_toollist : ToolPanel
            Qt parent, this tool is also added to the toollist's layout

        '''
        QWidget.__init__(self)

        self.name = name
        self.plot_button = QPushButton(name)
        self.plot_button.setCheckable(True)
        self.plot_button.toggled.connect(self.plot_clicked)

        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(self.plot_button,1)

        self.setLayout(layout)


    @QtCore.pyqtSlot(bool)
    def plot_clicked(self,is_clicked):
        self.add_remove_plot.emit(self.name,is_clicked)

    def reset(self):
        self.blockSignals(True)
        self.plot_button.setChecked(False)
        self.blockSignals(False)

def add_grouping_rule(expr,color=None,sub=r'\1'):
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

def remove_grouping_rules(index=None):
    '''
    Remove grouping rules.
    Note: Rules are only applied when the dataframe is set, you need to set the
    dataframe again for this change to apply.

    Parameters:
    -----------
    index : int, optional
        Index of rule to remove. If None, clear all the grouping rules.

    '''
    global _isInit

    if _isInit:
        print("Warning: changing the grouping rules will not have an effect",
              "until you call set_dataframe() again.")
    if index == None:
        TagInfo.taginfo_rules.clear()
    else:
        TagInfo.taginfo_rules.pop(index)

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
        if rule.color == None:
            col = 'None'
        else:
            col = rule.color
        print("{:<3} {:<60} {:^10} {}"\
            .format(i, rule.expr, col, sub )
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
    global tool_panel
    global plot_window
    global plot_manager

    if _isInit:
        tool_panel.remove_tagtools()

    plot_manager.set_dataframe(df)
    tool_panel.add_tagtools( plot_manager.get_tagtools() )

    _isInit = True


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

def set_exec_on_show(on=True):
    '''
    Set whether Qt app .exec function should be called on show().  When
    proc_plot is used in a jupyter notebook with %matplotlib qt magic then the
    gui loop is already running and starting it again will break the app.
    proc_plot tries to figure it out automatically but you can override the
    setting with this function.

    Parameters:
    -----------
    on : bool, optional
        set to False to disable runnnig app.exec.

    '''
    global _execApp
    _execApp = on

_isInit = False # has the window been initialised with a dataframe?
_execApp = True # if started with qt, gui loop is running

if DEBUG:
    print("Backend: ", plt.get_backend())

if (plt.get_backend().lower() == 'qt5agg' and
    plt.isinteractive() ):
    # looks like you are running a jupyter notebook with %matplotlib qt
    _execApp = False
    print("It looks like you are running a jupyter notebook with " \
         +"%matplotlib qt magic.\nThe gui loop is disabled, if you " \
         +"want to enable it, use proc_plot.set_exec_on_show()")

app = QtCore.QCoreApplication.instance()
if app is None:
    app = QApplication([])
    if DEBUG:
        print("app was None")

interactive = plt.isinteractive()
if interactive:
    plt.ioff()

main_window = QWidget()
plot_manager = PlotManager(main_window)
tool_panel = ToolPanel(main_window)

tool_panel.showme_clicked.connect(plot_manager.showme)
tool_panel.clear_click_signal.connect(plot_manager.clear_all_plots)
tool_panel.refresh_click_signal.connect(plot_manager.refresh)

layout = QHBoxLayout()
layout.addWidget(tool_panel,0)
layout.addWidget(plot_manager.plot_window,1)
main_window.setLayout(layout)
#del layout


if interactive:
    plt.ion()
