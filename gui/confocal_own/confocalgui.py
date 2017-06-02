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

class CrossROI(pg.ROI):

    """ Create a Region of interest, which is a zoomable rectangular.

    @param float pos: optional parameter to set the position
    @param float size: optional parameter to set the size of the roi

    Have a look at:
    http://www.pyqtgraph.org/documentation/graphicsItems/roi.html
    """
    sigUserRegionUpdate = QtCore.Signal(object)
    sigMachineRegionUpdate = QtCore.Signal(object)

    def __init__(self, pos, size, **args):
        """Create a ROI with a central handle."""
        self.userDrag = False
        pg.ROI.__init__(self, pos, size, **args)
        # That is a relative position of the small box inside the region of
        # interest, where 0 is the lowest value and 1 is the higherst:
        center = [0.5, 0.5]
        # Translate the center to the intersection point of the crosshair.
        self.addTranslateHandle(center)

        self.sigRegionChangeStarted.connect(self.startUserDrag)
        self.sigRegionChangeFinished.connect(self.stopUserDrag)
        self.sigRegionChanged.connect(self.regionUpdateInfo)

    def setPos(self, pos, update=True, finish=False):
        """Sets the position of the ROI.

        @param bool update: whether to update the display for this call of setPos
        @param bool finish: whether to emit sigRegionChangeFinished

        Changed finish from parent class implementation to not disrupt user dragging detection.
        """
        super().setPos(pos, update=update, finish=finish)

    def setSize(self,size, update=True,finish=True):
        """
        Sets the size of the ROI
        @param bool update: whether to update the display for this call of setPos
        @param bool finish: whether to emit sigRegionChangeFinished
        """
        super().setSize(size,update=update,finish=finish)

    def handleMoveStarted(self):
        """ Handles should always be moved by user."""
        super().handleMoveStarted()
        self.userDrag = True

    def startUserDrag(self, roi):
        """ROI has started being dragged by user."""
        self.userDrag = True

    def stopUserDrag(self, roi):
        """ROI has stopped being dragged by user"""
        self.userDrag = False

    def regionUpdateInfo(self, roi):
        """When the region is being dragged by the user, emit the corresponding signal."""
        if self.userDrag:
            self.sigUserRegionUpdate.emit(roi)
        else:
            self.sigMachineRegionUpdate.emit(roi)


class CrossLine(pg.InfiniteLine):

    """ Construct one line for the Crosshair in the plot.

    @param float pos: optional parameter to set the position
    @param float angle: optional parameter to set the angle of the line
    @param dict pen: Configure the pen.

    For additional options consider the documentation of pyqtgraph.InfiniteLine
    """

    def __init__(self, **args):
        pg.InfiniteLine.__init__(self, **args)
#        self.setPen(QtGui.QPen(QtGui.QColor(255, 0, 255),0.5))

    def adjust(self, extroi):
        """
        Run this function to adjust the position of the Crosshair-Line

        @param object extroi: external roi object from pyqtgraph
        """
        if self.angle == 0:
            self.setValue(extroi.pos()[1] + extroi.size()[1] * 0.5)
        if self.angle == 90:
            self.setValue(extroi.pos()[0] + extroi.size()[0] * 0.5)


class ConfocalMainWindow(QtWidgets.QMainWindow):

    """ Create the Mainwindow based on the corresponding *.ui file. """

    sigPressKeyBoard = QtCore.Signal(QtCore.QEvent)

    def __init__(self, **kwargs):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'attocubePositionerGUI.ui')

        # Load it
        super().__init__(**kwargs)
        uic.loadUi(ui_file, self)
        self.show()

    def keyPressEvent(self, event):
        """Pass the keyboard press event from the main window further. """
        self.sigPressKeyBoard.emit(event)


class ConfocalSettingDialog(QtWidgets.QDialog):

    """ Create the SettingsDialog window, based on the corresponding *.ui file."""

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_cf_settings.ui')

        # Load it
        super(ConfocalSettingDialog, self).__init__()
        uic.loadUi(ui_file, self)


class OptimizerSettingDialog(QtWidgets.QDialog):
    """ User configurable settings for the optimizer embedded in cofocal gui"""

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_optim_settings.ui')

        # Load it
        super(OptimizerSettingDialog, self).__init__()
        uic.loadUi(ui_file, self)


