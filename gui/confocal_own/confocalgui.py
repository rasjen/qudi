# -*- coding: utf-8 -*-

"""
This file contains the Qudi GUI for general Confocal control.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic
import pyqtgraph as pg
import numpy as np
import time
import os

from gui.guibase import GUIBase

class ConfocalMainWindow(QtWidgets.QMainWindow):

    """ Create the Mainwindow based on the corresponding *.ui file. """
        
    def __init__(self, **kwargs):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'attocubePositionerGUI.ui')

        # Load it
        super().__init__(**kwargs)
        uic.loadUi(ui_file, self)
        self.show()

class ConfocalGui(GUIBase):

    """ Main Confocal Class for xy and depth scans.
    """
    _modclass = 'ConfocalGui'
    _modtype = 'gui'

    # declare connectors
    _in = {'confocallogic1': 'ConfocalLogic',
           'savelogic': 'SaveLogic',
           }

    sigStartOptimizer = QtCore.Signal(list, str)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.info('The following configuration was found.')

        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key, config[key]))


    def on_activate(self, e=None):
        """ Initializes all needed UI files and establishes the connectors.

        @param object e: Fysom.event object from Fysom class.
                         An object created by the state machine module Fysom,
                         which is connected to a specific event (have a look in
                         the Base Class). This object contains the passed event,
                         the state before the event happened and the destination
                         of the state which should be reached after the event
                         had happened.

        This method executes the all the inits for the differnt GUIs and passes
        the event argument from fysom to the methods.
        """

        # Getting an access to all connectors:
        self._scanning_logic = self.get_in_connector('confocallogic1')
        self._save_logic = self.get_in_connector('savelogic')
        
        self._mw = ConfocalMainWindow()

        # All our gui elements are dockable, and so there should be no "central" widget.
        # always use first channel on startup, can be changed afterwards
        self.xy_channel = 0

        # Get the image for the display from the logic. Transpose the received
        # matrix to get the proper scan. The graphig widget displays vector-
        # wise the lines and the lines are normally columns, but in our
        # measurement we scan rows per row. That's why it has to be transposed.
        arr01 = self._scanning_logic.xy_image[:, :, 3 + self.xy_channel].transpose()

        # Load the images for xy in the display:
        self.xy_image = pg.ImageItem(arr01)

        # Add the display item to the xy ViewWidget, which was defined
        # in the UI file:
        # To use addItem method, the widget needs to be promoted with
        # pyqtgraph class (can be done in qtDesigner with a rigth click
        # on the widget)
        self._mw.xyScanView.addItem(self.xy_image)

        # Label the axes:
        self._mw.xyScanView.setLabel('bottom', 'X position', units='μm')
        self._mw.xyScanView.setLabel('left', 'Y position', units='μm')

        # Connections between GUI and logic fonctions
        self._mw.stepXBackwardPushButton.clicked.connect(self.stepXBackward)
        self._mw.stepXForwardPushButton.clicked.connect(self.stepXForward)
        self._mw.stepYBackwardPushButton.clicked.connect(self.stepYBackward)
        self._mw.stepYForwardPushButton.clicked.connect(self.stepYForward)
        self._mw.stepZBackwardPushButton.clicked.connect(self.stepZBackward)
        self._mw.stepZForwardPushButton.clicked.connect(self.stepZForward)
        self._mw.xAmplitudeDoubleSpinBox.valueChanged.connect(self.set_xAxisAmplitude)
        self._mw.yAmplitudeDoubleSpinBox.valueChanged.connect(self.set_yAxisAmplitude)
        self._mw.zAmplitudeDoubleSpinBox.valueChanged.connect(self.set_zAxisAmplitude)
        self._mw.xFrequencyDoubleSpinBox.valueChanged.connect(self.set_xAxisFrequency)
        self._mw.yFrequencyDoubleSpinBox.valueChanged.connect(self.set_yAxisFrequency)
        self._mw.zFrequencyDoubleSpinBox.valueChanged.connect(self.set_zAxisFrequency)
        self._mw.xAxisCheckBox.stateChanged.connect(self.xaxis_output_status)
        self._mw.yAxisCheckBox.stateChanged.connect(self.yaxis_output_status)
        self._mw.zAxisCheckBox.stateChanged.connect(self.zaxis_output_status)



    def on_deactivate(self, e):
        """ Reverse steps of activation

        @param object e: Fysom.event object from Fysom class. A more detailed
                         explanation can be found in the method initUI.

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def show(self):
        """Make main window visible and put it above all other windows. """
        # Show the Main Confocal GUI:
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()

    # Fonctions used for connectors
    def stepXBackward(self):
        self._scanning_logic.single_step(axis='x', direction='backward')

    def stepXForward(self):
        self._scanning_logic.single_step(axis='x', direction='forward')

    def stepYBackward(self):
        self._scanning_logic.single_step(axis='y', direction='backward')

    def stepYForward(self):
        self._scanning_logic.single_step(axis='y', direction='forward')

    def stepZBackward(self):
        self._scanning_logic.single_step(axis='z', direction='backward')

    def stepZForward(self):
        self._scanning_logic.single_step(axis='z', direction='forward')

    def set_xAxisFrequency(self):
        self._scanning_logic.set_frequency(axis='x', freq=self._mw.xFrequencyDoubleSpinBox.value())

    def set_yAxisFrequency(self):
        self._scanning_logic.set_frequency(axis='y', freq=self._mw.yFrequencyDoubleSpinBox.value())

    def set_zAxisFrequency(self):
        self._scanning_logic.set_frequency(axis='z', freq=self._mw.zFrequencyDoubleSpinBox.value())

    def set_xAxisAmplitude(self):
        self._scanning_logic.set_amplitude(axis='x', amp=self._mw.xAmplitudeDoubleSpinBox.value())

    def set_yAxisAmplitude(self):
        self._scanning_logic.set_amplitude(axis='y', amp=self._mw.yAmplitudeDoubleSpinBox.value())

    def set_zAxisAmplitude(self):
        self._scanning_logic.set_amplitude(axis='z', amp=self._mw.zAmplitudeDoubleSpinBox.value())

    def xaxis_output_status(self):
        if self._mw.xAxisCheckBox.isChecked():
            self._scanning_logic.axis_output_status(axis='x', status='on')
        else:
            self._scanning_logic.axis_output_status(axis='x', status='off')

    def yaxis_output_status(self):
        if self._mw.yAxisCheckBox.isChecked():
            self._scanning_logic.axis_output_status(axis='y', status='on')
        else:
            self._scanning_logic.axis_output_status(axis='y', status='off')

    def zaxis_output_status(self):
        if self._mw.zAxisCheckBox.isChecked():
            self._scanning_logic.axis_output_status(axis='z', status='on')
        else:
            self._scanning_logic.axis_output_status(axis='z', status='off')