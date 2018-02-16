"""
Interfuse to do confocal scans with attocube stages.

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

import time
import numpy as np
from qtpy import QtCore

from core.module import Base
from interface.empty_interface import EmptyInterface
from core.module import Connector, ConfigOption, StatusVar
import matplotlib.pyplot as plt

class Keysight_33500B_logic(Base, EmptyInterface):

    """This is the Interface class to define the controls for the simple
    microwave hardware.
    """
    _modclass = 'Keysight_33500B_logic'
    _modtype = 'logic'

    # connectors
    keysight_33500B_hardware = Connector(interface='EmptyInterface')

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._Keysight_33500B_hardware = self.get_connector('keysight_33500B_hardware')

    def on_deactivate(self):
        self._Keysight_33500B_hardware.on_deactivate()

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs can access it.
        """
        pass

    def get_source_parameters(self, source):
        return self._Keysight_33500B_hardware.get_source_parameters(source)

    def get_output_status(self, source):
        return self._Keysight_33500B_hardware.get_output_status(source)

    def enable_output(self, source):
        self._Keysight_33500B_hardware.enable_output(source)

    def disable_output(self, source):
        self._Keysight_33500B_hardware.disable_output(source)

    def set_function(self, source, waveform):
        self._Keysight_33500B_hardware.set_function(source, waveform)

    def set_frequency(self, source, frequency):
        self._Keysight_33500B_hardware.set_frequency(source, frequency)

    def set_offset(self, source, offset):
        self._Keysight_33500B_hardware.set_offset(source, offset)

    def set_amplitude(self, source, amplitude):
        self._Keysight_33500B_hardware.set_amplitude(source, amplitude)