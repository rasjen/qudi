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
import datetime
import os

from gui.guibase import GUIBase
from gui.colordefs import QudiPalettePale as palette
from gui.guiutils import ColorBar
from gui.colordefs import ColorScaleViridis, ColorScaleInferno
from core.module import Connector, ConfigOption, StatusVar

class ConfocalMainWindow(QtWidgets.QMainWindow):

    """ Create the Mainwindow based on the corresponding *.ui file. """

    sigPressKeyBoard = QtCore.Signal(QtCore.QEvent)

    def __init__(self, **kwargs):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'confocal_JPE_CPSHR3_nicard_gui.ui')

        # Load it
        super().__init__(**kwargs)
        uic.loadUi(ui_file, self)
        self.show()

    def keyPressEvent(self, event):
        """Pass the keyboard press event from the main window further. """
        self.sigPressKeyBoard.emit(event)



class confocal_JPE_CPSHR3_nicard_gui(GUIBase):

    """ Main Confocal Class for xy and depth scans.
    """
    _modclass = 'confocal_JPE_CPSHR3_nicard_gui'
    _modtype = 'gui'

    # declare connectors
    confocallogic = Connector(interface='confocal_scanner_JPE_CPSHR3_nicard_interface')
    savelogic = Connector(interface='SaveLogic')


    sigStartOptimizer = QtCore.Signal(list, str)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.info('The following configuration was found.')

        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key, config[key]))


    def on_activate(self):
        """ Initializes all needed UI files and establishes the connectors.

        This method executes the all the inits for the differnt GUIs and passes
        the event argument from fysom to the methods.
        """

        # Getting an access to all connectors:
        self._confocal_scan_logic = self.get_connector('confocallogic')
        self._save_logic = self.get_connector('savelogic')

        self._mw = ConfocalMainWindow()



        # Take the default values from logic:
        self.step_size_value = self._mw.step_size_value_double_spinBox.value()*1e-6

        # Connections between GUI and logic fonctions
        self._mw.step_xplus_pushButton.clicked.connect(self.move_x_plus)
        self._mw.step_xminus_pushButton.clicked.connect(self.move_x_minus)
        self._mw.step_yplus_pushButton.clicked.connect(self.move_y_plus)
        self._mw.step_yminus_pushButton.clicked.connect(self.move_y_minus)
        self._mw.step_zplus_pushButton.clicked.connect(self.move_z_plus)
        self._mw.step_zminus_pushButton.clicked.connect(self.move_z_minus)

        self._mw.step_size_value_double_spinBox.valueChanged.connect(self.set_step_value)


    def on_deactivate(self):
        """ Reverse steps of activation

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
    def move_x_plus(self):
        self._confocal_scan_logic._scanner_logic.move_xyz(self.step_size_value, 0, 0)

    def move_x_minus(self):
        self._confocal_scan_logic._scanner_logic.move_xyz(-self.step_size_value, 0, 0)

    def move_y_plus(self):
        self._confocal_scan_logic._scanner_logic.move_xyz(0, self.step_size_value, 0)

    def move_y_minus(self):
        self._confocal_scan_logic._scanner_logic.move_xyz(0, -self.step_size_value, 0)

    def move_z_plus(self):
        self._confocal_scan_logic._scanner_logic.move_xyz(0, 0, self.step_size_value)

    def move_z_minus(self):
        self._confocal_scan_logic._scanner_logic.move_xyz(0, 0, -self.step_size_value)

    def set_step_value(self):
        self.step_size_value = self._mw.step_size_value_double_spinBox.value()*1e-6

