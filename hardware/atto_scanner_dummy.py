# -*- coding: utf-8 -*-

"""
This module contains the Qudi interface file for confocal scanner.

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
from random import randint
from time import sleep
from core.module import Base
from interface.atto_scanner_interface import AttoScanner
import numpy as np

class ConfocalScannerAtto(Base, AttoScanner):
    """ This is the Interface class to define the controls for the simple
    microwave hardware.
    """

    _modtype = 'AttoScanner'
    _modclass = 'hardware'

    _connectors = {'scanner': 'AttoScanner'}

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.info('The following configuration was found.')

        # checking for the right configuration

        # Internal parameters
        self._line_length = None

        self._position_range = [[0, 100e-6], [0, 100e-6], [0, 100e-6]]
        self._current_position = [0, 0, 0]#[0:len(self.get_scanner_axes())]
        self._current_position_abs = [0, 0, 0]#[0:len(self.get_scanner_axes())]
        self._num_points = 500
        self.can_move = False
        self.target_position = [0,0,0]

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """


    def on_deactivate(self):
        """ Deactivate properly the confocal scanner dummy.
        """
        self.reset_hardware()

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs
            can access it.

        @return int: error code (0:OK, -1:error)
        """
        self.log.warning('Scanning Device will be reset.')
        return 0

    def get_position_range(self):
        """ Returns the physical range of the scanner.

        @return float [4][2]: array of 4 ranges with an array containing lower
                              and upper limit. The unit of the scan range is
                              micrometer.
        """
        self._position_range = [[0, 5000e-6], [0, 5000e-6], [0, 5000e-6], [0, 0]]
        return self._position_range

    def set_position_range(self, myrange=None):
        """ Sets the physical range of the scanner.

        @param float [4][2] myrange: array of 4 ranges with an array containing
                                     lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        self._position_range = myrange

    def get_scanner_axes(self):
        """ Find out how many axes the scanning device is using for confocal and their names.

        @return list(str): list of axis names

        Example:
          For 3D confocal microscopy in cartesian coordinates, ['x', 'y', 'z'] is a sensible value.
          For 2D, ['x', 'y'] would be typical.
          You could build a turntable microscope with ['r', 'phi', 'z'].
          Most callers of this function will only care about the number of axes, though.

          On error, return an empty list.
        """
        return ['x', 'y', 'z']


    def set_scanner_position(self, x=None, y=None, z=None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)
        @param float a: postion in a-direction (volts)

        @return int: error code (0:OK, -1:error)
        """
        self._current_position = [x,y,z]

    def get_scanner_position(self):
        """ Get the current position of the scanner hardware.

        @return float[n]: current position in (x, y, z, a).
        """
        return self._current_position


    def single_step(self, axis='x', direction='forward'):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        pass

    def axis_output_status(self, axis, status='off'):
        pass

    def set_frequency(self, axis, freq):
        '''

        :param axis: 'x', 'y' 'z'
        :param freq: Frequency in Hz, internal resolution is 1 Hz
        :return:
        '''
        pass

    def set_amplitude(self, axis, amp):
        '''

        :param axis: 'x', 'y' 'z'
        :param amp: Amplitude in V, internal resolution is 1 mV
        :return:
        '''
        pass

    def get_frequency(self, axis):
        '''

        :param axis: 'x', 'y' 'z'
        :param freq: Frequency in Hz, internal resolution is 1 Hz
        :return:
        '''
        return 1000

    def get_amplitude(self, axis):
        '''

        :param axis: 'x', 'y' 'z'
        :param amp: Amplitude in V, internal resolution is 1 mV
        :return:
        '''
        return 10

    def enable_outputs(self):
        self.can_move = True
        pass

    def disable_outputs(self):
        self.can_move = False

    def set_target_range(self, axis, range):
        pass

    def set_target_position(self,axis,position):
        if axis == 'x':
            self.target_position[0] = position
        elif axis == 'y':
            self.target_position[1] = position
        elif axis == 'z':
            self.target_position[2] = position
        else:
            self.log.error('Axes should be x,y or z')
        print('targetposition', axis ,position)
        return 0

    def auto_move(self,axis,enable):
        if self.can_move is True:
            self._current_position = self.target_position
            while True:
                if self.getAxisStatus_target(axis):
                    break

    def getAxisStatus_target(self,axis):
        x = randint(0,1)
        return x

    def get_voltage_range(self):
        xV_range = [0,60]
        yV_range = [0,70]
        return [xV_range, yV_range]

    def set_dcvoltage(self, axis, voltage):
        '''

        :param axis: 'x', 'y' 'z'
        :param voltage: DC output voltage [V], internal resolution is 1 mV
        :return:
        '''
        voltage = np.round(voltage,3)
        print('dc', axis, voltage)