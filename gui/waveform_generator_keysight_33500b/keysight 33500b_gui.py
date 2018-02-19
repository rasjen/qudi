# -*- coding: utf-8 -*-

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


class Keysight_33500B_GUI_Window(QtWidgets.QMainWindow):

    """ Create the Mainwindow based on the corresponding *.ui file. """

    sigPressKeyBoard = QtCore.Signal(QtCore.QEvent)
    sigDoubleClick = QtCore.Signal()

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'keysight_33500B.ui')
        self._doubleclicked = False

        # Load it
        super(Keysight_33500B_GUI_Window, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()

    def keyPressEvent(self, event):
        """Pass the keyboard press event from the main window further. """
        self.sigPressKeyBoard.emit(event)

    def mouseDoubleClickEvent(self, event):
        self._doubleclicked = True
        self.sigDoubleClick.emit()

class Keysight_33500B_GUI(GUIBase):

    """ Main Confocal Class for xy and depth scans.
    """
    _modclass = 'Keysight_33500B_GUI'
    _modtype = 'gui'

    # declare connectors
    keysight_33500B_logic = Connector(interface='EmptyInterface')

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
        self._keysight_33500B_logic = self.get_connector('keysight_33500B_logic')

        self.initMainUI()      # initialize the main GUI

    def initMainUI(self):
        """ Definition, configuration and initialisation of the confocal GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        Moreover it sets default values.
        """
        self._mw = Keysight_33500B_GUI_Window()

        # Adjust GUI Parameters
        self._mw.output_comboBox.addItems(['ON', 'OFF'])
        self._mw.output_comboBox_2.addItems(['ON', 'OFF'])
        self._mw.function_comboBox.addItems(['DC', 'SIN', 'SQUARE','RAMP','PULSE'])
        self._mw.function_comboBox_2.addItems(['DC', 'SIN', 'SQUARE','RAMP','PULSE'])

        self._mw.function_comboBox.setCurrentIndex(self._mw.function_comboBox.findText(self._keysight_33500B_logic.get_source_parameters(1)[0], QtCore.Qt.MatchFixedString))
        self._mw.function_comboBox_2.setCurrentIndex(self._mw.function_comboBox.findText(self._keysight_33500B_logic.get_source_parameters(2)[0], QtCore.Qt.MatchFixedString))
        self._mw.output_comboBox.setCurrentIndex(self._mw.output_comboBox.findText(self._keysight_33500B_logic.get_output_status(1), QtCore.Qt.MatchFixedString))
        self._mw.output_comboBox_2.setCurrentIndex(self._mw.output_comboBox_2.findText(self._keysight_33500B_logic.get_output_status(2), QtCore.Qt.MatchFixedString))
        self._mw.frequency_doubleSpinBox.setValue(self._keysight_33500B_logic.get_source_parameters(1)[1])
        self._mw.frequency_doubleSpinBox_2.setValue(self._keysight_33500B_logic.get_source_parameters(2)[1])
        self._mw.amplitude_doubleSpinBox.setValue(self._keysight_33500B_logic.get_source_parameters(1)[2])
        self._mw.amplitude_doubleSpinBox_2.setValue(self._keysight_33500B_logic.get_source_parameters(2)[2])
        self._mw.offset_doubleSpinBox.setValue(self._keysight_33500B_logic.get_source_parameters(1)[3])
        self._mw.offset_doubleSpinBox_2.setValue(self._keysight_33500B_logic.get_source_parameters(2)[3])
        self._mw.phase_doubleSpinBox.setValue(self._keysight_33500B_logic.get_source_parameters(1)[4])
        self._mw.phase_doubleSpinBox_2.setValue(self._keysight_33500B_logic.get_source_parameters(2)[4])

        if self._mw.function_comboBox.currentText() == 'DC':
            self._mw.frequency_doubleSpinBox.setEnabled(0)
            self._mw.amplitude_doubleSpinBox.setEnabled(0)
            self._mw.phase_doubleSpinBox.setEnabled(0)
        if self._mw.function_comboBox_2.currentText() == 'DC':
            self._mw.frequency_doubleSpinBox_2.setEnabled(0)
            self._mw.amplitude_doubleSpinBox_2.setEnabled(0)
            self._mw.phase_doubleSpinBox_2.setEnabled(0)

        # Connection
        self._mw.output_comboBox.currentTextChanged.connect(self.set_channel1_output_status)
        self._mw.output_comboBox_2.currentTextChanged.connect(self.set_channel2_output_status)

        self._mw.function_comboBox.currentTextChanged.connect(self.set_channel1_function)
        self._mw.function_comboBox_2.currentTextChanged.connect(self.set_channel2_function)

        self._mw.frequency_doubleSpinBox.valueChanged.connect(self.set_channel1_frequency)
        self._mw.frequency_doubleSpinBox_2.valueChanged.connect(self.set_channel2_frequency)

        self._mw.amplitude_doubleSpinBox.valueChanged.connect(self.set_channel1_amplitude)
        self._mw.amplitude_doubleSpinBox_2.valueChanged.connect(self.set_channel2_amplitude)

        self._mw.offset_doubleSpinBox.valueChanged.connect(self.set_channel1_offset)
        self._mw.offset_doubleSpinBox_2.valueChanged.connect(self.set_channel2_offset)

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def set_channel1_output_status(self):
        if self._mw.output_comboBox.currentText() == 'ON':
            self._keysight_33500B_logic.enable_output(1)
        elif self._mw.output_comboBox.currentText() == 'OFF':
            self._keysight_33500B_logic.disable_output(1)

    def set_channel2_output_status(self):
        if self._mw.output_comboBox_2.currentText() == 'ON':
            self._keysight_33500B_logic.enable_output(2)
        elif self._mw.output_comboBox_2.currentText() == 'OFF':
            self._keysight_33500B_logic.disable_output(2)

    def set_channel1_function(self):
        self._keysight_33500B_logic.set_function(1, self._mw.function_comboBox.currentText())
        if self._mw.function_comboBox.currentText() == 'DC':
            self._mw.frequency_doubleSpinBox.setEnabled(0)
            self._mw.amplitude_doubleSpinBox.setEnabled(0)
            self._mw.phase_doubleSpinBox.setEnabled(0)
        else:
            self._mw.frequency_doubleSpinBox.setEnabled(1)
            self._mw.amplitude_doubleSpinBox.setEnabled(1)
            self._mw.phase_doubleSpinBox.setEnabled(1)

    def set_channel2_function(self):
        self._keysight_33500B_logic.set_function(2, self._mw.function_comboBox_2.currentText())
        if self._mw.function_comboBox_2.currentText() == 'DC':
            self._mw.frequency_doubleSpinBox_2.setEnabled(0)
            self._mw.amplitude_doubleSpinBox_2.setEnabled(0)
            self._mw.phase_doubleSpinBox_2.setEnabled(0)
        else:
            self._mw.frequency_doubleSpinBox_2.setEnabled(1)
            self._mw.amplitude_doubleSpinBox_2.setEnabled(1)
            self._mw.phase_doubleSpinBox_2.setEnabled(1)

    def set_channel1_frequency(self):
        self._keysight_33500B_logic.set_frequency(1, self._mw.frequency_doubleSpinBox.value())

    def set_channel2_frequency(self):
        self._keysight_33500B_logic.set_frequency(2, self._mw.frequency_doubleSpinBox_2.value())

    def set_channel1_amplitude(self):
        self._keysight_33500B_logic.set_amplitude(1, self._mw.amplitude_doubleSpinBox.value())

    def set_channel2_amplitude(self):
        self._keysight_33500B_logic.set_amplitude(2, self._mw.amplitude_doubleSpinBox_2.value())

    def set_channel1_offset(self):
        self._keysight_33500B_logic.set_offset(1, self._mw.offset_doubleSpinBox.value())

    def set_channel2_offset(self):
        self._keysight_33500B_logic.set_offset(2, self._mw.offset_doubleSpinBox_2.value())
