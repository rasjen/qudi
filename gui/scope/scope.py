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

        # Configuration of the trigger source comboWidget
        self._mw.trigger_source_comboBox.addItem('1')
        self._mw.trigger_source_comboBox.addItem('2')
        self._mw.trigger_source_comboBox.addItem('3')
        self._mw.trigger_source_comboBox.addItem('4')

        # Configuration of the time scale comboWidget
        self._mw.time_scale_comboBox.addItem('2e-9')
        self._mw.time_scale_comboBox.addItem('5e-9')
        self._mw.time_scale_comboBox.addItem('1e-6')
        self._mw.time_scale_comboBox.addItem('2e-6')
        self._mw.time_scale_comboBox.addItem('5e-6')
        self._mw.time_scale_comboBox.addItem('1e-3')
        self._mw.time_scale_comboBox.addItem('2e-3')
        self._mw.time_scale_comboBox.addItem('5e-3')
        self._mw.time_scale_comboBox.addItem('1e-2')
        self._mw.time_scale_comboBox.addItem('2e-2')
        self._mw.time_scale_comboBox.addItem('5e-2')
        self._mw.time_scale_comboBox.addItem('1e-1')
        self._mw.time_scale_comboBox.addItem('2e-1')
        self._mw.time_scale_comboBox.addItem('5e-1')
        self._mw.time_scale_comboBox.addItem('1')
        self._mw.time_scale_comboBox.addItem('2')
        self._mw.time_scale_comboBox.addItem('5')
        self._mw.time_scale_comboBox.addItem('10')
        self._mw.time_scale_comboBox.addItem('20')
        self._mw.time_scale_comboBox.addItem('50')

        # Configuration of the channel 1 vertical scale comboWidget
        self._mw.channel1_vscale_comboBox.addItem('1e-3')
        self._mw.channel1_vscale_comboBox.addItem('2e-3')
        self._mw.channel1_vscale_comboBox.addItem('5e-3')
        self._mw.channel1_vscale_comboBox.addItem('1e-2')
        self._mw.channel1_vscale_comboBox.addItem('2e-2')
        self._mw.channel1_vscale_comboBox.addItem('5e-2')
        self._mw.channel1_vscale_comboBox.addItem('1e-1')
        self._mw.channel1_vscale_comboBox.addItem('2e-1')
        self._mw.channel1_vscale_comboBox.addItem('5e-1')
        self._mw.channel1_vscale_comboBox.addItem('1')
        self._mw.channel1_vscale_comboBox.addItem('2')
        self._mw.channel1_vscale_comboBox.addItem('5')

        # Configuration of the channel 2 vertical scale comboWidget
        self._mw.channel2_vscale_comboBox.addItem('1e-3')
        self._mw.channel2_vscale_comboBox.addItem('2e-3')
        self._mw.channel2_vscale_comboBox.addItem('5e-3')
        self._mw.channel2_vscale_comboBox.addItem('1e-2')
        self._mw.channel2_vscale_comboBox.addItem('2e-2')
        self._mw.channel2_vscale_comboBox.addItem('5e-2')
        self._mw.channel2_vscale_comboBox.addItem('1e-1')
        self._mw.channel2_vscale_comboBox.addItem('2e-1')
        self._mw.channel2_vscale_comboBox.addItem('5e-1')
        self._mw.channel2_vscale_comboBox.addItem('1')
        self._mw.channel2_vscale_comboBox.addItem('2')
        self._mw.channel2_vscale_comboBox.addItem('5')

        # Configuration of the channel 3 vertical scale comboWidget
        self._mw.channel3_vscale_comboBox.addItem('1e-3')
        self._mw.channel3_vscale_comboBox.addItem('2e-3')
        self._mw.channel3_vscale_comboBox.addItem('5e-3')
        self._mw.channel3_vscale_comboBox.addItem('1e-2')
        self._mw.channel3_vscale_comboBox.addItem('2e-2')
        self._mw.channel3_vscale_comboBox.addItem('5e-2')
        self._mw.channel3_vscale_comboBox.addItem('1e-1')
        self._mw.channel3_vscale_comboBox.addItem('2e-1')
        self._mw.channel3_vscale_comboBox.addItem('5e-1')
        self._mw.channel3_vscale_comboBox.addItem('1')
        self._mw.channel3_vscale_comboBox.addItem('2')
        self._mw.channel3_vscale_comboBox.addItem('5')

        # Configuration of the channel 4 vertical scale comboWidget
        self._mw.channel4_vscale_comboBox.addItem('1e-3')
        self._mw.channel4_vscale_comboBox.addItem('2e-3')
        self._mw.channel4_vscale_comboBox.addItem('5e-3')
        self._mw.channel4_vscale_comboBox.addItem('1e-2')
        self._mw.channel4_vscale_comboBox.addItem('2e-2')
        self._mw.channel4_vscale_comboBox.addItem('5e-2')
        self._mw.channel4_vscale_comboBox.addItem('1e-1')
        self._mw.channel4_vscale_comboBox.addItem('2e-1')
        self._mw.channel4_vscale_comboBox.addItem('5e-1')
        self._mw.channel4_vscale_comboBox.addItem('1')
        self._mw.channel4_vscale_comboBox.addItem('2')
        self._mw.channel4_vscale_comboBox.addItem('5')

        # Configuration of the channel 1 vertical scale comboWidget
        self._mw.trigger_mode_comboBox.addItem('EDGE')
        self._mw.trigger_mode_comboBox.addItem('GLITch')
        self._mw.trigger_mode_comboBox.addItem('PATTern')
        self._mw.trigger_mode_comboBox.addItem('TV')
        self._mw.trigger_mode_comboBox.addItem('DELay')
        self._mw.trigger_mode_comboBox.addItem('EBURst')
        self._mw.trigger_mode_comboBox.addItem('OR')
        self._mw.trigger_mode_comboBox.addItem('RUNT')
        self._mw.trigger_mode_comboBox.addItem('SHOLd')
        self._mw.trigger_mode_comboBox.addItem('TRANsition')
        self._mw.trigger_mode_comboBox.addItem('SBUS{1 | 2}')
        self._mw.trigger_mode_comboBox.addItem('USB')



        # Configuration of the channels RadioButton
        self._mw.channel1_display_radioButton.setChecked(True)
        self._mw.channel2_display_radioButton.setChecked(True)
        self._mw.channel3_display_radioButton.setChecked(True)
        self._mw.channel4_display_radioButton.setChecked(True)
        self._mw.channel1_DC_radioButton.setChecked(True)
        self._mw.channel2_DC_radioButton.setChecked(True)
        self._mw.channel3_DC_radioButton.setChecked(True)
        self._mw.channel4_DC_radioButton.setChecked(True)
        self._mw.channel1_impedance_input_radioButton.setChecked(True)
        self._mw.channel2_impedance_input_radioButton.setChecked(True)
        self._mw.channel3_impedance_input_radioButton.setChecked(True)
        self._mw.channel4_impedance_input_radioButton.setChecked(True)


        # Connections
        self._mw.run_pushButton.clicked.connect(self._scope_logic.run_continuous)
        self._mw.stop_pushButton.clicked.connect(self._scope_logic.stop_aq)
        self._mw.singlerun_pushButton.clicked.connect(self._scope_logic.single_aq)
        self._mw.autoscale_pushButton.clicked.connect(self._scope_logic.auto_scale)

        self._mw.time_scale_comboBox.currentIndexChanged.connect(self.time_scale)
        self._mw.time_delay_doubleSpinBox.valueChanged.connect(self.time_delay)

        self._mw.channel1_DC_radioButton.clicked.connect(self._scope_logic.set_channel1_DC_couling)
        self._mw.channel1_AC_radioButton.clicked.connect(self._scope_logic.set_channel1_AC_couling)
        self._mw.channel2_DC_radioButton.clicked.connect(self._scope_logic.set_channel2_DC_couling)
        self._mw.channel2_AC_radioButton.clicked.connect(self._scope_logic.set_channel2_AC_couling)
        self._mw.channel3_DC_radioButton.clicked.connect(self._scope_logic.set_channel3_DC_couling)
        self._mw.channel3_AC_radioButton.clicked.connect(self._scope_logic.set_channel3_AC_couling)
        self._mw.channel4_DC_radioButton.clicked.connect(self._scope_logic.set_channel4_DC_couling)
        self._mw.channel4_AC_radioButton.clicked.connect(self._scope_logic.set_channel4_AC_couling)

        self._mw.trigger_source_comboBox.currentIndexChanged.connect(self.trigger_source)
        self._mw.trigger_mode_comboBox.currentIndexChanged.connect(self.trigger_mode)
        self._mw.trigger50_pushButton.clicked.connect(self._scope_logic.trigger_50)
        self._mw.trigger_level_doubleSpinBox.valueChanged.connect(self.trigger_level)

        self._mw.aqcuire_mode_normal_radioButton.clicked.connect(self._scope_logic.acquire_mode_normal)
        self._mw.aqcuire_mode_highres_radioButton.clicked.connect(self._scope_logic.aqcuire_mode_highres)
        self._mw.aqcuire_mode_average_radioButton.clicked.connect(self._scope_logic.aqcuire_mode_average)
        self._mw.aqcuire_mode_peak_radioButton.clicked.connect(self._scope_logic.aqcuire_mode_peak)

        self._mw.channel1_vscale_comboBox.currentIndexChanged.connect(self.change_channel1_vscale)
        self._mw.channel2_vscale_comboBox.currentIndexChanged.connect(self.change_channel2_vscale)
        self._mw.channel3_vscale_comboBox.currentIndexChanged.connect(self.change_channel3_vscale)
        self._mw.channel4_vscale_comboBox.currentIndexChanged.connect(self.change_channel4_vscale)

        self._mw.channel1_impedance_input_radioButton.clicked.connect(self.channel1_impedance_input)
        self._mw.channel2_impedance_input_radioButton.clicked.connect(self.channel2_impedance_input)
        self._mw.channel3_impedance_input_radioButton.clicked.connect(self.channel3_impedance_input)
        self._mw.channel4_impedance_input_radioButton.clicked.connect(self.channel4_impedance_input)

        self._mw.channel1_display_radioButton.clicked.connect(self.channel1_state_chage)
        self._mw.channel2_display_radioButton.clicked.connect(self.channel2_state_chage)
        self._mw.channel3_display_radioButton.clicked.connect(self.channel3_state_chage)
        self._mw.channel4_display_radioButton.clicked.connect(self.channel4_state_chage)

        self._mw.channel1_offset_doubleSpinBox.valueChanged.connect(self.channel1_offset)
        self._mw.channel1_zero_offset_pushButton.clicked.connect(self.channel1_zero_offset)
        self._mw.channel2_offset_doubleSpinBox.valueChanged.connect(self.channel2_offset)
        self._mw.channel2_zero_offset_pushButton.clicked.connect(self.channel2_zero_offset)
        self._mw.channel3_offset_doubleSpinBox.valueChanged.connect(self.channel3_offset)
        self._mw.channel3_zero_offset_pushButton.clicked.connect(self.channel3_zero_offset)
        self._mw.channel4_offset_doubleSpinBox.valueChanged.connect(self.channel4_offset)
        self._mw.channel4_zero_offset_pushButton.clicked.connect(self.channel4_zero_offset)

        self._mw.getdata_pushButton.clicked.connect(self._scope_logic.get_data)
        self._mw.savedata_pushButton.clicked.connect(self._scope_logic.save_data)

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

        for ch in self._scope_logic.get_channels():
            self._scope_logic.change_channel_state(channel=ch, state='ON')

    def updateData(self):
        """
        The function that grabs the data and sends it to the plot.
        """
        #if self._scope_logic.getState() == 'locked':
        t_vals = self._scope_logic.get_timescale()
        for i, ch in enumerate(self._scope_logic.active_channels):
             self.curves[i].setData(y=self._scope_logic.scopedata[i], x=t_vals)
        self._pw.enableAutoRange()
        return 0

    def set_time_range(self):
        self._scope_logic.set_time_range(self._mw.time_range_Spinbox.value()*1e-6)

    def update_traceplot(self):
        self._tracesWidget.clear()
        for data in self._scope_logic.split_data:
            self._pw.addItem(pg.PlotDataItem(pen=pg.mkPen(data), symbol=None))

    # Channel 1 functions

    def channel1_state_chage(self):
        if self._mw.channel1_display_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=1, state='ON')
        else:
            self._scope_logic.change_channel_state(channel=1, state='OFF')

    def change_channel1_vscale(self, ind):
        val = float(self._mw.channel1_vscale_comboBox.itemText(ind))
        self._scope_logic.set_channel1_vscale(val)
        return val

    def channel1_impedance_input(self):
        if self._mw.channel1_impedance_input_radioButton.isChecked():
            self._scope_logic.set_channel1_impedance_input_1M()
        else:
            self._scope_logic.set_channel1_impedance_input_50()


    def channel1_offset(self):
        value = -self._mw.channel1_offset_doubleSpinBox.value()
        self._scope_logic.channel1_offset(value)

    def channel1_zero_offset(self):
        self._mw.channel1_offset_doubleSpinBox.setValue(0)
        value = -self._mw.channel1_offset_doubleSpinBox.value()
        self._scope_logic.channel1_offset(value)


    # Channel 2 functions

    def channel2_state_chage(self):
        if self._mw.channel2_display_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=2, state='ON')
        else:
            self._scope_logic.change_channel_state(channel=2, state='OFF')

    def change_channel2_vscale(self, ind):
        val = float(self._mw.channel2_vscale_comboBox.itemText(ind))
        self._scope_logic.set_channel2_vscale(val)

    def channel2_impedance_input(self):
        if self._mw.channel2_impedance_input_radioButton.isChecked():
            self._scope_logic.set_channel2_impedance_input_1M()
        else:
            self._scope_logic.set_channel2_impedance_input_50()

    def channel2_offset(self):
        value = -self._mw.channel2_offset_doubleSpinBox.value()
        self._scope_logic.channel2_offset(value)

    def channel2_zero_offset(self):
        self._mw.channel2_offset_doubleSpinBox.setValue(0)
        value = -self._mw.channel2_offset_doubleSpinBox.value()
        self._scope_logic.channel2_offset(value)

    # Channel 3 functions

    def channel3_state_chage(self):
        if self._mw.channel3_display_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=3, state='ON')
        else:
            self._scope_logic.change_channel_state(channel=3, state='OFF')

    def change_channel3_vscale(self, ind):
        val = float(self._mw.channel3_vscale_comboBox.itemText(ind))
        self._scope_logic.set_channel3_vscale(val)

    def channel3_impedance_input(self):
        if self._mw.channel3_impedance_input_radioButton.isChecked():
            self._scope_logic.set_channel3_impedance_input_1M()
        else:
            self._scope_logic.set_channel3_impedance_input_50()

    def channel3_offset(self):
        value = -self._mw.channel3_offset_doubleSpinBox.value()
        self._scope_logic.channel3_offset(value)

    def channel3_zero_offset(self):
        self._mw.channel3_offset_doubleSpinBox.setValue(0)
        value = -self._mw.channel3_offset_doubleSpinBox.value()
        self._scope_logic.channel3_offset(value)

    # Channel 4 functions

    def channel4_state_chage(self):
        if self._mw.channel4_display_radioButton.isChecked():
            self._scope_logic.change_channel_state(channel=4, state='ON')
        else:
            self._scope_logic.change_channel_state(channel=4, state='OFF')

    def change_channel4_vscale(self, ind):
        val = float(self._mw.channel4_vscale_comboBox.itemText(ind))
        self._scope_logic.set_channel4_vscale(val)

    def channel4_impedance_input(self):
        if self._mw.channel4_impedance_input_radioButton.isChecked():
            self._scope_logic.set_channel4_impedance_input_1M()
        else:
            self._scope_logic.set_channel4_impedance_input_50()

    def channel4_offset(self):
        value = -self._mw.channel4_offset_doubleSpinBox.value()
        self._scope_logic.channel4_offset(value)

    def channel4_zero_offset(self):
        self._mw.channel4_offset_doubleSpinBox.setValue(0)
        value = -self._mw.channel4_offset_doubleSpinBox.value()
        self._scope_logic.channel4_offset(value)

    # Trigger functions

    def trigger_source(self, ind):
            channel = self._mw.trigger_source_comboBox.itemText(ind)
            mode = self._mw.trigger_mode_comboBox.itemText(self._mw.trigger_mode_comboBox.currentIndex())
            self._scope_logic.trigger_source(mode, channel)

    def trigger_mode(self, ind):
        mode = self._mw.trigger_mode_comboBox.itemText(ind)
        self._scope_logic.trigger_mode(mode)

    def trigger_level(self, ind):
        mode = self._mw.trigger_mode_comboBox.currentText()
        value = self._mw.trigger_level_doubleSpinBox.value()
        self._scope_logic.trigger_level(mode, value)

    def time_scale(self, ind):
        value = float(self._mw.time_scale_comboBox.itemText(ind))
        self._scope_logic.time_scale(value)
        return value

    def time_delay(self):
        value = self._mw.time_delay_doubleSpinBox.value()
        self._scope_logic.time_delay(value)

