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

from core.module import Base
from interface.confocal_scanner_JPE_CPSHR3_nicard_interface import confocal_scanner_JPE_CPSHR3_nicard_interface
from core.module import Connector, ConfigOption, StatusVar


class confocal_scanner_JPE_CPSHR3_nicard_interfuse(Base, confocal_scanner_JPE_CPSHR3_nicard_interface):

    """This is the Interface class to define the controls for the simple
    microwave hardware.
    """
    _modclass = 'confocal_scanner_JPE_CPSHR3_micard_interfuse'
    _modtype = 'interfuse'
    # connectors
    scanner = Connector(interface='confocal_scanner_JPE_CPSHR3_nicard_interface')
    counter = Connector(interface='CounterLogic')

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._scanner_logic = self.get_connector('scanner')
        self._counter_logic = self.get_connector('counter')

    def on_deactivate(self):
        self._scanner_logic.on_deactivate()
        self._counter_logic.on_deactivate()

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs can access it.
        """
        pass

    # counter methods
    def start_counter(self):
        self._counter_logic.startCount()

    def stop_counter(self):
        self._counter_logic.stopCount()

    def get_counter(self, samples=None):
        counts = self._counter_logic._counting_device.get_counter(samples)
        return np.sum(counts[0])/samples

    def set_count_frequency(self, frequency=50):
        self._counter_logic.set_count_frequency(frequency)

    def set_count_length(self, length=300):
        self._counter_logic.set_count_length(length)

    # scanner methods

    def snake_scan(self, step, square_side):
        '''Scan a square area around a central spot describing a snake movement'''
        # Go to top left position of the square area
        self._scanner_logic.set_snake_scan_begin_position(step, square_side)
        n = 0
        n_lines = square_side/step
        point_number = 0
        while n <= n_lines :
            print('line = ', n)
            if n % 2 == 0 :
                while point_number <= square_side/step:
                    self._scanner_logic.move_xyz(step, 0, 0)
                    point += 1
            else :
                while point_number >= 0:
                    self._scanner_logic.move_xyz(-step, 0, 0)
                    point -=1
            self._scanner_logic.move_xyz(0, step, 0)
            n += 1
        self._scanner_logic.set_snake_scan_begin_position(step, square_side)

