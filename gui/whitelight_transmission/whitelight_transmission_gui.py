import numpy as np
import os
import pyqtgraph as pg

from core.module import Connector
from core.util import units
from gui.guibase import GUIBase
from gui.guiutils import ColorBar
from gui.colordefs import ColorScaleInferno
from gui.colordefs import QudiPalettePale as palette
from qtpy import QtCore
from qtpy import QtWidgets
from qtpy import uic


class WLTMainWindow(QtWidgets.QMainWindow):
    """ The main window for the ODMR measurement GUI.
    """
    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'whitelight_transmission.ui')

        # Load it
        super(WLTMainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()



class WLTGui(GUIBase):
    """
    This is the GUI Class for WLT measurements
    """

    _modclass = 'WLTGui'
    _modtype = 'gui'

    # declare connectors
    cavitylogic = Connector(interface='CavityLogic')
    savelogic = Connector(interface='SaveLogic')

    sigStartWLTScan = QtCore.Signal(float, float, float)
    sigStopWLTScan = QtCore.Signal()
    sigContinueWLTScan = QtCore.Signal()
    sigClearData = QtCore.Signal()
    sigSpectrometerParamsChanged = QtCore.Signal(float, float)
    # sigSaveMeasurement = QtCore.Signal(str, list, list)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Definition, configuration and initialisation of the ODMR GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        """

        # setting up main window
        self._mw = WLTMainWindow()

        # connect to cavity logic
        self._wlt_logic = self.get_connector('cavitylogic')

        constraints_dict = self._wlt_logic.get_hw_constraints()

        # Create a QSettings object for the mainwindow and store the actual GUI layout
        self.mwsettings = QtCore.QSettings("QUDI", "WLT")
        self.mwsettings.setValue("geometry", self._mw.saveGeometry())
        self.mwsettings.setValue("windowState", self._mw.saveState())

        # Adjust range of scientific spinboxes above what is possible in Qt Designer
        self._mw.start_position_doubleSpinBox.setRange(constraints_dict['min_position']*1e6,
                                                       constraints_dict['max_position']*1e6)
        self._mw.stop_position_doubleSpinBox.setRange(constraints_dict['min_position']*1e6,
                                                      constraints_dict['max_position']*1e6)
        self._mw.scan_speed_doubleSpinBox.setRange(constraints_dict['min_speed'], constraints_dict['max_speed'])
        self._mw.set_temperature_doubleSpinBox.setRange(constraints_dict['min_temperature'],
                                                        constraints_dict['max_temperature'])
        self._mw.get_temperature_doubleSpinBox.setRange(constraints_dict['min_temperature'],
                                                        constraints_dict['max_temperature'])
        self._mw.averages_doubleSpinBox.setRange(constraints_dict['min_number_accumulations'],
                                                 constraints_dict['max_number_accumulations'])
        self._mw.exposure_time_doubleSpinBox.setRange(constraints_dict['min_exposure'],
                                                      constraints_dict['max_exposure'])


        # Get the image from the logic
        self.WLT_image = pg.ImageItem(self._wlt_logic.WLT_image, axisOrder='row-major')
        #self.odmr_matrix_image.setRect(QtCore.QRectF(
        #        self._odmr_logic.mw_start,
        #        0,
        #        self._odmr_logic.mw_stop - self._odmr_logic.mw_start,
        #        self._odmr_logic.number_of_lines
        #    ))

        self.spectrum_image = pg.PlotDataItem(self._wlt_logic.wl,
                                          self._wlt_logic.counts,
                                          pen=pg.mkPen(palette.c1, style=QtCore.Qt.DotLine),
                                          symbol='o',
                                          symbolPen=palette.c1,
                                          symbolBrush=palette.c1,
                                          symbolSize=7)#

        self.pzt_image = pg.PlotDataItem(self._wlt_logic.position_time,
                                          self._wlt_logic.position_data,
                                          pen=pg.mkPen(palette.c1, style=QtCore.Qt.DotLine),
                                          symbol='o',
                                          symbolPen=palette.c1,
                                          symbolBrush=palette.c1,
                                          symbolSize=7)#

        # Add the display item to the xy and xz ViewWidget, which was defined in the UI file.
        self._mw.transmission_map_PlotWidget.addItem(self.WLT_image)
        self._mw.transmission_map_PlotWidget.setLabel(axis='bottom', text='Time', units='s')
        self._mw.transmission_map_PlotWidget.setLabel(axis='left', text='Wavelength', units='m')


        self._mw.spectrum_PlotWidget.addItem(self.spectrum_image)
        self._mw.spectrum_PlotWidget.setLabel(axis='left', text='Counts', units='Counts/s')
        self._mw.spectrum_PlotWidget.setLabel(axis='bottom', text='Wavelength', units='m')
        self._mw.spectrum_PlotWidget.showGrid(x=True, y=True, alpha=0.8)

        self._mw.pzt_PlotWidget.addItem(self.pzt_image)
        self._mw.pzt_PlotWidget.setLabel(axis='left', text='Voltage', units='V')
        self._mw.pzt_PlotWidget.setLabel(axis='bottom', text='time', units='s')
        self._mw.pzt_PlotWidget.showGrid(x=True, y=True, alpha=0.8)


        # Get the colorscales at set LUT
        my_colors = ColorScaleInferno()
        self.WLT_image.setLookupTable(my_colors.lut)

        ########################################################################
        #                  Configuration of the Colorbar                       #
        ########################################################################
        self.transmission_map_cb = ColorBar(my_colors.cmap_normed, 100, 0, 100000)

        # adding colorbar to ViewWidget
        self._mw.transmission_map_cb_PlotWidget.addItem(self.transmission_map_cb)
        self._mw.transmission_map_cb_PlotWidget.hideAxis('bottom')
        self._mw.transmission_map_cb_PlotWidget.hideAxis('left')
        self._mw.transmission_map_cb_PlotWidget.setLabel('right', 'Counts', units='counts/s')

        ########################################################################
        #                       Connect signals                                #
        ########################################################################
        # Internal user input changed signals
        self._mw.start_position_doubleSpinBox.editingFinished.connect(self.changed_pos_params)
        self._mw.stop_position_doubleSpinBox.editingFinished.connect(self.changed_pos_params)
        self._mw.scan_speed_doubleSpinBox.editingFinished.connect(self.changed_pos_params)
        self._mw.number_of_steps_doubleSpinBox.editingFinished.connect(self.changed_pos_params)

        self._mw.averages_doubleSpinBox.editingFinished.connect(self.changed_spectrometer_params)
        self._mw.exposure_time_doubleSpinBox.editingFinished.connect(self.changed_exposure)
        self._mw.cycle_time_doubleSpinBox.editingFinished.connect(self.changed_cycletime)

        # Internal trigger signals
        self._mw.transmission_map_cb_manual_RadioButton.clicked.connect(self.colorscale_changed)
        self._mw.start_pushButton.clicked.connect(self.run_wlt)
        self._mw.stop_pushButton.clicked.connect(self.stop_wlt)
        self._mw.continue_pushButton.clicked.connect(self.continue_wlt)
        self._mw.set_temperature_pushButton.clicked.connect(self.set_temperature)

        self._mw.transmission_map_cb_manual_RadioButton.clicked.connect(self.refresh_WLT_image)
        self._mw.transmission_map_cb_centiles_RadioButton.clicked.connect(self.refresh_WLT_image)
        self._mw.normalize_checkBox.clicked.connect(self.refresh_WLT_image)

        self._mw.transmission_map_cb_min_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_manual)
        self._mw.transmission_map_cb_max_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_manual)
        self._mw.transmission_map_cb_low_percentile_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_centiles)
        self._mw.transmission_map_cb_high_percentile_DoubleSpinBox.valueChanged.connect(self.shortcut_to_xy_cb_centiles)

        # Control/values-changed signals to logic
        self.sigStartWLTScan.connect(self._wlt_logic.start_wlt_measurement)
        self.sigStopWLTScan.connect(self._wlt_logic.stop_wlt_measurement)
        self.sigContinueWLTScan.connect(self._wlt_logic.continue_wlt_measurement,
                                         )
        self._mw.get_temperature_pushButton.clicked.connect(self._wlt_logic.get_temperature)
        self._mw.take_spectrum_pushButton.clicked.connect(self._wlt_logic.take_single_spectrum)

        # Update signals coming from logic:
        self._wlt_logic.sigParameterUpdated.connect(self.update_parameter )
        self._wlt_logic.sigSpectrumPlotUpdated.connect(self.refresh_spectrum_graph)
        self._wlt_logic.sigWLTimageUpdated.connect(self.refresh_WLT_image)
        self._wlt_logic.sigPztimageUpdated.connect(self.refresh_pzt_plot)

        # Ramp
        self._mw.ramp_frequency_DoubleSpinBox.setMaximum(50)
        self._mw.ramp_frequency_DoubleSpinBox.setMinimum(0)
        #self._mw.ramp_frequency_DoubleSpinBox.setOpts(minStep=0.5)  # set the minimal step to 0.5Hz
        self._mw.ramp_offset_DoubleSpinBox.setMaximum(5)
        self._mw.ramp_offset_DoubleSpinBox.setMinimum(0)
        self._mw.ramp_amplitude_DoubleSpinBox.setMinimum(0)
        self._mw.ramp_amplitude_DoubleSpinBox.setMaximum(5)

        self._mw.StartRamp_PushButton.clicked.connect(self.start_ramp)
        self._mw.StopRamp_PushButton.clicked.connect(self.stop_ramp)

        # Show the Main ODMR GUI:
        self.show()
        # Update parameters
        self._wlt_logic.get_temperature()
        self.adjust_xy_window()

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def show(self):
        """Make window visible and put it above all other windows. """
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()

    def restore_defaultview(self):
        self._mw.restoreGeometry(self.mwsettings.value("geometry", ""))
        self._mw.restoreState(self.mwsettings.value("windowState", ""))

    def colorscale_changed(self):
        """
        Updates the range of the displayed colorscale in both the colorbar and the matrix plot.
        """
        cb_range = self.get_matrix_cb_range()
        self.update_colorbar(cb_range)
        self.WLT_image.setImage(image=self.WLT_image.image.transpose(), levels=(cb_range[0], cb_range[1]))
        return

    def update_colorbar(self, cb_range):
        """
        Update the colorbar to a new range.

        @param list cb_range: List or tuple containing the min and max values for the cb range
        """

        self.transmission_map_cb.refresh_colorbar(cb_range[0], cb_range[1])
        return

    def get_matrix_cb_range(self, data=None):
        """
        Determines the cb_min and cb_max values for the matrix plot
        """
        if data is None:
            matrix_image = self.WLT_image.image
        else:
            matrix_image = data
        # If "Manual" is checked or the image is empty (all zeros), then take manual cb range.
        # Otherwise, calculate cb range from percentiles.
        if self._mw.transmission_map_cb_manual_RadioButton.isChecked() or np.max(matrix_image) < 0.1:
            cb_min = self._mw.transmission_map_cb_min_DoubleSpinBox.value()
            cb_max = self._mw.transmission_map_cb_max_DoubleSpinBox.value()
        else:
            # Exclude any zeros (which are typically due to unfinished scan)
            matrix_image_nonzero = matrix_image[np.nonzero(matrix_image)]

            # Read centile range
            low_centile = self._mw.transmission_map_cb_low_percentile_DoubleSpinBox.value()
            high_centile = self._mw.transmission_map_cb_high_percentile_DoubleSpinBox.value()

            cb_min = np.percentile(matrix_image_nonzero, low_centile)
            cb_max = np.percentile(matrix_image_nonzero, high_centile)

        cb_range = [cb_min, cb_max]
        return cb_range

    def changed_spectrometer_params(self):
        self._wlt_logic.set_number_accumulations(self._mw.averages_doubleSpinBox.value())

    def changed_exposure(self):
        self._wlt_logic.set_exposure_time(self._mw.exposure_time_doubleSpinBox.value())

    def changed_cycletime(self):
        self._wlt_logic.set_cycle_time(self._mw.cycle_time_doubleSpinBox.value())


    def changed_pos_params(self):
        pos_start = self._mw.start_position_doubleSpinBox.value()*1e-6
        pos_stop = self._mw.stop_position_doubleSpinBox.value()*1e-6
        number_of_steps = self._mw.number_of_steps_doubleSpinBox.value()
        freq = 1/self._mw.scan_speed_doubleSpinBox.value()
        self._wlt_logic.set_positions_parameters(pos_start=pos_start, pos_stop=pos_stop,
                                                 number_of_steps=number_of_steps, frequency=freq)

    def run_wlt(self):
        """ Starts the WLT"""
        self.sigStartWLTScan.emit(self._mw.scan_speed_doubleSpinBox.value(),
                                  self._mw.start_position_doubleSpinBox.value()*1e-6,
                                  self._mw.stop_position_doubleSpinBox.value()*1e-6)

    def stop_wlt(self):
        """ Stops the WLT"""
        self.sigStopWLTScan.emit()

    def continue_wlt(self):
        """ Continues the WLT measurement"""
        self.sigContinueWLTScan.emit()

    def update_parameter(self, temperature, exposure_time, number_accumulations, cycle_time):
        """
        Updates the paremeters from the spectrometer
        
        :return: 
        """
        self._mw.get_temperature_doubleSpinBox.setValue(temperature)
        self._mw.exposure_time_doubleSpinBox.setValue(exposure_time)
        self._mw.averages_doubleSpinBox.setValue(number_accumulations)
        self._mw.cycle_time_doubleSpinBox.setValue(cycle_time)

    def set_temperature(self):
        """
        
        :return: 
        """
        self._wlt_logic.set_temperature(self._mw.set_temperature_doubleSpinBox.value())

    def refresh_pzt_plot(self):
        self.pzt_image.setData(x=self._wlt_logic.position_time, y=self._wlt_logic.position_data)

    def refresh_spectrum_graph(self, wavelengths, counts):
        self.spectrum_image.setData(x=wavelengths, y=counts)

    def refresh_WLT_image(self):
        """ Update the current XY image from the logic.

        Everytime the scanner is scanning a line in xy the
        image is rebuild and updated in the GUI.
        """
        self.WLT_image.getViewBox().updateAutoRange()

        if self._mw.normalize_checkBox.isChecked():
            WLT_image_data = (self._wlt_logic.WLT_image.transpose() / self._wlt_logic.WLT_image.max(axis=1)).transpose()
        else:
            WLT_image_data = self._wlt_logic.WLT_image

        cb_range = self.get_matrix_cb_range(WLT_image_data)

        # Now update image with new color scale, and update colorbar
        self.WLT_image.setImage(image=WLT_image_data.transpose(), levels=(cb_range[0], cb_range[1]))
        self.update_colorbar(cb_range=cb_range)
        self.adjust_xy_window()

    def shortcut_to_xy_cb_manual(self):
        """Someone edited the absolute counts range for the xy colour bar, better update."""
        self._mw.transmission_map_cb_manual_RadioButton.setChecked(True)
        self.refresh_WLT_image()

    def shortcut_to_xy_cb_centiles(self):
        """Someone edited the centiles range for the xy colour bar, better update."""
        self._mw.transmission_map_cb_centiles_RadioButton.setChecked(True)
        self.refresh_WLT_image()

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

        yMin = self._wlt_logic.wl[0]
        yMax = self._wlt_logic.wl[-1]
        xMin = self._wlt_logic.time_start
        xMax = self._wlt_logic.time_stop


        #xy_viewbox.setLimits(xMin=xMin - (xMax - xMin) * 0.01,
        #                         xMax=xMax + (xMax - xMin) * 0.01,
        #                         yMin=yMin - (yMax - yMin) * 0.01,
        #                         yMax=yMax + (yMax - yMin) * 0.01)

        self.WLT_image.setRect(QtCore.QRectF(xMin, yMin, xMax - xMin, yMax - yMin))

        #xy_viewbox.updateAutoRange()
        #xy_viewbox.updateViewRange()

    def start_ramp(self):
        """

        @return:
        """

        amplitude = self._mw.ramp_amplitude_DoubleSpinBox.value()
        offset = self._mw.ramp_offset_DoubleSpinBox.value()
        freq = self._mw.ramp_frequency_DoubleSpinBox.value()

        self._wlt_logic.start_ramp(amplitude, offset, freq)

        # Disable changes to parameters
        self._mw.ramp_amplitude_DoubleSpinBox.setEnabled(False)
        self._mw.ramp_offset_DoubleSpinBox.setEnabled(False)
        self._mw.ramp_frequency_DoubleSpinBox.setEnabled(False)
        self._mw.start_pushButton.setEnabled(False)


    def stop_ramp(self):
        self._wlt_logic.stop_ramp()

        # Enable changes to parameters
        self._mw.ramp_amplitude_DoubleSpinBox.setEnabled(True)
        self._mw.ramp_offset_DoubleSpinBox.setEnabled(True)
        self._mw.ramp_frequency_DoubleSpinBox.setEnabled(True)
        self._mw.start_pushButton.setEnabled(True)