class ConfocalGui(GUIBase):

    """ Main Confocal Class for xy and depth scans.
    """
    _modclass = 'ConfocalGui'
    _modtype = 'gui'

    # declare connectors
    _connectors = {'confocallogic1': 'ConfocalLogic',
           'savelogic': 'SaveLogic',
           'optimizerlogic1': 'OptimizerLogic'
           }

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
        self._scanning_logic = self.get_connector('confocallogic1')
        self._save_logic = self.get_connector('savelogic')
        self._optimizer_logic = self.get_connector('optimizerlogic1')

        self._mw = ConfocalMainWindow()

        # All our gui elements are dockable, and so there should be no "central" widget.
        # always use first channel on startup, can be changed afterwards
        self.xy_channel = 1

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

        ini_pos_x_crosshair = (self._scanning_logic.xy_image[-1,-1,1] + self._scanning_logic.xy_image[0,0,1]) / 2
        ini_pos_y_crosshair = (self._scanning_logic.xy_image[-1,-1,0] + self._scanning_logic.xy_image[0,0,0]) / 2

        self.pixel_size = (self._scanning_logic.xy_image[1,1,0] - self._scanning_logic.xy_image[0,0,0])/2
        # Create Region of Interest for xy image and add to xy Image Widget:
        self.roi_xy = CrossROI(
            [
                ini_pos_y_crosshair - self.pixel_size / 2,
                ini_pos_x_crosshair - self.pixel_size / 2
            ],
            [self.pixel_size, self.pixel_size],
            pen={'color': "F0F", 'width': 1},
            removable=True
        )

        self._mw.xyScanView.addItem(self.roi_xy)
        # create horizontal and vertical line as a crosshair in xy image:
        self.hline_xy = CrossLine(pos=ini_pos_x_crosshair,
                                  angle=0, pen={'color': palette.green, 'width': 1})
        self.vline_xy = CrossLine(pos=ini_pos_y_crosshair,
                                  angle=90, pen={'color': palette.green, 'width': 1})



        # add the configured crosshair to the xy Widget
        self._mw.xyScanView.addItem(self.hline_xy)
        self._mw.xyScanView.addItem(self.vline_xy)

        # connect the change of a region with the adjustment of the crosshair:
        self.roi_xy.sigRegionChanged.connect(self.hline_xy.adjust)
        self.roi_xy.sigRegionChanged.connect(self.vline_xy.adjust)
        self.roi_xy.sigUserRegionUpdate.connect(self.update_from_roi_xy)
        self.roi_xy.sigRegionChangeFinished.connect(self.roi_xy_bounds_check)
        # set up scan line plot
        #sc = self._scanning_logic._scan_counter
        #sc = sc - 1 if sc >= 1 else sc
        #data = self._scanning_logic.xy_image[sc, :, 0:4:3]

        #self.scan_line_plot = pg.PlotDataItem(data, pen=pg.mkPen(palette.c1))
        #self._mw.xyScanView.addItem(self.scan_line_plot)

        self.fixed_aspect_ratio_xy = True
        # Label the axes:
        self._mw.xyScanView.setLabel('bottom', 'X position', units='m')
        self._mw.xyScanView.setLabel('left', 'Y position', units='m')

        self.my_colors = ColorScaleViridis()
        self.xy_cb = ColorBar(self.my_colors.cmap_normed, width=100, cb_min=0, cb_max=100)
        self.xy_image_orientation = np.array([0, 1, 2, -1], int)
        self.xy_image.setLookupTable(self.my_colors.lut)


        self._mw.contrastView.addItem(self.xy_cb)
        self._mw.contrastView.hideAxis('bottom')
        self._mw.contrastView.setLabel('left', 'Fluorescence', units='c/s')
        self._mw.contrastView.setMouseEnabled(x=False, y=False)

        self.slider_small_step = 1e-6  # initial value in meter
        self.slider_big_step = 10e-6  # initial value in meter

        # Setup the Sliders:
        # Calculate the needed Range for the sliders. The image ranges comming
        # from the Logic module must be in meters.
        # 1 nanometer resolution per one change, units are meters
        self.slider_res = 1e-6

        # How many points are needed for that kind of resolution:
        num_of_points_x = (self._scanning_logic.x_range[1] - self._scanning_logic.x_range[0]) / self.slider_res
        num_of_points_y = (self._scanning_logic.y_range[1] - self._scanning_logic.y_range[0]) / self.slider_res
        num_of_points_z = (self._scanning_logic.z_range[1] - self._scanning_logic.z_range[0]) / self.slider_res

        # Set a Range for the sliders:
        self._mw.x_SliderWidget.setRange(0, num_of_points_x)
        self._mw.y_SliderWidget.setRange(0, num_of_points_y)
        self._mw.z_SliderWidget.setRange(0, num_of_points_z)

        # Just to be sure, set also the possible maximal values for the spin
        # boxes of the current values:
        self._mw.x_current_InputWidget.setRange(self._scanning_logic.x_range[0], self._scanning_logic.x_range[1])
        self._mw.y_current_InputWidget.setRange(self._scanning_logic.y_range[0], self._scanning_logic.y_range[1])
        self._mw.z_current_InputWidget.setRange(self._scanning_logic.z_range[0], self._scanning_logic.z_range[1])

        # set minimal steps for the current value
        self._mw.x_current_InputWidget.setOpts(minStep=1e-6)
        self._mw.y_current_InputWidget.setOpts(minStep=1e-6)
        self._mw.z_current_InputWidget.setOpts(minStep=1e-6)

        # Predefine the maximal and minimal image range as the default values
        # for the display of the range:
        self._mw.x_min_InputWidget.setValue(self._scanning_logic.image_x_range[0])
        self._mw.x_max_InputWidget.setValue(self._scanning_logic.image_x_range[1])
        self._mw.y_min_InputWidget.setValue(self._scanning_logic.image_y_range[0])
        self._mw.y_max_InputWidget.setValue(self._scanning_logic.image_y_range[1])
        self._mw.z_min_InputWidget.setValue(self._scanning_logic.image_z_range[0])
        self._mw.z_max_InputWidget.setValue(self._scanning_logic.image_z_range[1])


        # set the maximal ranges for the imagerange from the logic:
        self._mw.x_min_InputWidget.setRange(self._scanning_logic.x_range[0], self._scanning_logic.x_range[1])
        self._mw.x_max_InputWidget.setRange(self._scanning_logic.x_range[0], self._scanning_logic.x_range[1])
        self._mw.y_min_InputWidget.setRange(self._scanning_logic.y_range[0], self._scanning_logic.y_range[1])
        self._mw.y_max_InputWidget.setRange(self._scanning_logic.y_range[0], self._scanning_logic.y_range[1])
        self._mw.z_min_InputWidget.setRange(self._scanning_logic.z_range[0], self._scanning_logic.z_range[1])
        self._mw.z_max_InputWidget.setRange(self._scanning_logic.z_range[0], self._scanning_logic.z_range[1])

        # set the minimal step size
        self._mw.x_min_InputWidget.setOpts(minStep=1e-6)
        self._mw.x_max_InputWidget.setOpts(minStep=1e-6)
        self._mw.y_min_InputWidget.setOpts(minStep=1e-6)
        self._mw.y_max_InputWidget.setOpts(minStep=1e-6)
        self._mw.z_min_InputWidget.setOpts(minStep=1e-6)
        self._mw.z_max_InputWidget.setOpts(minStep=1e-6)

        # Handle slider movements by user:
        self._mw.x_SliderWidget.sliderMoved.connect(self.update_from_slider_x)
        self._mw.y_SliderWidget.sliderMoved.connect(self.update_from_slider_y)
        self._mw.z_SliderWidget.sliderMoved.connect(self.update_from_slider_z)

        # Take the default values from logic:
        self._mw.xy_res_InputWidget.setValue(self._scanning_logic.xy_resolution)

        # Update the inputed/displayed numbers if the cursor has left the field:
        self._mw.x_current_InputWidget.editingFinished.connect(self.update_from_input_x)
        self._mw.y_current_InputWidget.editingFinished.connect(self.update_from_input_y)
        self._mw.z_current_InputWidget.editingFinished.connect(self.update_from_input_z)

        self._mw.x_min_InputWidget.editingFinished.connect(self.change_x_image_range)
        self._mw.x_max_InputWidget.editingFinished.connect(self.change_x_image_range)
        self._mw.y_min_InputWidget.editingFinished.connect(self.change_y_image_range)
        self._mw.y_max_InputWidget.editingFinished.connect(self.change_y_image_range)
        self._mw.z_min_InputWidget.editingFinished.connect(self.change_z_image_range)
        self._mw.z_max_InputWidget.editingFinished.connect(self.change_z_image_range)

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


        self._mw.xy_res_InputWidget.editingFinished.connect(self.change_xy_resolution)
        self._mw.integrationtime.editingFinished.connect(self.set_integration_time)

        # Connect the buttons and inputs for the xy colorbar
        self._mw.manualRadioButton.clicked.connect(self.update_xy_cb_range)
        self._mw.peercentiesRadioButton.clicked.connect(self.update_xy_cb_range)

        self._mw.counterMinDoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_manual)
        self._mw.counterMaxDoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_manual)
        self._mw.percentileMinDoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_centiles)
        self._mw.percentileMaxDoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_centiles)

        self._mw.startScanPushButton.clicked.connect(self.xy_scan_clicked)
        self._mw.startScanPushButton_2.clicked.connect(self.fine_scan_clicked)
        self._mw.KillScanPushButton.clicked.connect(self.kill_scan_clicked)
        self._mw.KillScanPushButton_2.clicked.connect(self.kill_scan_clicked)

        # Connect the emitted signal of an image change from the logic with
        # a refresh of the GUI picture:
        self._scanning_logic.signal_xy_image_updated.connect(self.refresh_xy_image)
        self._scanning_logic.signal_position_changed.connect(self.update_position)
        self._scanning_logic.signal_change_position.connect(self.update_crosshair_position_from_logic)
        #self._scanning_logic.signal_xy_image_updated.connect(self.refresh_scan_line)
        self._scanning_logic.sigImageXYInitialized.connect(self.adjust_xy_window)

        self._mw.xAmplitudeDoubleSpinBox.setValue(self.get_xAxisAmplitude())
        self._mw.yAmplitudeDoubleSpinBox.setValue(self.get_yAxisAmplitude())
        self._mw.zAmplitudeDoubleSpinBox.setValue(self.get_zAxisAmplitude())
        self._mw.xFrequencyDoubleSpinBox.setValue(self.get_xAxisFrequency())
        self._mw.yFrequencyDoubleSpinBox.setValue(self.get_yAxisFrequency())
        self._mw.zFrequencyDoubleSpinBox.setValue(self.get_zAxisFrequency())

        self._mw.getposition_pushButton.clicked.connect(self.update_position)
        self._mw.setposition_pushButton.clicked.connect(self.set_position)

        self._mw.integrationtime.setValue(self.get_integration_time())

        self.update_position()
        self.adjust_xy_window()
        self._mw.savexy_pushButton.clicked.connect(self.save_xy)

        ##############################################################################################################
        ######### Fine scanner #######################################################################################
        ##############################################################################################################

        arr02 = self._scanning_logic.fine_image[:, :, 3 + self.xy_channel].transpose()
        self.fine_image = pg.ImageItem(arr02)

        # Add the display item to the xy fine VieWidget, which was defined in
        # the UI file.
        self._mw.xyScanView_2.addItem(self.fine_image)
        self.fine_image.setLookupTable(self.my_colors.lut)

        self.fine_cb = ColorBar(self.my_colors.cmap_normed, width=100, cb_min=0, cb_max=100)
        self._mw.contrastView_2.addItem(self.fine_cb)

        # Labelling axes
        self._mw.xyScanView_2.setLabel('bottom', 'X Voltage', units='V')
        self._mw.xyScanView_2.setLabel('left', 'Y Voltage', units='V')

        self._mw.contrastView_2.setLabel('left', 'Fluorescence', units='c/s')

        ini_pos_x_cross = (self._scanning_logic.fine_image[-1,-1,1] + self._scanning_logic.fine_image[0,0,1]) / 2
        ini_pos_y_cross = (self._scanning_logic.fine_image[-1,-1,0] + self._scanning_logic.fine_image[0,0,0]) / 2

        self.pixel_fine_size = (self._scanning_logic.fine_image[1,1,0] - self._scanning_logic.fine_image[0,0,0])/2

        # Create Region of Interest for depth image and add to xy Image Widget:
        self.roi_fine = CrossROI(
            [
                ini_pos_x_cross - self.pixel_fine_size / 2,
                ini_pos_y_cross - self.pixel_fine_size / 2
            ],
            [self.pixel_fine_size, self.pixel_fine_size],
            pen={'color': "F0F", 'width': 1},
            removable=True
        )
        self._mw.xyScanView_2.addItem(self.roi_fine)

        # create horizontal and vertical line as a crosshair in depth image:
        self.hline_fine = CrossLine(
            pos=self.roi_fine.pos() + self.roi_fine.size() * 0.5,
            angle=0,
            pen={'color': palette.green, 'width': 1}
        )
        self.vline_fine = CrossLine(
            pos=self.roi_fine.pos() + self.roi_fine.size() * 0.5,
            angle=90,
            pen={'color': palette.green, 'width': 1}
        )
        # connect the change of a region with the adjustment of the crosshair:
        self.roi_fine.sigRegionChanged.connect(self.hline_fine.adjust)
        self.roi_fine.sigRegionChanged.connect(self.vline_fine.adjust)
        self.roi_fine.sigUserRegionUpdate.connect(self.update_from_roi_fine)
        self.roi_fine.sigRegionChangeFinished.connect(self.roi_fine_bounds_check)

        # add the configured crosshair to the depth Widget:
        self._mw.xyScanView_2.addItem(self.hline_fine)
        self._mw.xyScanView_2.addItem(self.vline_fine)

        self.slider_small_step_fine = 1e-3  # initial value in meter
        self.slider_big_step_fine = 10e-3  # initial value in meter

        # Setup the Sliders:
        # Calculate the needed Range for the sliders. The image ranges comming
        # from the Logic module must be in meters.
        # 1 nanometer resolution per one change, units are meters
        self.slider_res_fine = 1e-6

        # How many points are needed for that kind of resolution:
        num_of_points_x = (self._scanning_logic.xV_range[1] - self._scanning_logic.xV_range[0]) / self.slider_res_fine
        num_of_points_y = (self._scanning_logic.yV_range[1] - self._scanning_logic.yV_range[0]) / self.slider_res_fine

        # Set a Range for the sliders:
        self._mw.x_SliderWidget_2.setRange(0, num_of_points_x)
        self._mw.y_SliderWidget_2.setRange(0, num_of_points_y)

        # Just to be sure, set also the possible maximal values for the spin
        # boxes of the current values:
        self._mw.x_current_InputWidget_2.setRange(self._scanning_logic.xV_range[0], self._scanning_logic.xV_range[1])
        self._mw.y_current_InputWidget_2.setRange(self._scanning_logic.yV_range[0], self._scanning_logic.yV_range[1])

        # set minimal steps for the current value
        self._mw.x_current_InputWidget_2.setOpts(minStep=1e-3)
        self._mw.y_current_InputWidget_2.setOpts(minStep=1e-3)

        # Predefine the maximal and minimal image range as the default values
        # for the display of the range:
        self._mw.x_min_InputWidget_2.setValue(self._scanning_logic.fine_image_x_range[0])
        self._mw.x_max_InputWidget_2.setValue(self._scanning_logic.fine_image_x_range[1])
        self._mw.y_min_InputWidget_2.setValue(self._scanning_logic.fine_image_y_range[0])
        self._mw.y_max_InputWidget_2.setValue(self._scanning_logic.fine_image_y_range[1])


        # set the maximal ranges for the imagerange from the logic:
        self._mw.x_min_InputWidget_2.setRange(self._scanning_logic.xV_range[0], self._scanning_logic.xV_range[1])
        self._mw.x_max_InputWidget_2.setRange(self._scanning_logic.xV_range[0], self._scanning_logic.xV_range[1])
        self._mw.y_min_InputWidget_2.setRange(self._scanning_logic.yV_range[0], self._scanning_logic.yV_range[1])
        self._mw.y_max_InputWidget_2.setRange(self._scanning_logic.yV_range[0], self._scanning_logic.yV_range[1])


        # set the minimal step size
        self._mw.x_min_InputWidget_2.setOpts(minStep=1e-3)
        self._mw.x_max_InputWidget_2.setOpts(minStep=1e-3)
        self._mw.y_min_InputWidget_2.setOpts(minStep=1e-3)
        self._mw.y_max_InputWidget_2.setOpts(minStep=1e-3)

        # Handle slider movements by user:
        self._mw.x_SliderWidget_2.sliderMoved.connect(self.update_from_fineslider_x)
        self._mw.y_SliderWidget_2.sliderMoved.connect(self.update_from_fineslider_y)

        # Take the default values from logic:
        self._mw.x_res_InputWidget_2.setValue(self._scanning_logic.x_fine_resolution)
        self._mw.y_res_InputWidget_2.setValue(self._scanning_logic.y_fine_resolution)

        # Update the inputed/displayed numbers if the cursor has left the field:
        self._mw.x_current_InputWidget_2.editingFinished.connect(self.update_from_input_x_fine)
        self._mw.y_current_InputWidget_2.editingFinished.connect(self.update_from_input_y_fine)

        self._mw.x_res_InputWidget_2.editingFinished.connect(self.change_x_fine_resolution)
        self._mw.y_res_InputWidget_2.editingFinished.connect(self.change_y_fine_resolution)

        self._mw.x_min_InputWidget_2.editingFinished.connect(self.change_x_fine_image_range)
        self._mw.x_max_InputWidget_2.editingFinished.connect(self.change_x_fine_image_range)
        self._mw.y_min_InputWidget_2.editingFinished.connect(self.change_y_fine_image_range)
        self._mw.y_max_InputWidget_2.editingFinished.connect(self.change_y_fine_image_range)

        # Connect the buttons and inputs for the depth colorbars
        # RadioButtons in Main tab
        self._mw.manual_RadioButton_2.clicked.connect(self.update_fine_cb_range)
        self._mw.centiles_RadioButton_2.clicked.connect(self.update_fine_cb_range)

        # input edits in Main tab
        self._mw.xy_cb_min_DoubleSpinBox_2.valueChanged.connect(self.shortcut_to_fine_cb_manual)
        self._mw.xy_cb_max_DoubleSpinBox_2.valueChanged.connect(self.shortcut_to_fine_cb_manual)
        self._mw.xy_cb_low_percentile_DoubleSpinBox_2.valueChanged.connect(self.shortcut_to_fine_cb_centiles)
        self._mw.xy_cb_high_percentile_DoubleSpinBox_2.valueChanged.connect(self.shortcut_to_fine_cb_centiles)

        self._scanning_logic.signal_xy_fine_image_updated.connect(self.refresh_fine_image)
        self._scanning_logic.sigImageXYfineInitialized.connect(self.adjust_fine_window)

        self._scanning_logic.signal_change_position.connect(self.update_crosshair_position_from_logic)

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


    def get_xAxisFrequency(self):
        return self._scanning_logic.get_frequency(axis='x')

    def get_yAxisFrequency(self):
        return self._scanning_logic.get_frequency(axis='y')

    def get_zAxisFrequency(self):
        return self._scanning_logic.get_frequency(axis='z')

    def get_xAxisAmplitude(self):
        return self._scanning_logic.get_amplitude(axis='x')

    def get_yAxisAmplitude(self):
        return self._scanning_logic.get_amplitude(axis='y')

    def get_zAxisAmplitude(self):
        return self._scanning_logic.get_amplitude(axis='z')

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

    def xy_scan_clicked(self):
        """ Manages what happens if the xy scan is started. """
        #self.disable_scan_actions()

        [x, y, z] = self._scanning_logic.get_position()
        self.startpositions = [x, y, z]

        self.startresolution = self._mw.xy_res_InputWidget.value()
        self.startintegrationtime = self._mw.integrationtime.value()
        self.startrange = self._mw.xy_res_InputWidget.value()


        self._scanning_logic.start_scanning(zscan=False,tag='gui')

    def kill_scan_clicked(self):
        """ Manages what happens if the xy scan is killed. """
        #self.disable_scan_actions()
        if self._scanning_logic.getState() == 'locked':
            self._scanning_logic.stop_scanning()

    def refresh_xy_image(self):
        """ Update the current XY image from the logic.

        Everytime the scanner is scanning a line in xy the
        image is rebuild and updated in the GUI.
        """
        self.xy_image.getViewBox().updateAutoRange()

        xy_image_data = np.rot90(
            self._scanning_logic.xy_image[:, :, 3 + self.xy_channel].transpose(),
            self.xy_image_orientation[0])

        cb_range = self.get_xy_cb_range()

        # Now update image with new color scale, and update colorbar
        self.xy_image.setImage(image=xy_image_data, levels=(cb_range[0], cb_range[1]))
        self.refresh_xy_colorbar()

        # Unlock state widget if scan is finished
        #if self._scanning_logic.getState() != 'locked':
        #    self.enable_scan_actions()

    def get_xy_cb_range(self):
        """ Determines the cb_min and cb_max values for the xy scan image
        """
        # If "Manual" is checked, or the image data is empty (all zeros), then take manual cb range.
        if self._mw.manualRadioButton.isChecked() or np.max(self.xy_image.image) == 0.0:
            cb_min = self._mw.counterMinDoubleSpinBox.value()
            cb_max = self._mw.counterMaxDoubleSpinBox.value()

        # Otherwise, calculate cb range from percentiles.
        else:
            # Exclude any zeros (which are typically due to unfinished scan)
            xy_image_nonzero = self.xy_image.image[np.nonzero(self.xy_image.image)]

            # Read centile range
            low_centile = self._mw.percentileMinDoubleSpinBox.value()
            high_centile = self._mw.percentileMaxDoubleSpinBox.value()

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

    def refresh_scan_line(self):
        """ Get the previously scanned image line and display it in the scan line plot. """
        sc = self._scanning_logic._scan_counter
        sc = sc - 1 if sc >= 1 else sc
        self.scan_line_plot.setData(self._scanning_logic.xy_image[sc, :, 0:4:3])
    
    def change_xy_resolution(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._scanning_logic.xy_resolution = self._mw.xy_res_InputWidget.value()

    def change_image_range(self):
        """ Adjust the image range for x in the logic. """
        self._scanning_logic.image_x_range = [0, self._mw.image_range_InputWidget.value()]
        self._scanning_logic.image_y_range = [0, self._mw.image_range_InputWidget.value()]

    def reset_xy_imagerange(self):
        """ Reset the imagerange if autorange was pressed.

        Take the image range values directly from the scanned image and set
        them as the current image ranges.
        """
        # extract the range directly from the image:
        xMin = self._scanning_logic.xy_image[0, 0, 0]
        yMin = self._scanning_logic.xy_image[0, 0, 1]
        xMax = self._scanning_logic.xy_image[-1, -1, 0]
        yMax = self._scanning_logic.xy_image[-1, -1, 1]

        self._mw.x_min_InputWidget.setValue(xMin)
        self._mw.x_max_InputWidget.setValue(xMax)
        self.change_x_image_range()

        self._mw.y_min_InputWidget.setValue(yMin)
        self._mw.y_max_InputWidget.setValue(yMax)
        self.change_y_image_range()

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

        xy_viewbox.updateAutoRange()
        xy_viewbox.updateViewRange()

    def shortcut_to_xy_cb_manual(self):
        """Someone edited the absolute counts range for the xy colour bar, better update."""
        self._mw.manualRadioButton.setChecked(True)
        self.update_xy_cb_range()

    def shortcut_to_xy_cb_centiles(self):
        """Someone edited the centiles range for the xy colour bar, better update."""
        self._mw.peercentiesRadioButton.setChecked(True)
        self.update_xy_cb_range()

    def update_xy_cb_range(self):
        """Redraw xy colour bar and scan image."""
        self.refresh_xy_colorbar()
        self.refresh_xy_image()

    def get_integration_time(self):
        return self._scanning_logic.get_integration_time()

    def set_integration_time(self):
        self._scanning_logic.set_integration_time(time=self._mw.integrationtime.value())

    def xy_fine(self):
        if self._mw.XY_fine_checkbox.isChecked():
            self._scanning_logic.set_xy_fine_state(True)
        else:
            self._scanning_logic.set_xy_fine_state(False)

    def stepper(self):
        if self._mw.stepscan_checkBox.isChecked():
            self._scanning_logic.set_stepscan(True)
        else:
            self._scanning_logic.set_stepscan(False)

    def update_position(self):
        [x,y,z] = self._scanning_logic.get_position()
        self._mw.xpositionSpinBox.setValue(x*1e6)
        self._mw.ypositionSpinBox.setValue(y*1e6)
        self._mw.zpositionSpinBox.setValue(z*1e6)

    def set_position(self):
        x = self._mw.xpositionSpinBox.value()*1e-6
        y = self._mw.ypositionSpinBox.value()*1e-6
        z = self._mw.zpositionSpinBox.value()*1e-6

        self.update_roi_xy(x,y)
        self.update_slider_x(x)
        self.update_slider_y(y)

        self.update_input_x(x)
        self.update_input_y(y)
        self._scanning_logic.set_position('gui',x, y, z)

    def save_xy(self):

        path = ''
        timestamp = datetime.datetime.now()
        filelabel = self._mw.savelabel.text()
        filename = timestamp.strftime('%Y%m%d-%H%M%S' + '_' + filelabel + '.txt')

        xy_image_data = np.rot90(
            self._scanning_logic.xy_image[:, :, 3 + self.xy_channel].transpose(),
            self.xy_image_orientation[0])

        header1 = 'start position (x,y,z : {} \n'.format(self.startpositions)
        header2 = 'range {} \n'.format(self.startrange)
        header3 = 'resolution {} \n'.format(self.startresolution)
        header4 = 'integration time {} \n'.format(self.startintegrationtime)

        header = header1+header2+header3+header4
        np.savetxt(filename, xy_image_data, header=header)


    def update_from_roi_xy(self, roi):
        """The user manually moved the XY ROI, adjust all other GUI elements accordingly

        @params object roi: PyQtGraph ROI object
        """
        x_pos = roi.pos()[0] + 0.5 * roi.size()[0]
        y_pos = roi.pos()[1] + 0.5 * roi.size()[1]

        if x_pos < self._scanning_logic.x_range[0]:
            x_pos = self._scanning_logic.x_range[0]
        elif x_pos > self._scanning_logic.x_range[1]:
            x_pos = self._scanning_logic.x_range[1]

        if y_pos < self._scanning_logic.y_range[0]:
            y_pos = self._scanning_logic.y_range[0]
        elif y_pos > self._scanning_logic.y_range[1]:
            y_pos = self._scanning_logic.y_range[1]

        #self.update_roi_depth(x=x_pos)

        self.update_slider_x(x_pos)
        self.update_slider_y(y_pos)

        self.update_input_x(x_pos)
        self.update_input_y(y_pos)

        self._scanning_logic.set_position('roixy', x=x_pos, y=y_pos)
        #self._optimizer_logic.set_position('roixy', x=x_pos, y=y_pos)

    def roi_xy_bounds_check(self, roi):
        """ Check if the focus cursor is oputside the allowed range after drag
            and set its position to the limit
        """
        x_pos = roi.pos()[0] + 0.5 * roi.size()[0]
        y_pos = roi.pos()[1] + 0.5 * roi.size()[1]

        needs_reset = False

        if x_pos < self._scanning_logic.image_x_range[0]:
            x_pos = self._scanning_logic.image_x_range[0]
            needs_reset = True
        elif x_pos > self._scanning_logic.image_x_range[1]:
            x_pos = self._scanning_logic.image_x_range[1]
            needs_reset = True

        if y_pos < self._scanning_logic.image_y_range[0]:
            y_pos = self._scanning_logic.image_y_range[0]
            needs_reset = True
        elif y_pos > self._scanning_logic.image_y_range[1]:
            y_pos = self._scanning_logic.image_y_range[1]
            needs_reset = True

        if needs_reset:
            self.update_roi_xy(x_pos, y_pos)


    def update_roi_xy(self, x=None, y=None):
        """ Adjust the xy ROI position if the value has changed.

        @param float x: real value of the current x position
        @param float y: real value of the current y position

        Since the origin of the region of interest (ROI) is not the crosshair
        point but the lowest left point of the square, you have to shift the
        origin according to that. Therefore the position of the ROI is not
        the actual position!
        """
        roi_x_view = self.roi_xy.pos()[0]
        roi_y_view = self.roi_xy.pos()[1]

        if x is not None:
            roi_x_view = x - self.roi_xy.size()[0] * 0.5
        if y is not None:
            roi_y_view = y - self.roi_xy.size()[1] * 0.5

        self.roi_xy.setPos([roi_x_view, roi_y_view])

    def update_from_key(self, x=None, y=None, z=None):
        """The user pressed a key to move the crosshair, adjust all GUI elements.

        @param float x: new x position in m
        @param float y: new y position in m
        @param float z: new z position in m
        """
        if x is not None:
            self.update_roi_xy(x=x)
            #self.update_roi_depth(x=x)
            self.update_slider_x(x)
            self.update_input_x(x)
            self._scanning_logic.set_position('xinput', x=x)
        if y is not None:
            self.update_roi_xy(y=y)
            self.update_slider_y(y)
            self.update_input_y(y)
            self._scanning_logic.set_position('yinput', y=y)
        if z is not None:
            #self.update_roi_depth(z=z)
            self.update_slider_z(z)
            self.update_input_z(z)
            self._scanning_logic.set_position('zinput', z=z)

    def update_from_input_x(self):
        """ The user changed the number in the x position spin box, adjust all
            other GUI elements."""
        x_pos = self._mw.x_current_InputWidget.value()
        self.update_roi_xy(x=x_pos)
        #self.update_roi_depth(x=x_pos)
        self.update_slider_x(x_pos)
        self._scanning_logic.set_position('xinput', x=x_pos)
        #self._optimizer_logic.set_position('xinput', x=x_pos)

    def update_from_input_y(self):
        """ The user changed the number in the y position spin box, adjust all
            other GUI elements."""
        y_pos = self._mw.y_current_InputWidget.value()
        self.update_roi_xy(y=y_pos)
        self.update_slider_y(y_pos)
        self._scanning_logic.set_position('yinput', y=y_pos)
        #self._optimizer_logic.set_position('yinput', y=y_pos)

    def update_from_input_z(self):
        """ The user changed the number in the z position spin box, adjust all
           other GUI elements."""
        z_pos = self._mw.z_current_InputWidget.value()
        #self.update_roi_depth(z=z_pos)
        self.update_slider_z(z_pos)
        self._scanning_logic.set_position('zinput', z=z_pos)
        #self._optimizer_logic.set_position('zinput', z=z_pos)

    def update_input_x(self, x_pos):
        """ Update the displayed x-value.

        @param float x_pos: the current value of the x position in m
        """
        # Convert x_pos to number of points for the slider:
        self._mw.x_current_InputWidget.setValue(x_pos)

    def update_input_y(self, y_pos):
        """ Update the displayed y-value.

        @param float y_pos: the current value of the y position in m
        """
        # Convert x_pos to number of points for the slider:
        self._mw.y_current_InputWidget.setValue(y_pos)

    def update_input_z(self, z_pos):
        """ Update the displayed z-value.

        @param float z_pos: the current value of the z position in m
        """
        # Convert x_pos to number of points for the slider:
        self._mw.z_current_InputWidget.setValue(z_pos)

    def update_from_slider_x(self, sliderValue):
        """The user moved the x position slider, adjust the other GUI elements.

        @params int sliderValue: slider postion, a quantized whole number
        """
        x_pos = self._scanning_logic.x_range[0] + sliderValue * self.slider_res
        self.update_roi_xy(x=x_pos)
        #self.update_roi_depth(x=x_pos)
        self.update_input_x(x_pos)
        self._scanning_logic.set_position('xslider', x=x_pos)
       #self._optimizer_logic.set_position('xslider', x=x_pos)

    def update_from_slider_y(self, sliderValue):
        """The user moved the y position slider, adjust the other GUI elements.

        @params int sliderValue: slider postion, a quantized whole number
        """
        y_pos = self._scanning_logic.y_range[0] + sliderValue * self.slider_res
        self.update_roi_xy(y=y_pos)
        self.update_input_y(y_pos)
        self._scanning_logic.set_position('yslider', y=y_pos)
        #self._optimizer_logic.set_position('yslider', y=y_pos)

    def update_from_slider_z(self, sliderValue):
        """The user moved the z position slider, adjust the other GUI elements.

        @params int sliderValue: slider postion, a quantized whole number
        """
        z_pos = self._scanning_logic.z_range[0] + sliderValue * self.slider_res
        #self.update_roi_depth(z=z_pos)
        self.update_input_z(z_pos)
        self._scanning_logic.set_position('zslider', z=z_pos)
        #self._optimizer_logic.set_position('zslider', z=z_pos)

    def update_slider_x(self, x_pos):
        """ Update the x slider when a change happens.

        @param float x_pos: x position in m
        """
        self._mw.x_SliderWidget.setValue((x_pos - self._scanning_logic.x_range[0]) / self.slider_res)

    def update_slider_y(self, y_pos):
        """ Update the y slider when a change happens.

        @param float y_pos: x yosition in m
        """
        self._mw.y_SliderWidget.setValue((y_pos - self._scanning_logic.y_range[0]) / self.slider_res)

    def update_slider_z(self, z_pos):
        """ Update the z slider when a change happens.

        @param float z_pos: z position in m
        """
        self._mw.z_SliderWidget.setValue((z_pos - self._scanning_logic.z_range[0]) / self.slider_res)

    def change_xy_resolution(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._scanning_logic.xy_resolution = self._mw.xy_res_InputWidget.value()

    def change_x_image_range(self):
        """ Adjust the image range for x in the logic. """
        self._scanning_logic.image_x_range = [self._mw.x_min_InputWidget.value(), self._mw.x_max_InputWidget.value()]

    def change_y_image_range(self):
        """ Adjust the image range for y in the logic.
        """
        self._scanning_logic.image_y_range = [self._mw.y_min_InputWidget.value(), self._mw.y_max_InputWidget.value()]

    def change_z_image_range(self):
        """ Adjust the image range for z in the logic. """
        self._scanning_logic.image_z_range = [self._mw.z_min_InputWidget.value(), self._mw.z_max_InputWidget.value()]

    def update_crosshair_position_from_logic(self, tag):
        """ Update the GUI position of the crosshair from the logic.

        @param str tag: tag indicating the source of the update

        Ignore the update when it is tagged with one of the tags that the
        confocal gui emits, as the GUI elements were already adjusted.
        """
        if 'roi' not in tag and 'slider' not in tag and 'key' not in tag and 'input' not in tag and 'gui' not in tag:
            position = self._scanning_logic.get_position()
            x_pos = position[0]
            y_pos = position[1]
            z_pos = position[2]

            roi_x_view = x_pos - self.roi_xy.size()[0] * 0.5
            roi_y_view = y_pos - self.roi_xy.size()[1] * 0.5
            self.roi_xy.setPos([roi_x_view, roi_y_view])

            #roi_x_view = x_pos - self.roi_depth.size()[0] * 0.5
            #roi_y_view = z_pos - self.roi_depth.size()[1] * 0.5
            #self.roi_depth.setPos([roi_x_view, roi_y_view])

            self.update_slider_x(x_pos)
            self.update_slider_y(y_pos)
            self.update_slider_z(z_pos)

            self.update_input_x(x_pos)
            self.update_input_y(y_pos)
            self.update_input_z(z_pos)

    def put_cursor_in_xy_scan(self):
        """Put the xy crosshair back if it is outside of the visible range. """
        view_x_min = self._scanning_logic.image_x_range[0]
        view_x_max = self._scanning_logic.image_x_range[1]
        view_y_min = self._scanning_logic.image_y_range[0]
        view_y_max = self._scanning_logic.image_y_range[1]

        x_value = self.roi_xy.pos()[0]
        y_value = self.roi_xy.pos()[1]
        cross_pos = self.roi_xy.pos() + self.roi_xy.size() * 0.5

        if (view_x_min > cross_pos[0]):
            x_value = view_x_min + self.roi_xy.size()[0]

        if (view_x_max < cross_pos[0]):
            x_value = view_x_max - self.roi_xy.size()[0]

        if (view_y_min > cross_pos[1]):
            y_value = view_y_min + self.roi_xy.size()[1]

        if (view_y_max < cross_pos[1]):
            y_value = view_y_max - self.roi_xy.size()[1]

        self.roi_xy.setPos([x_value, y_value], update=True)

    def roi_fine_bounds_check(self, roi):
        """ Check if the focus cursor is oputside the allowed range after drag
            and set its position to the limit """
        x_pos = roi.pos()[0] + 0.5 * roi.size()[0]
        y_pos = roi.pos()[1] + 0.5 * roi.size()[1]

        needs_reset = False

        if x_pos < self._scanning_logic.xV_range[0]:
            x_pos = self._scanning_logic.xV_range[0]
            needs_reset = True
        elif x_pos > self._scanning_logic.xV_range[1]:
            x_pos = self._scanning_logic.xV_range[1]
            needs_reset = True

        if y_pos < self._scanning_logic.yV_range[0]:
            y_pos = self._scanning_logic.yV_range[0]
            needs_reset = True
        elif y_pos > self._scanning_logic.yV_range[1]:
            y_pos = self._scanning_logic.yV_range[1]
            needs_reset = True

        if needs_reset:
            self.update_roi_fine(x_pos, y_pos)

    def update_from_roi_fine(self, roi):
            """The user manually moved the Z ROI, adjust all other GUI elements accordingly

            @params object roi: PyQtGraph ROI object
            """
            x_pos = roi.pos()[0] + 0.5 * roi.size()[0]
            y_pos = roi.pos()[1] + 0.5 * roi.size()[1]

            if x_pos < self._scanning_logic.xV_range[0]:
                x_pos = self._scanning_logic.xV_range[0]
            elif x_pos > self._scanning_logic.xV_range[1]:
                x_pos = self._scanning_logic.xV_range[1]

            if y_pos < self._scanning_logic.yV_range[0]:
                y_pos = self._scanning_logic.yV_range[0]
            elif y_pos > self._scanning_logic.yV_range[1]:
                y_pos = self._scanning_logic.yV_range[1]

            self.update_fineslider_x(x_pos)
            self.update_fineslider_y(y_pos)
            self.update_input_x_fine(x_pos)
            self.update_input_y_fine(y_pos)

            self._scanning_logic.set_position_fine('roifine', x=x_pos, y=y_pos)

    def update_roi_fine(self, x=None, y=None):
        """ Adjust the xy ROI position if the value has changed.

        @param float x: real value of the current x position
        @param float y: real value of the current y position

        Since the origin of the region of interest (ROI) is not the crosshair
        point but the lowest left point of the square, you have to shift the
        origin according to that. Therefore the position of the ROI is not
        the actual position!
        """
        roi_xfine_view = self.roi_fine.pos()[0]
        roi_yfine_view = self.roi_fine.pos()[1]

        if x is not None:
            roi_xfine_view = x - self.roi_fine.size()[0] * 0.5
        if y is not None:
            roi_yfine_view = y - self.roi_fine.size()[1] * 0.5

        self.roi_fine.setPos([roi_xfine_view, roi_yfine_view])

    def update_from_fineslider_x(self, sliderValue):
        """The user moved the x position slider, adjust the other GUI elements.

        @params int sliderValue: slider postion, a quantized whole number
        """
        x_pos = self._scanning_logic.xV_range[0] + sliderValue * self.slider_res
        self.update_roi_fine(x=x_pos)
        #self.update_roi_depth(x=x_pos)
        self.update_input_x_fine(x_pos)
        self._scanning_logic.set_position_fine('xslider', x=x_pos)
       #self._optimizer_logic.set_position('xslider', x=x_pos)

    def update_from_fineslider_y(self, sliderValue):
        """The user moved the y position slider, adjust the other GUI elements.

        @params int sliderValue: slider postion, a quantized whole number
        """
        y_pos = self._scanning_logic.yV_range[0] + sliderValue * self.slider_res
        self.update_roi_fine(y=y_pos)
        self.update_input_y_fine(y_pos)
        self._scanning_logic.set_position_fine('yslider', y=y_pos)
        #self._optimizer_logic.set_position('yslider', y=y_pos)

    def update_input_x_fine(self, x_pos):
        """ Update the displayed x-value.

        @param float x_pos: the current value of the x position in m
        """
        # Convert x_pos to number of points for the slider:
        self._mw.x_current_InputWidget_2.setValue(x_pos)

    def update_input_y_fine(self, y_pos):
        """ Update the displayed y-value.

        @param float y_pos: the current value of the y position in m
        """
        # Convert x_pos to number of points for the slider:
        self._mw.y_current_InputWidget_2.setValue(y_pos)

    def update_from_input_x_fine(self):
        """ The user changed the number in the x position spin box, adjust all
            other GUI elements."""
        x_pos = self._mw.x_current_InputWidget_2.value()
        self.update_roi_fine(x=x_pos)
        #self.update_roi_depth(x=x_pos)
        self.update_fineslider_x(x_pos)
        self._scanning_logic.set_position_fine('xinput', x=x_pos)
        #self._optimizer_logic.set_position('xinput', x=x_pos)

    def update_from_input_y_fine(self):
        """ The user changed the number in the y position spin box, adjust all
            other GUI elements."""
        y_pos = self._mw.y_current_InputWidget_2.value()
        self.update_roi_fine(y=y_pos)
        self.update_fineslider_y(y_pos)
        self._scanning_logic.set_position_fine('yinput', y=y_pos)
        #self._optimizer_logic.set_position('yinput', y=y_pos)

    def update_fineslider_x(self, x_pos):
        """ Update the x slider when a change happens.

        @param float x_pos: x position in m
        """
        self._mw.x_SliderWidget_2.setValue((x_pos - self._scanning_logic.x_range[0]) / self.slider_res)

    def update_fineslider_y(self, y_pos):
        """ Update the y slider when a change happens.

        @param float y_pos: x yosition in m
        """
        self._mw.y_SliderWidget_2.setValue((y_pos - self._scanning_logic.y_range[0]) / self.slider_res)

    def change_x_fine_resolution(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._scanning_logic.x_fine_resolution = self._mw.x_res_InputWidget_2.value()

    def change_y_fine_resolution(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._scanning_logic.y_fine_resolution = self._mw.y_res_InputWidget_2.value()

    def change_x_fine_image_range(self):
        """ Adjust the image range for x in the logic. """
        self._scanning_logic.fine_image_x_range = [self._mw.x_min_InputWidget_2.value(), self._mw.x_max_InputWidget_2.value()]

    def change_y_fine_image_range(self):
        """ Adjust the image range for y in the logic.
        """
        self._scanning_logic.fine_image_y_range = [self._mw.y_min_InputWidget_2.value(), self._mw.y_max_InputWidget_2.value()]

    def update_fine_cb_range(self):
        """Redraw z colour bar and scan image."""
        self.refresh_fine_colorbar()
        self.refresh_fine_image()

    def refresh_fine_colorbar(self):
        """ Adjust the depth colorbar.

        Calls the refresh method from colorbar, which takes either the lowest
        and higherst value in the image or predefined ranges. Note that you can
        invert the colorbar if the lower border is bigger then the higher one.
        """
        cb_range = self.get_fine_cb_range()
        self.fine_cb.refresh_colorbar(cb_range[0], cb_range[1])

    def get_fine_cb_range(self):
        """ Determines the cb_min and cb_max values for the xy scan image
        """
        # If "Manual" is checked, or the image data is empty (all zeros), then take manual cb range.
        if self._mw.manual_RadioButton_2.isChecked() or np.max(self.fine_image.image) == 0.0:
            cb_min = self._mw.xy_cb_min_DoubleSpinBox_2.value()
            cb_max = self._mw.xy_cb_max_DoubleSpinBox_2.value()

        # Otherwise, calculate cb range from percentiles.
        else:
            # Exclude any zeros (which are typically due to unfinished scan)
            fine_image_nonzero = self.fine_image.image[np.nonzero(self.fine_image.image)]

            # Read centile range
            low_centile = self._mw.xy_cb_low_percentile_DoubleSpinBox_2.value()
            high_centile = self._mw.xy_cb_high_percentile_DoubleSpinBox_2.value()

            cb_min = np.percentile(fine_image_nonzero, low_centile)
            cb_max = np.percentile(fine_image_nonzero, high_centile)

        cb_range = [cb_min, cb_max]
        return cb_range

    def refresh_fine_image(self):
        """ Update the current Depth image from the logic.

        Everytime the scanner is scanning a line in depth the
        image is rebuild and updated in the GUI.
        """

        self.fine_image.getViewBox().enableAutoRange()

        fine_image_data = self._scanning_logic.fine_image[:, :, 3 + self.xy_channel].transpose()
        cb_range = self.get_fine_cb_range()

        # Now update image with new color scale, and update colorbar
        self.fine_image.setImage(image=fine_image_data, levels=(cb_range[0], cb_range[1]))
        self.refresh_fine_colorbar()

        # Unlock state widget if scan is finished
        # if self._scanning_logic.getState() != 'locked':
        #     self.enable_scan_actions()

    def shortcut_to_fine_cb_manual(self):
        """Someone edited the absolute counts range for the z colour bar, better update."""
        # Change cb mode
        self._mw.manual_RadioButton_2.setChecked(True)
        self.update_fine_cb_range()

    def shortcut_to_fine_cb_centiles(self):
        """Someone edited the centiles range for the z colour bar, better update."""
        # Change cb mode
        self._mw.centiles_RadioButton_2.setChecked(True)
        self.update_fine_cb_range()

    def adjust_fine_window(self):
        """ Fit the visible window in the depth scan to full view.

        Be careful in using that method, since it uses the input values for
        the ranges to adjust x and z. Make sure that in the process of the depth scan
        no method is calling adjust_xy_window, otherwise it will adjust for you
        a window which does not correspond to the scan!
        """
        # It is extremly crutial that before adjusting the window view and
        # limits, to make an update of the current image. Otherwise the
        # adjustment will just be made for the previous image.
        self.refresh_fine_image()

        fine_viewbox = self.fine_image.getViewBox()

        xMin = self._scanning_logic.fine_image_x_range[0]
        xMax = self._scanning_logic.fine_image_x_range[1]
        zMin = self._scanning_logic.fine_image_y_range[0]
        zMax = self._scanning_logic.fine_image_y_range[1]

        self.fixed_aspect_ratio_fine = True
        if self.fixed_aspect_ratio_fine:
            # Reset the limit settings so that the method 'setAspectLocked'
            # works properly. It has to be done in a manual way since no method
            # exists yet to reset the set limits:
            fine_viewbox.state['limits']['xLimits'] = [None, None]
            fine_viewbox.state['limits']['yLimits'] = [None, None]
            fine_viewbox.state['limits']['xRange'] = [None, None]
            fine_viewbox.state['limits']['yRange'] = [None, None]

            fine_viewbox.setAspectLocked(lock=True, ratio=1.0)
            fine_viewbox.updateViewRange()
        # else:
        #     fine_viewbox.setLimits(
        #         xMin=xMin - xMin * self.image_x_padding,
        #         xMax=xMax + xMax * self.image_x_padding,
        #         yMin=zMin - zMin * self.image_z_padding,
        #         yMax=zMax + zMax * self.image_z_padding
        #     )

        self.fine_image.setRect(QtCore.QRectF(xMin, zMin, xMax - xMin, zMax - zMin))

        self.put_cursor_in_fine_scan()

        fine_viewbox.updateAutoRange()
        fine_viewbox.updateViewRange()

    def put_cursor_in_fine_scan(self):
        """Put the depth crosshair back if it is outside of the visible range. """
        view_x_min = self._scanning_logic.fine_image_x_range[0]
        view_x_max = self._scanning_logic.fine_image_x_range[1]
        view_y_min = self._scanning_logic.fine_image_y_range[0]
        view_y_max = self._scanning_logic.fine_image_y_range[1]

        x_value = self.roi_fine.pos()[0]
        y_value = self.roi_fine.pos()[1]
        cross_pos = self.roi_fine.pos() + self.roi_fine.size() * 0.5

        if (view_x_min > cross_pos[0]):
            x_value = view_x_min + self.roi_fine.size()[0]

        if (view_x_max < cross_pos[0]):
            x_value = view_x_max - self.roi_fine.size()[0]

        if (view_y_min > cross_pos[1]):
            y_value = view_y_min + self.roi_fine.size()[1]

        if (view_y_max < cross_pos[1]):
            y_value = view_y_max - self.roi_fine.size()[1]

        self.roi_fine.setPos([x_value, y_value], update=True)


    def update_finecrosshair_position_from_logic(self, tag):
        """ Update the GUI position of the crosshair from the logic.

        @param str tag: tag indicating the source of the update

        Ignore the update when it is tagged with one of the tags that the
        confocal gui emits, as the GUI elements were already adjusted.
        """
        if 'roi' not in tag and 'slider' not in tag and 'key' not in tag and 'input' not in tag:
            position = self._scanning_logic.get_position_fine()
            x_pos = position[0]
            y_pos = position[1]

            roi_x_view = x_pos - self.roi_fine.size()[0] * 0.5
            roi_y_view = y_pos - self.roi_fine.size()[1] * 0.5
            self.roi_fine.setPos([roi_x_view, roi_y_view])


            self.update_fineslider_x(x_pos)
            self.update_fineslider_y(y_pos)

            self.update_input_x_fine(x_pos)
            self.update_input_y_fine(y_pos)

    def fine_scan_clicked(self):
        """ Manages what happens if the xy scan is started. """
        # self.disable_scan_actions()
        self._scanning_logic.start_scanning(zscan=False,finescan=True,  tag='gui')

    def save_xy_scan_data(self):
        """ Run the save routine from the logic to save the xy confocal data."""
        cb_range = self.get_xy_cb_range()

        # Percentile range is None, unless the percentile scaling is selected in GUI.
        pcile_range = None
        if not self._mw.manualRadioButton.isChecked():
            low_centile = self._mw.percentileMinDoubleSpinBox.value()
            high_centile = self._mw.percentileMaxDoubleSpinBox.value()
            pcile_range = [low_centile, high_centile]

        self._scanning_logic.save_xy_data(colorscale_range=cb_range, percentile_range=pcile_range)

        # TODO: find a way to produce raw image in savelogic.  For now it is saved here.
        filepath = self._save_logic.get_path_for_module(module_name='Confocal')
        filename = filepath + os.sep + time.strftime('%Y%m%d-%H%M-%S_confocal_xy_scan_raw_pixel_image')

        self.xy_image.save(filename + '_raw.png')