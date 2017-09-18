from gui.guibase import GUIBase
from qtpy import QtWidgets
from qtpy.QtGui import QPixmap
from qtpy import QtCore
from qtpy import uic
import pyqtgraph as pg
from gui.colordefs import QudiPalettePale as palette
import numpy as np
import os
import matplotlib.image as mpimg
import matplotlib.pyplot as plt



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

    def on_deactivate(self):
        """
        Reverse steps of activation
        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def on_activate(self):
        """
        Definition and initialisation of the GUI plus staring the measurement.
        """
        self._scope_logic = self.get_connector('scopelogic')
        self._mw = ScopeWindow()

        ''' Add items into the combo boxes of the GUI'''
        # Time scale comboWidget
        self._mw.time_scale_comboBox.addItem('2E-09')
        self._mw.time_scale_comboBox.addItem('5E-09')
        self._mw.time_scale_comboBox.addItem('1E-06')
        self._mw.time_scale_comboBox.addItem('2E-06')
        self._mw.time_scale_comboBox.addItem('5E-06')
        self._mw.time_scale_comboBox.addItem('1E-03')
        self._mw.time_scale_comboBox.addItem('2E-03')
        self._mw.time_scale_comboBox.addItem('5E-03')
        self._mw.time_scale_comboBox.addItem('1E-02')
        self._mw.time_scale_comboBox.addItem('2E-02')
        self._mw.time_scale_comboBox.addItem('5E-02')
        self._mw.time_scale_comboBox.addItem('1E-01')
        self._mw.time_scale_comboBox.addItem('2E-01')
        self._mw.time_scale_comboBox.addItem('5E-01')
        self._mw.time_scale_comboBox.addItem('1E+00')
        self._mw.time_scale_comboBox.addItem('2E+00')
        self._mw.time_scale_comboBox.addItem('5E+00')
        self._mw.time_scale_comboBox.addItem('1E+01')
        self._mw.time_scale_comboBox.addItem('2E+01')
        self._mw.time_scale_comboBox.addItem('5E+01')
        # Channel 1 vertical scale comboWidget
        self._mw.channel1_vscale_comboBox.addItem('1E-03')
        self._mw.channel1_vscale_comboBox.addItem('2E-03')
        self._mw.channel1_vscale_comboBox.addItem('5E-03')
        self._mw.channel1_vscale_comboBox.addItem('1E-02')
        self._mw.channel1_vscale_comboBox.addItem('2E-02')
        self._mw.channel1_vscale_comboBox.addItem('5E-02')
        self._mw.channel1_vscale_comboBox.addItem('1E-01')
        self._mw.channel1_vscale_comboBox.addItem('2E-01')
        self._mw.channel1_vscale_comboBox.addItem('5E-01')
        self._mw.channel1_vscale_comboBox.addItem('1E+00')
        self._mw.channel1_vscale_comboBox.addItem('2E+00')
        self._mw.channel1_vscale_comboBox.addItem('5E+00')
        # Channel 2 vertical scale comboWidget
        self._mw.channel2_vscale_comboBox.addItem('1E-03')
        self._mw.channel2_vscale_comboBox.addItem('2E-03')
        self._mw.channel2_vscale_comboBox.addItem('5E-03')
        self._mw.channel2_vscale_comboBox.addItem('1E-02')
        self._mw.channel2_vscale_comboBox.addItem('2E-02')
        self._mw.channel2_vscale_comboBox.addItem('5E-02')
        self._mw.channel2_vscale_comboBox.addItem('1E-01')
        self._mw.channel2_vscale_comboBox.addItem('2E-01')
        self._mw.channel2_vscale_comboBox.addItem('5E-01')
        self._mw.channel2_vscale_comboBox.addItem('1E+00')
        self._mw.channel2_vscale_comboBox.addItem('2E+00')
        self._mw.channel2_vscale_comboBox.addItem('5E+00')
        # Channel 3 vertical scale comboWidget
        self._mw.channel3_vscale_comboBox.addItem('1E-03')
        self._mw.channel3_vscale_comboBox.addItem('2E-03')
        self._mw.channel3_vscale_comboBox.addItem('5E-03')
        self._mw.channel3_vscale_comboBox.addItem('1E-02')
        self._mw.channel3_vscale_comboBox.addItem('2E-02')
        self._mw.channel3_vscale_comboBox.addItem('5E-02')
        self._mw.channel3_vscale_comboBox.addItem('1E-01')
        self._mw.channel3_vscale_comboBox.addItem('2E-01')
        self._mw.channel3_vscale_comboBox.addItem('5E-01')
        self._mw.channel3_vscale_comboBox.addItem('1E+00')
        self._mw.channel3_vscale_comboBox.addItem('2E+00')
        self._mw.channel3_vscale_comboBox.addItem('5E+00')
        # Channel 4 vertical scale comboWidget
        self._mw.channel4_vscale_comboBox.addItem('1E-03')
        self._mw.channel4_vscale_comboBox.addItem('2E-03')
        self._mw.channel4_vscale_comboBox.addItem('5E-03')
        self._mw.channel4_vscale_comboBox.addItem('1E-02')
        self._mw.channel4_vscale_comboBox.addItem('2E-02')
        self._mw.channel4_vscale_comboBox.addItem('5E-02')
        self._mw.channel4_vscale_comboBox.addItem('1E-01')
        self._mw.channel4_vscale_comboBox.addItem('2E-01')
        self._mw.channel4_vscale_comboBox.addItem('5E-01')
        self._mw.channel4_vscale_comboBox.addItem('1E+00')
        self._mw.channel4_vscale_comboBox.addItem('2E+00')
        self._mw.channel4_vscale_comboBox.addItem('5E+00')
        # Trigger mode comboWidget
        self._mw.trigger_mode_comboBox.addItem('EDGE')
        self._mw.trigger_mode_comboBox.addItem('GLIT')
        self._mw.trigger_mode_comboBox.addItem('PATT')
        self._mw.trigger_mode_comboBox.addItem('TV')
        self._mw.trigger_mode_comboBox.addItem('DEL')
        self._mw.trigger_mode_comboBox.addItem('EBUR')
        self._mw.trigger_mode_comboBox.addItem('OR')
        self._mw.trigger_mode_comboBox.addItem('RUNT')
        self._mw.trigger_mode_comboBox.addItem('SHOLd')
        self._mw.trigger_mode_comboBox.addItem('TRAN')
        self._mw.trigger_mode_comboBox.addItem('SBUS{1 | 2}')
        self._mw.trigger_mode_comboBox.addItem('USB')
        # Trigger source comboWidget
        self._mw.trigger_source_comboBox.addItem('CHAN1')
        self._mw.trigger_source_comboBox.addItem('CHAN2')
        self._mw.trigger_source_comboBox.addItem('CHAN3')
        self._mw.trigger_source_comboBox.addItem('CHAN4')


        '''Grab the data from the scope and put the corresponding values inside the GUI '''
        # Time
        self._mw.time_delay_doubleSpinBox.setValue(self._scope_logic.get_time_delay())
        self._mw.time_scale_comboBox.setCurrentText(self._scope_logic.get_time_scale())
        # Acquisition mode
        if self._scope_logic.get_acquire_mode() == 'NORM':
            self._mw.aqcuire_mode_normal_radioButton.setChecked(True)
        else:
            self._mw.aqcuire_mode_normal_radioButton.setChecked(False)

        if self._scope_logic.get_acquire_mode() == 'AVER':
            self._mw.aqcuire_mode_average_radioButton.setChecked(True)
        else:
            self._mw.aqcuire_mode_average_radioButton.setChecked(False)

        if self._scope_logic.get_acquire_mode() == 'PEAK':
            self._mw.aqcuire_mode_peak_radioButton.setChecked(True)
        else:
            self._mw.aqcuire_mode_peak_radioButton.setChecked(False)

        if self._scope_logic.get_acquire_mode() == 'HRES':
            self._mw.aqcuire_mode_highres_radioButton.setChecked(True)
        else:
            self._mw.aqcuire_mode_highres_radioButton.setChecked(False)
        # Channels Vscale
        self._mw.channel1_vscale_comboBox.setCurrentText(self._scope_logic.get_channel_vscale(1))
        self._mw.channel2_vscale_comboBox.setCurrentText(self._scope_logic.get_channel_vscale(2))
        self._mw.channel3_vscale_comboBox.setCurrentText(self._scope_logic.get_channel_vscale(3))
        self._mw.channel4_vscale_comboBox.setCurrentText(self._scope_logic.get_channel_vscale(4))
        # Channels couling AC/DC
        if self._scope_logic.get_channel_coupling(1) == 'DC\n':
            self._mw.channel1_DC_radioButton.setChecked(True)
        else:
            self._mw.channel1_AC_radioButton.setChecked(True)

        if self._scope_logic.get_channel_coupling(2) == 'DC\n':
            self._mw.channel2_DC_radioButton.setChecked(True)
        else:
            self._mw.channel2_AC_radioButton.setChecked(True)

        if self._scope_logic.get_channel_coupling(3) == 'DC\n':
            self._mw.channel3_DC_radioButton.setChecked(True)
        else:
            self._mw.channel3_AC_radioButton.setChecked(True)

        if self._scope_logic.get_channel_coupling(4) == 'DC\n':
            self._mw.channel4_DC_radioButton.setChecked(True)
        else:
            self._mw.channel4_AC_radioButton.setChecked(True)

        # Channels display
        if self._scope_logic.get_display_status(1) == '1':
            self._mw.channel1_display_radioButton.setChecked(True)
        else:
            self._mw.channel1_display_radioButton.setChecked(False)

        if self._scope_logic.get_display_status(2) == '1':
            self._mw.channel2_display_radioButton.setChecked(True)
        else:
            self._mw.channel2_display_radioButton.setChecked(False)

        if self._scope_logic.get_display_status(3) == '1':
            self._mw.channel3_display_radioButton.setChecked(True)
        else:
            self._mw.channel3_display_radioButton.setChecked(False)

        if self._scope_logic.get_display_status(4) == '1':
            self._mw.channel4_display_radioButton.setChecked(True)
        else:
            self._mw.channel4_display_radioButton.setChecked(False)

        # Channels input impedance
        if self._scope_logic.get_impedance_input(1) == 'ONEM\n':
            self._mw.channel1_impedance_input_radioButton.setChecked(True)
        else:
            self._mw.channel1_impedance_input_radioButton.setChecked(False)

        if self._scope_logic.get_impedance_input(2) == 'ONEM\n':
            self._mw.channel2_impedance_input_radioButton.setChecked(True)
        else:
            self._mw.channel2_impedance_input_radioButton.setChecked(False)

        if self._scope_logic.get_impedance_input(3) == 'ONEM\n':
            self._mw.channel3_impedance_input_radioButton.setChecked(True)
        else:
            self._mw.channel3_impedance_input_radioButton.setChecked(False)

        if self._scope_logic.get_impedance_input(4) == 'ONEM\n':
            self._mw.channel4_impedance_input_radioButton.setChecked(True)
        else:
            self._mw.channel4_impedance_input_radioButton.setChecked(False)

        # Channels offset
        self._mw.channel1_offset_doubleSpinBox.setValue(self._scope_logic.get_channel_offset(1))
        self._mw.channel2_offset_doubleSpinBox.setValue(self._scope_logic.get_channel_offset(2))
        self._mw.channel3_offset_doubleSpinBox.setValue(self._scope_logic.get_channel_offset(3))
        self._mw.channel4_offset_doubleSpinBox.setValue(self._scope_logic.get_channel_offset(4))

        # Trigger configuration
        self._mw.trigger_mode_comboBox.setCurrentText(self._scope_logic.get_trigger_mode())
        self._mw.trigger_source_comboBox.setCurrentText(self._scope_logic.get_trigger_source())
        self._mw.trigger_level_doubleSpinBox.setValue(self._scope_logic.get_trigger_level())

        '''Connections between buttons of the GUI and functions'''
        self._mw.run_pushButton.clicked.connect(self._scope_logic.run_continuous)
        self._mw.stop_pushButton.clicked.connect(self._scope_logic.stop_acquisition)
        self._mw.singlerun_pushButton.clicked.connect(self._scope_logic.single_acquisition)
        self._mw.autoscale_pushButton.clicked.connect(self._scope_logic.auto_scale)
        self._mw.time_scale_comboBox.currentIndexChanged.connect(self.set_time_scale)
        self._mw.time_delay_doubleSpinBox.valueChanged.connect(self.set_time_delay)
        self._mw.channel1_DC_radioButton.clicked.connect(self._scope_logic.set_channel1_DC_couling)
        self._mw.channel1_AC_radioButton.clicked.connect(self._scope_logic.set_channel1_AC_couling)
        self._mw.channel2_DC_radioButton.clicked.connect(self._scope_logic.set_channel2_DC_couling)
        self._mw.channel2_AC_radioButton.clicked.connect(self._scope_logic.set_channel2_AC_couling)
        self._mw.channel3_DC_radioButton.clicked.connect(self._scope_logic.set_channel3_DC_couling)
        self._mw.channel3_AC_radioButton.clicked.connect(self._scope_logic.set_channel3_AC_couling)
        self._mw.channel4_DC_radioButton.clicked.connect(self._scope_logic.set_channel4_DC_couling)
        self._mw.channel4_AC_radioButton.clicked.connect(self._scope_logic.set_channel4_AC_couling)
        self._mw.trigger_source_comboBox.currentIndexChanged.connect(self.set_trigger_source)
        self._mw.trigger_mode_comboBox.currentIndexChanged.connect(self.set_trigger_mode)
        self._mw.trigger50_pushButton.clicked.connect(self.set_trigger_50)
        self._mw.trigger_level_doubleSpinBox.valueChanged.connect(self.set_trigger_level)
        self._mw.aqcuire_mode_normal_radioButton.clicked.connect(self._scope_logic.set_acquire_mode_normal)
        self._mw.aqcuire_mode_highres_radioButton.clicked.connect(self._scope_logic.set_aqcuire_mode_highres)
        self._mw.aqcuire_mode_average_radioButton.clicked.connect(self._scope_logic.set_aqcuire_mode_average)
        self._mw.aqcuire_mode_peak_radioButton.clicked.connect(self._scope_logic.set_aqcuire_mode_peak)
        self._mw.channel1_vscale_comboBox.currentIndexChanged.connect(self.set_channel1_vscale)
        self._mw.channel2_vscale_comboBox.currentIndexChanged.connect(self.set_channel2_vscale)
        self._mw.channel3_vscale_comboBox.currentIndexChanged.connect(self.set_channel3_vscale)
        self._mw.channel4_vscale_comboBox.currentIndexChanged.connect(self.set_channel4_vscale)
        self._mw.channel1_impedance_input_radioButton.clicked.connect(self.set_channel1_impedance_input)
        self._mw.channel2_impedance_input_radioButton.clicked.connect(self.set_channel2_impedance_input)
        self._mw.channel3_impedance_input_radioButton.clicked.connect(self.set_channel3_impedance_input)
        self._mw.channel4_impedance_input_radioButton.clicked.connect(self.set_channel4_impedance_input)
        self._mw.channel1_display_radioButton.clicked.connect(self.channel1_state_change)
        self._mw.channel2_display_radioButton.clicked.connect(self.channel2_state_change)
        self._mw.channel3_display_radioButton.clicked.connect(self.channel3_state_change)
        self._mw.channel4_display_radioButton.clicked.connect(self.channel4_state_change)
        self._mw.channel1_offset_doubleSpinBox.valueChanged.connect(self.set_channel1_offset)
        self._mw.channel1_zero_offset_pushButton.clicked.connect(self.set_channel1_zero_offset)
        self._mw.channel2_offset_doubleSpinBox.valueChanged.connect(self.set_channel2_offset)
        self._mw.channel2_zero_offset_pushButton.clicked.connect(self.set_channel2_zero_offset)
        self._mw.channel3_offset_doubleSpinBox.valueChanged.connect(self.set_channel3_offset)
        self._mw.channel3_zero_offset_pushButton.clicked.connect(self.set_channel3_zero_offset)
        self._mw.channel4_offset_doubleSpinBox.valueChanged.connect(self.set_channel4_offset)
        self._mw.channel4_zero_offset_pushButton.clicked.connect(self.set_channel4_zero_offset)

        self._mw.savedata_pushButton.clicked.connect(self._scope_logic.save_data)
        self._mw.screenshot_pushButton.clicked.connect(self._scope_logic.get_screenshot_data)
        self._scope_logic.screenshotDataUpdated.connect(self.plot_screenshot)

        #self._mw.screenshot_pushButton.click()


    ''' Functions '''
    def channel1_state_change(self):
        if self._mw.channel1_display_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=1, state='ON')
        else:
            self._scope_logic.change_channel_state(channel=1, state='OFF')

    def set_channel1_vscale(self, ind):
        val = float(self._mw.channel1_vscale_comboBox.itemText(ind))
        self._scope_logic.set_channel1_vscale(val)
        return val

    def set_channel1_impedance_input(self):
        if self._mw.channel1_impedance_input_radioButton.isChecked():
            self._scope_logic.set_channel1_impedance_input_1M()
        else:
            self._scope_logic.set_channel1_impedance_input_50()

    def set_channel1_offset(self):
        value = -self._mw.channel1_offset_doubleSpinBox.value()
        self._scope_logic.set_channel1_offset(value)

    def set_channel1_zero_offset(self):
        self._mw.channel1_offset_doubleSpinBox.setValue(0)
        value = -self._mw.channel1_offset_doubleSpinBox.value()
        self._scope_logic.set_channel1_offset(value)

    def channel2_state_change(self):
        if self._mw.channel2_display_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=2, state='ON')
        else:
            self._scope_logic.change_channel_state(channel=2, state='OFF')

    def set_channel2_vscale(self, ind):
        val = float(self._mw.channel2_vscale_comboBox.itemText(ind))
        self._scope_logic.set_channel2_vscale(val)

    def set_channel2_impedance_input(self):
        if self._mw.channel2_impedance_input_radioButton.isChecked():
            self._scope_logic.set_channel2_impedance_input_1M()
        else:
            self._scope_logic.set_channel2_impedance_input_50()

    def set_channel2_offset(self):
        value = -self._mw.channel2_offset_doubleSpinBox.value()
        self._scope_logic.set_channel2_offset(value)

    def set_channel2_zero_offset(self):
        self._mw.channel2_offset_doubleSpinBox.setValue(0)
        value = -self._mw.channel2_offset_doubleSpinBox.value()
        self._scope_logic.set_channel2_offset(value)

    def channel3_state_change(self):
        if self._mw.channel3_display_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=3, state='ON')
        else:
            self._scope_logic.change_channel_state(channel=3, state='OFF')

    def set_channel3_vscale(self, ind):
        val = float(self._mw.channel3_vscale_comboBox.itemText(ind))
        self._scope_logic.set_channel3_vscale(val)

    def set_channel3_impedance_input(self):
        if self._mw.channel3_impedance_input_radioButton.isChecked():
            self._scope_logic.set_channel3_impedance_input_1M()
        else:
            self._scope_logic.set_channel3_impedance_input_50()

    def set_channel3_offset(self):
        value = -self._mw.channel3_offset_doubleSpinBox.value()
        self._scope_logic.set_channel3_offset(value)

    def set_channel3_zero_offset(self):
        self._mw.channel3_offset_doubleSpinBox.setValue(0)
        value = -self._mw.channel3_offset_doubleSpinBox.value()
        self._scope_logic.set_channel3_offset(value)

    def channel4_state_change(self):
        if self._mw.channel4_display_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=4, state='ON')
        else:
            self._scope_logic.change_channel_state(channel=4, state='OFF')

    def set_channel4_vscale(self, ind):
        val = float(self._mw.channel4_vscale_comboBox.itemText(ind))
        self._scope_logic.set_channel4_vscale(val)

    def set_channel4_impedance_input(self):
        if self._mw.channel4_impedance_input_radioButton.isChecked():
            self._scope_logic.set_channel4_impedance_input_1M()
        else:
            self._scope_logic.set_channel4_impedance_input_50()

    def set_channel4_offset(self):
        value = -self._mw.channel4_offset_doubleSpinBox.value()
        self._scope_logic.set_channel4_offset(value)

    def set_channel4_zero_offset(self):
        self._mw.channel4_offset_doubleSpinBox.setValue(0)
        value = -self._mw.channel4_offset_doubleSpinBox.value()
        self._scope_logic.set_channel4_offset(value)

    def set_trigger_source(self, ind):
            channel = self._mw.trigger_source_comboBox.itemText(ind)[-1]
            mode = self._mw.trigger_mode_comboBox.itemText(self._mw.trigger_mode_comboBox.currentIndex())
            self._scope_logic.set_trigger_source(mode, channel)

    def set_trigger_mode(self, ind):
        mode = self._mw.trigger_mode_comboBox.itemText(ind)
        self._scope_logic.set_trigger_mode(mode)

    def set_trigger_level(self, ind):
        mode = self._mw.trigger_mode_comboBox.currentText()
        value = self._mw.trigger_level_doubleSpinBox.value()
        self._scope_logic.set_trigger_level(mode, value)

    def set_time_scale(self, ind):
        value = float(self._mw.time_scale_comboBox.itemText(ind))
        self._scope_logic.set_time_scale(value)
        return value

    def set_time_delay(self):
        value = self._mw.time_delay_doubleSpinBox.value()
        self._scope_logic.set_time_delay(value)

    def plot_screenshot(self):
        self._mw.label.setPixmap(QPixmap("C:\software\Qudi -Rasmus\screenshot.png"))
        self._mw.label.show()

    def set_trigger_50(self):
        self._scope_logic.set_trigger_50()
        self._mw.trigger_level_doubleSpinBox.setValue(self._scope_logic.get_trigger_level())
