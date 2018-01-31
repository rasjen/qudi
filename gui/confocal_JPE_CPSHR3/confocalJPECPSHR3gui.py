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

import numpy as np
import os
import pyqtgraph as pg
import time

from core.module import Connector, ConfigOption, StatusVar
from gui.guibase import GUIBase
from gui.guiutils import ColorBar
from gui.colordefs import ColorScaleInferno
from gui.colordefs import QudiPalettePale as palette
from gui.fitsettings import FitParametersWidget
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic


class ConfocalMainWindow(QtWidgets.QMainWindow):

    """ Create the Mainwindow based on the corresponding *.ui file. """

    sigPressKeyBoard = QtCore.Signal(QtCore.QEvent)
    sigDoubleClick = QtCore.Signal()

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'confocalJPECPSHR3.ui')
        self._doubleclicked = False

        # Load it
        super(ConfocalMainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()

    def keyPressEvent(self, event):
        """Pass the keyboard press event from the main window further. """
        self.sigPressKeyBoard.emit(event)

    def mouseDoubleClickEvent(self, event):
        self._doubleclicked = True
        self.sigDoubleClick.emit()

class ConfocalGui(GUIBase):

    """ Main Confocal Class for xy and depth scans.
    """
    _modclass = 'ConfocalGui'
    _modtype = 'gui'

    # declare connectors
    confocallogic2 = Connector(interface='EmptyInterface')
    savelogic = Connector(interface='SaveLogic')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def show(self):
        """Make main window visible and put it above all other windows. """
        # Show the Main Confocal GUI:
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()

    def on_activate(self):
        """ Initializes all needed UI files and establishes the connectors.

        This method executes the all the inits for the differnt GUIs and passes
        the event argument from fysom to the methods.
        """

        # Getting an access to all connectors:
        self._scanning_logic = self.get_connector('confocallogic2')
        self._save_logic = self.get_connector('savelogic')

        self.initMainUI()      # initialize the main GUI

    def initMainUI(self):
        """ Definition, configuration and initialisation of the confocal GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        Moreover it sets default values.
        """
        self._mw = ConfocalMainWindow()


        # Get the image for the display from the logic
        self._scanning_logic.data = np.zeros((50, 50), dtype=int)

        # Load the images for xy and depth in the display:
        self.xy_image = pg.ImageItem(image=self._scanning_logic.data, axisOrder='row-major')

        # Add the display item to the xy and depth ViewWidget, which was defined
        # in the UI file:
        self._mw.xy_ViewWidget.addItem(self.xy_image)

        # Disable the CLAs
        self.disable_manual_ClAs_move()

        # Label the axes:
        self._mw.xy_ViewWidget.setLabel('bottom', 'X position', units='m')
        self._mw.xy_ViewWidget.setLabel('left', 'Y position', units='m')

        # Get the colorscale and set the LUTs
        self.my_colors = ColorScaleInferno()

        self.xy_image.setLookupTable(self.my_colors.lut)

        # Create colorbars and add them at the desired place in the GUI. Add
        # also units to the colorbar.

        self.xy_cb = ColorBar(self.my_colors.cmap_normed, width=100, cb_min=0, cb_max=100)
        self.depth_cb = ColorBar(self.my_colors.cmap_normed, width=100, cb_min=0, cb_max=100)
        self._mw.xy_cb_ViewWidget.addItem(self.xy_cb)
        self._mw.xy_cb_ViewWidget.hideAxis('bottom')
        self._mw.xy_cb_ViewWidget.setLabel('left', 'Fluorescence', units='c/s')
        self._mw.xy_cb_ViewWidget.setMouseEnabled(x=False, y=False)

        # connection
        self._scanning_logic.signal_xy_image_updated.connect(self.refresh_xy_image)
        self._mw.xy_cb_min_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_manual)
        self._mw.xy_cb_max_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_manual)
        self._mw.xy_cb_low_percentile_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_centiles)
        self._mw.xy_cb_high_percentile_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_centiles)
        self._mw.xy_cb_centiles_RadioButton.clicked.connect(self.update_xy_cb_range)
        self._mw.xy_cb_manual_RadioButton.clicked.connect(self.update_xy_cb_range)
        self._mw.CLAs_movable_checkBox.stateChanged.connect(self.CLAs_movable_checkBox_clicked)

        self._mw.step_xminus_pushButton.clicked.connect(self.step_xminus_pushButton_clicked)
        self._mw.step_xplus_pushButton.clicked.connect(self.step_xplus_pushButton_clicked)
        self._mw.step_yminus_pushButton.clicked.connect(self.step_yminus_pushButton_clicked)
        self._mw.step_yplus_pushButton.clicked.connect(self.step_yplus_pushButton_clicked)
        self._mw.step_zminus_pushButton.clicked.connect(self.step_zminus_pushButton_clicked)
        self._mw.step_zplus_pushButton.clicked.connect(self.step_zplus_pushButton_clicked)

        self._mw.CLA1_step_up_pushButton.clicked.connect(self.CLA1_step_up_pushButton_clicked)
        self._mw.CLA2_step_up_pushButton.clicked.connect(self.CLA2_step_up_pushButton_clicked)
        self._mw.CLA3_step_up_pushButton.clicked.connect(self.CLA3_step_up_pushButton_clicked)
        self._mw.CLA1_step_down_pushButton.clicked.connect(self.CLA1_step_down_pushButton_clicked)
        self._mw.CLA2_step_down_pushButton.clicked.connect(self.CLA2_step_down_pushButton_clicked)
        self._mw.CLA3_step_down_pushButton.clicked.connect(self.CLA3_step_down_pushButton_clicked)

        self._mw.snake_scan_pushButton.clicked.connect(self.snake_scan_pushButton_clicked)
        self._mw.horizontal_scan_pushButton.clicked.connect(self.horizontal_scan_pushButton_clicked)
        self.show()

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

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

        return cb_range

    def refresh_xy_colorbar(self):
        """ Adjust the xy colorbar.

        Calls the refresh method from colorbar, which takes either the lowest
        and higherst value in the image or predefined ranges. Note that you can
        invert the colorbar if the lower border is bigger then the higher one.
        """
        cb_range = self.get_xy_cb_range()
        self.xy_cb.refresh_colorbar(cb_range[0], cb_range[1])

    def xy_scan_clicked(self):
        """ Manages what happens if the xy scan is started. """
        self.disable_scan_actions()
        self._scanning_logic.start_scanning(zscan=False,tag='gui')

    def change_xy_resolution(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        #self._scanning_logic.xy_resolution = self._mw.xy_res_InputWidget.value()
        pass

    def change_x_image_range(self):
        """ Adjust the image range for x in the logic. """
        self._scanning_logic.image_x_range = [
            self._mw.x_min_InputWidget.value(),
            self._mw.x_max_InputWidget.value()]

    def change_y_image_range(self):
        """ Adjust the image range for y in the logic.
        """
        self._scanning_logic.image_y_range = [
            self._mw.y_min_InputWidget.value(),
            self._mw.y_max_InputWidget.value()]

    def update_xy_channel(self, index):
        """ The displayed channel for the XY image was changed, refresh the displayed image.

            @param index int: index of selected channel item in combo box
        """
        self.xy_channel = int(self._mw.xy_channel_ComboBox.itemData(index, QtCore.Qt.UserRole))
        self.refresh_xy_image()

    def update_depth_channel(self, index):
        """ The displayed channel for the X-depth image was changed, refresh the displayed image.

            @param index int: index of selected channel item in combo box
        """
        self.depth_channel = int(self._mw.depth_channel_ComboBox.itemData(index, QtCore.Qt.UserRole))
        self.refresh_depth_image()

    def shortcut_to_xy_cb_manual(self):
        """Someone edited the absolute counts range for the xy colour bar, better update."""
        self._mw.xy_cb_manual_RadioButton.setChecked(True)
        self.update_xy_cb_range()

    def shortcut_to_xy_cb_centiles(self):
        """Someone edited the centiles range for the xy colour bar, better update."""
        self._mw.xy_cb_centiles_RadioButton.setChecked(True)
        self.update_xy_cb_range()

    def update_xy_cb_range(self):
        """Redraw xy colour bar and scan image."""
        self.refresh_xy_colorbar()
        self.refresh_xy_image()

    def refresh_xy_image(self):
        """ Update the current XY image from the logic.

        Everytime the scanner is scanning a line in xy the
        image is rebuild and updated in the GUI.
        """
        self.xy_image.getViewBox().updateAutoRange()

        xy_image_data = self._scanning_logic.data

        cb_range = self.get_xy_cb_range()

        # Now update image with new color scale, and update colorbar
        self.xy_image.setImage(image=xy_image_data, levels=(cb_range[0], cb_range[1]))
        self.refresh_xy_colorbar()

    def adjust_xy_window(self):
        """ Fit the visible window in the xy scan to full view.

        Be careful in using that method, since it uses the input values for
        the ranges to adjust x and y. Make sure that in the process of the depth scan
        no method is calling adjust_depth_window, otherwise it will adjust for you
        a window which does not correspond to the scan!
        """
        # It is extremly crucial that before adjusting the window view and
        # limits, to make an update of the current image. Otherwise the
        # adjustment will just be made for the previous image.
        self.refresh_xy_image()
        xy_viewbox = self.xy_image.getViewBox()

        xMin = self._scanning_logic.image_x_range[0]
        xMax = self._scanning_logic.image_x_range[1]
        yMin = self._scanning_logic.image_y_range[0]
        yMax = self._scanning_logic.image_y_range[1]

        if self.fixed_aspect_ratio_xy:
            # Reset the limit settings so that the method 'setAspectLocked'
            # works properly. It has to be done in a manual way since no method
            # exists yet to reset the set limits:
            xy_viewbox.state['limits']['xLimits'] = [None, None]
            xy_viewbox.state['limits']['yLimits'] = [None, None]
            xy_viewbox.state['limits']['xRange'] = [None, None]
            xy_viewbox.state['limits']['yRange'] = [None, None]

            xy_viewbox.setAspectLocked(lock=True, ratio=1.0)
            xy_viewbox.updateViewRange()
        else:
            xy_viewbox.setLimits(xMin=xMin - (xMax - xMin) * self.image_x_padding,
                                 xMax=xMax + (xMax - xMin) * self.image_x_padding,
                                 yMin=yMin - (yMax - yMin) * self.image_y_padding,
                                 yMax=yMax + (yMax - yMin) * self.image_y_padding)

        self.xy_image.setRect(QtCore.QRectF(xMin, yMin, xMax - xMin, yMax - yMin))

        self.put_cursor_in_xy_scan()

        xy_viewbox.updateAutoRange()
        xy_viewbox.updateViewRange()
        self.update_roi_xy()

    def save_xy_scan_data(self):
        """ Run the save routine from the logic to save the xy confocal data."""
        cb_range = self.get_xy_cb_range()

        # Percentile range is None, unless the percentile scaling is selected in GUI.
        pcile_range = None
        if not self._mw.xy_cb_manual_RadioButton.isChecked():
            low_centile = self._mw.xy_cb_low_percentile_DoubleSpinBox.value()
            high_centile = self._mw.xy_cb_high_percentile_DoubleSpinBox.value()
            pcile_range = [low_centile, high_centile]

        self._scanning_logic.save_xy_data(colorscale_range=cb_range, percentile_range=pcile_range)

        # TODO: find a way to produce raw image in savelogic.  For now it is saved here.
        filepath = self._save_logic.get_path_for_module(module_name='Confocal')
        filename = filepath + os.sep + time.strftime('%Y%m%d-%H%M-%S_confocal_xy_scan_raw_pixel_image')
        if self._sd.save_purePNG_checkBox.isChecked():
            self.xy_image.save(filename + '_raw.png')

    def save_xy_scan_image(self):
        """ Save the image and according to that the data.

        Here only the path to the module is taken from the save logic, but the
        picture save algorithm is situated here in confocal, since it is a very
        specific task to save the used PlotObject.
        """
        self.log.warning('Deprecated, use normal save method instead!')

    def disable_manual_ClAs_move(self):
        self._mw.step_xminus_pushButton.setEnabled(0)
        self._mw.step_yminus_pushButton.setEnabled(0)
        self._mw.step_zminus_pushButton.setEnabled(0)
        self._mw.step_xplus_pushButton.setEnabled(0)
        self._mw.step_yplus_pushButton.setEnabled(0)
        self._mw.step_zplus_pushButton.setEnabled(0)
        self._mw.CLA1_step_up_pushButton.setEnabled(0)
        self._mw.CLA1_step_down_pushButton.setEnabled(0)
        self._mw.CLA2_step_up_pushButton.setEnabled(0)
        self._mw.CLA2_step_down_pushButton.setEnabled(0)
        self._mw.CLA3_step_up_pushButton.setEnabled(0)
        self._mw.CLA3_step_down_pushButton.setEnabled(0)

    def enable_manual_ClAs_move(self):
        self._mw.step_xminus_pushButton.setEnabled(1)
        self._mw.step_yminus_pushButton.setEnabled(1)
        self._mw.step_zminus_pushButton.setEnabled(1)
        self._mw.step_xplus_pushButton.setEnabled(1)
        self._mw.step_yplus_pushButton.setEnabled(1)
        self._mw.step_zplus_pushButton.setEnabled(1)
        self._mw.CLA1_step_up_pushButton.setEnabled(1)
        self._mw.CLA1_step_down_pushButton.setEnabled(1)
        self._mw.CLA2_step_up_pushButton.setEnabled(1)
        self._mw.CLA2_step_down_pushButton.setEnabled(1)
        self._mw.CLA3_step_up_pushButton.setEnabled(1)
        self._mw.CLA3_step_down_pushButton.setEnabled(1)

    def CLAs_movable_checkBox_clicked(self):
        if self._mw.CLAs_movable_checkBox.isChecked() == 0:
            self.disable_manual_ClAs_move()
        else:
            self.enable_manual_ClAs_move()
        return 0

    def step_xminus_pushButton_clicked(self):
        self._scanning_logic.move_scanner_xyz(-self._mw.step_size_value_double_spinBox.value(), 0, 0)
        return 0

    def step_xplus_pushButton_clicked(self):
        self._scanning_logic.move_scanner_xyz(self._mw.step_size_value_double_spinBox.value() ,0, 0)
        return 0

    def step_yminus_pushButton_clicked(self):
        self._scanning_logic.move_scanner_xyz(0, -self._mw.step_size_value_double_spinBox.value(), 0)
        return 0

    def step_yplus_pushButton_clicked(self):
        self._scanning_logic.move_scanner_xyz(0, self._mw.step_size_value_double_spinBox.value(), 0)
        return 0

    def step_zminus_pushButton_clicked(self):
        self._scanning_logic.move_scanner_xyz(0, 0, -self._mw.step_size_value_double_spinBox.value())
        return 0

    def step_zplus_pushButton_clicked(self):
        self._scanning_logic.move_scanner_xyz(0, 0, self._mw.step_size_value_double_spinBox.value())
        return 0

    def CLA1_step_up_pushButton_clicked(self):
        self._scanning_logic.move_CLA1(self._mw.step_size_value_double_spinBox.value())

    def CLA1_step_down_pushButton_clicked(self):
        self._scanning_logic.move_CLA1(-self._mw.step_size_value_double_spinBox.value())

    def CLA2_step_up_pushButton_clicked(self):
        self._scanning_logic.move_CLA2(self._mw.step_size_value_double_spinBox.value())

    def CLA2_step_down_pushButton_clicked(self):
        self._scanning_logic.move_CLA2(-self._mw.step_size_value_double_spinBox.value())

    def CLA3_step_up_pushButton_clicked(self):
        self._scanning_logic.move_CLA3(self._mw.step_size_value_double_spinBox.value())

    def CLA3_step_down_pushButton_clicked(self):
        self._scanning_logic.move_CLA3(-self._mw.step_size_value_double_spinBox.value())

    def snake_scan_pushButton_clicked(self):
        self._mw.CLAs_movable_checkBox.setCheckState(0)
        self._scanning_logic.initialize_scan(self._mw.scan_step_doubleSpinBox.value(), self._mw.scan_range_doubleSpinBox.value())
        self._scanning_logic.snake_scan()

    def horizontal_scan_pushButton_clicked(self):
        self._mw.CLAs_movable_checkBox.setCheckState(0)
        self._scanning_logic.initialize_scan(self._mw.scan_step_doubleSpinBox.value(), self._mw.scan_range_doubleSpinBox.value())
        self._scanning_logic.horizontal_scan()