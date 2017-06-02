from gui.guibase import GUIBase
from qtpy import QtWidgets
from qtpy import QtCore
from qtpy import uic
import pyqtgraph as pg
from gui.colordefs import QudiPalettePale as palette
import numpy as np
import os

class ScopeWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'scope_gui.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class ScopeGUI(GUIBase):
    '''
    This is a simple oscilloscope gui
    '''
    _modclass = 'scopegui'
    _modtype = 'gui'

    ## declare connectors
    _connectors = {'scopelogic': 'ScopeLogic'}

    sigStart = QtCore.Signal()
    sigStop = QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.info('The following configuration was found.')

        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key, config[key]))

    def on_activate(self):
        """ Definition and initialisation of the GUI plus staring the measurement.

        """
        self._scope_logic = self.get_connector('scopelogic')

        self._mw = ScopeWindow()

        self._mw.run_pushButton.clicked.connect(self._scope_logic.run_continuous)
        self._mw.stop_pushButton.clicked.connect(self._scope_logic.stop_aq)
        self._mw.getdata_pushButton.clicked.connect(self._scope_logic.get_data)

        self._mw.Channel1_radioButton.clicked.connect(self.channel1_state_chage)
        self._mw.Channel2_radioButton.clicked.connect(self.channel2_state_chage)
        self._mw.Channel3_radioButton.clicked.connect(self.channel3_state_chage)
        self._mw.Channel4_radioButton.clicked.connect(self.channel4_state_chage)

        # Plot labels.
        self._pw = self._mw.scope_PlotWidget

        self._pw.setLabel('left', 'Voltage', units='V')
        self._pw.setLabel('bottom', 'Time', units='s')

        self.curves = []
        self.colors = [palette.c1, palette.c5, palette.c6, palette.c4]
        for i, ch in enumerate(self._scope_logic.get_channels()):
                # Create an empty plot curve to be filled later, set its pen
                self.curves.append(
                    pg.PlotDataItem(pen=pg.mkPen(self.colors[i]), symbol=None))
                self._pw.addItem(self.curves[-1])


        # setting the x axis length correctly
        self._pw.setXRange(
            0,
            self._scope_logic.get_timescale()[-1]
        )

        self._scope_logic.sigDataUpdated.connect(self.updateData)

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def updateData(self):
        """ The function that grabs the data and sends it to the plot.
        """

        #if self._scope_logic.getState() == 'locked':

        t_vals = self._scope_logic.get_timescale()

        for i, ch in enumerate(self._scope_logic.get_channels()):
             print(t_vals)
             self.curves[i].setData(y=self._scope_logic.scopedata[i], x=t_vals)

        return 0

    def channel1_state_chage(self):
        if self._mw.Channel1_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=1, state='on')
        else:
            self._scope_logic.change_channel_state(channel=1, state='off')

    def channel2_state_chage(self):
        if self._mw.Channel2_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=2, state='on')
        else:
            self._scope_logic.change_channel_state(channel=2, state='off')

    def channel3_state_chage(self):
        if self._mw.Channel3_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=3, state='on')
        else:
            self._scope_logic.change_channel_state(channel=3, state='off')

    def channel4_state_chage(self):
        if self._mw.Channel4_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=4, state='on')
        else:
            self._scope_logic.change_channel_state(channel=4, state='off')



