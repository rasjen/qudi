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

        # Create an instance of ConfocalMainWindow class
        self._mw = ConfocalMainWindow()
        self._mw.setGeometry(1184, 277, 868, 907)
        self._mw.xy_ViewWidget.setGeometry(10, 88, 680, 634)
        self._mw.emergency_stop_pushButton.setStyleSheet("background-color: darkred")
        # Take the default values from logic:
        self.step_size_value = self._mw.step_size_value_double_spinBox.value()*1e-6
        self.CLA_movable = bool(0)
        self._mw.step_xplus_pushButton.setEnabled(0)
        self._mw.step_xminus_pushButton.setEnabled(0)
        self._mw.step_yplus_pushButton.setEnabled(0)
        self._mw.step_yminus_pushButton.setEnabled(0)
        self._mw.step_zplus_pushButton.setEnabled(0)
        self._mw.step_zminus_pushButton.setEnabled(0)

        # Create an empty image and add it to the plot widget
        xy_image_data = np.zeros([50, 50], dtype=int)
        self.xy_image = pg.ImageItem(image=xy_image_data, axisOrder='row-major')

        self._mw.xy_ViewWidget.addItem(self.xy_image)

        self.my_colors = ColorScaleInferno()
        self.xy_cb = ColorBar(self.my_colors.cmap_normed, width=100, cb_min=0, cb_max=100)
        self._mw.xy_cb_ViewWidget.addItem(self.xy_cb)
        self._mw.xy_cb_ViewWidget.hideAxis('bottom')
        self._mw.xy_cb_ViewWidget.setLabel('left', 'Fluorescence', units='c/s')
        self._mw.xy_cb_ViewWidget.setMouseEnabled(x=False, y=False)

        # Connections between GUI and logic fonctions

        self._confocal_scan_logic.signal_xy_image_updated.connect(self.refresh_xy_image)

        self._mw.step_xplus_pushButton.clicked.connect(self.move_x_plus)
        self._mw.step_xminus_pushButton.clicked.connect(self.move_x_minus)
        self._mw.step_yplus_pushButton.clicked.connect(self.move_y_plus)
        self._mw.step_yminus_pushButton.clicked.connect(self.move_y_minus)
        self._mw.step_zplus_pushButton.clicked.connect(self.move_z_plus)
        self._mw.step_zminus_pushButton.clicked.connect(self.move_z_minus)

        self._mw.step_size_value_double_spinBox.valueChanged.connect(self.set_step_value)
        self._mw.CLAs_movable_checkBox.clicked.connect(self.CLAs_movable_checkBox_clicked)
        self._mw.emergency_stop_pushButton.clicked.connect(self.emergency_stop)
        self._mw.start_scan_pushButton.clicked.connect(self.XY_scan)

        self.n = 0

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
            self.step_size_value = self._mw.step_size_value_double_spinBox.value()

    def CLAs_movable_checkBox_clicked(self):
        if self._mw.CLAs_movable_checkBox.isChecked() == False:
            self._mw.step_xplus_pushButton.setEnabled(0)
            self._mw.step_xminus_pushButton.setEnabled(0)
            self._mw.step_yplus_pushButton.setEnabled(0)
            self._mw.step_yminus_pushButton.setEnabled(0)
            self._mw.step_zplus_pushButton.setEnabled(0)
            self._mw.step_zminus_pushButton.setEnabled(0)
        elif self._mw.CLAs_movable_checkBox.isChecked() == True:
            self._mw.step_xplus_pushButton.setEnabled(1)
            self._mw.step_xminus_pushButton.setEnabled(1)
            self._mw.step_yplus_pushButton.setEnabled(1)
            self._mw.step_yminus_pushButton.setEnabled(1)
            self._mw.step_zplus_pushButton.setEnabled(1)
            self._mw.step_zminus_pushButton.setEnabled(1)

    def emergency_stop(self):
        self._confocal_scan_logic._scanner_logic.stop_CLAs()

    def XY_scan(self):
        step = self._mw.scanner_step_size_value_double_spinBox.value()
        square_size = self._mw.scanner_range_size_value_double_spinBox.value()
        self._confocal_scan_logic.snake_scan(step, square_size)

    def refresh_xy_image(self):
        """ Update the current XY image from the logic.

        Everytime the scanner is scanning a line in xy the
        image is rebuild and updated in the GUI.
        """
        self.xy_image.getViewBox().updateAutoRange()

        xy_image_data = self._confocal_scan_logic.data

        cb_range = self.get_xy_cb_range()

        # Now update image with new color scale, and update colorbar
        self.xy_image.setImage(image=xy_image_data, levels=(cb_range[0], cb_range[1]))
        self.refresh_xy_colorbar()

        # Unlock state widget if scan is finished
        if self._confocal_scan_logic.getState() != 'locked':
            self.enable_scan_actions()

    def get_xy_cb_range(self):
        """ Determines the cb_min and cb_max values for the xy scan image
        """
        # If "Manual" is checked, or the image data is empty (all zeros), then take manual cb range.
        if self._mw.xy_cb_manual_RadioButton.isChecked() or np.max(self.xy_image.image) == 0.0:
            cb_min = self._mw.xy_cb_min_DoubleSpinBox.value()
            cb_max = self._mw.xy_cb_max_DoubleSpinBox.value()

        # Otherwise, calculate cb range from percentiles.
        else:
            # Exclude any zeros (which are typically due to unfinished scan)
            xy_image_nonzero = self.xy_image.image[np.nonzero(self.xy_image.image)]
            # Read centile range
            low_centile = self._mw.xy_cb_low_percentile_DoubleSpinBox.value()
            high_centile = self._mw.xy_cb_high_percentile_DoubleSpinBox.value()

            cb_min = np.percentile(xy_image_nonzero, low_centile)
            cb_max = np.percentile(xy_image_nonzero, high_centile)

        cb_range = [cb_min, cb_max]
        print(cb_range)
        return cb_range

    def refresh_xy_colorbar(self):
        """ Adjust the xy colorbar.

        Calls the refresh method from colorbar, which takes either the lowest
        and higherst value in the image or predefined ranges. Note that you can
        invert the colorbar if the lower border is bigger then the higher one.
        """
        cb_range = self.get_xy_cb_range()
        self.xy_cb.refresh_colorbar(cb_range[0], cb_range[1])

    def enable_scan_actions(self):
        """ Reset the scan action buttons to the default active
        state when the system is idle.
        """
        # Disable the stop scanning button

        # Enable the scan buttons
