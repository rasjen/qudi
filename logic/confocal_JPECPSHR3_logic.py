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

class ConfocalScannerLogic(Base, EmptyInterface):

    """This is the Interface class to define the controls for the simple
    microwave hardware.
    """
    _modclass = 'ConfocalLogic'
    _modtype = 'logic'

    # connectors
    confocalscanner2 = Connector(interface='EmptyInterface')
    counter1 = Connector(interface='CounterLogic')
    savelogic = Connector(interface='SaveLogic')

    signal_xy_image_updated = QtCore.Signal()
    signal_continue_snake_scan = QtCore.Signal()


    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._scanner_logic = self.get_connector('confocalscanner2')
        self._counter_logic = self.get_connector('counter1')
        self._save_logic = self.get_connector('savelogic')

        #self.signal_xy_image_updated.connect(self.xy_image_updated, QtCore.Qt.QueuedConnection)
        self.signal_continue_snake_scan.connect(self.snake_scan, QtCore.Qt.QueuedConnection)



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

    def set_up_counter(self, counter_channels='/Dev1/Ctr1', sources='/Dev1/PFI13', clock_channel='/Dev1/Ctr0', counter_buffer=None):
        self._counter_logic._counting_device.set_up_counter(counter_channels, sources, clock_channel, counter_buffer)

    def set_count_frequency(self, frequency=50):
        self._counter_logic.set_count_frequency(frequency)

    def set_count_length(self, length=300):
        self._counter_logic.set_count_length(length)

    # snake scan methods
    def initialize_snake_scan(self, step, square_side):
        self.start_counter()
        self.step = step
        self.square_side = square_side
        self.point = 0
        self.line = 0
        self.data = np.zeros((int(np.round(square_side / step)), int(np.round(square_side / step))), dtype=int)
        self.snake_scan_iteration = 0

    def snake_scan(self):
        '''Scan a square area around a central spot describing a snake movement'''
        # First snake scan iteration :
        # 1: Go to the starting point of the scan area
        # 2: Acquire the point
        # 3: Continue to scan
        if self.snake_scan_iteration == 0:
            self.set_snake_scan_begin_position(self.step, self.square_side)
            self.acquire_point()
            self.signal_xy_image_updated.emit()
            self.point += 1
            self.snake_scan_iteration += 1
            self.signal_continue_snake_scan.emit()
            return
        # Last snake scan iteration after the last point is scanend :
        # 1: Go back to central point of the area of the scan
        # 2: Stop the scan
        elif self.snake_scan_iteration == self.square_side**2:
            self.set_snake_scan_begin_position(self.step, self.square_side)
            self.snake_scan_iteration += 1
            return
        # Other snake scan iterations
        # 1: Move the scanner
        # 2: Acquire the point
        # 3: Continue to scan
        else:
            # change line if the number of point complete a line
            if self.point == self.square_side:
                self.point = 0
                # vertical_move
                self.move_scanner_xyz(0, self.step, 0)
                self.line += 1
            if self.line % 2 == 0:
                # horizontal move (positive way)
                self.move_scanner_xyz(self.step, 0, 0)
                self.acquire_point()
            else:
                # horizontal move (negative way)
                self.move_scanner_xyz(-self.step, 0, 0)
                self.acquire_point_reversed()
            # update the image
            self.signal_xy_image_updated.emit()
            self.point += 1
            self.snake_scan_iteration += 1
            self.signal_continue_snake_scan.emit()
            return

    def acquire_point(self):
        count_number = self._counter_logic._counting_device.get_counter(1)[0, 0]
        self.data[self.line, self.point] = count_number

    def acquire_point_reversed(self):
        count_number = self._counter_logic._counting_device.get_counter(1)[0, 0]
        self.data[self.line, np.size(self.data, 0) - self.point % np.size(self.data, 0) - 1] = count_number

    def xy_image_updated(self):
        print(self.data)
        return 0



    def move_scanner_xyz(self,x, y, z):
        self._scanner_logic.move_xyz(x, y, z)
        return 0

    def move_CLA1(self, displacement):
        self._scanner_logic.move_CLA1(displacement)
        return 0

    def move_CLA2(self, displacement):
        self._scanner_logic.move_CLA2(displacement)
        return 0

    def move_CLA3(self, displacement):
        self._scanner_logic.move_CLA3(displacement)
        return 0

    def set_snake_scan_begin_position(self, step, square_side):
        '''The snake scan scan a square area around a central spot.
        This function move the sample in order to start the snake scan on the top left corner
        of the square area and make the sample move back to the central spot when the snake scan is finished'''
        n = 0
        while n < (square_side/2)/step:
            self.move_scanner_xyz(-step, -step, 0)
            #while True:
            #    time.sleep(0.1)
            #    if self.get_CLA_STATUS(1) == 'Stopped' and self.get_CLA_STATUS(2) == 'Stopped' and self.get_CLA_STATUS(3) == 'Stopped':
            #       break
            n += 1
        print('done')