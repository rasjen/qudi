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


from core.base import Base
from interface.confocal_scanner_atto_interface import ConfocalScannerInterfaceAtto
import numpy as np

class ConfocalScannerAtto(Base, ConfocalScannerInterfaceAtto):
    """ This is the Interface class to define the controls for the simple
    microwave hardware.
    """

    _modtype = 'ConfocalScannerInterfaceAtto'
    _modclass = 'hardware'

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

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """


        # put randomly distributed NVs in the scanner, first the x,y scan
        self._points = np.empty([self._num_points, 7])
        # amplitude
        self._points[:, 0] = np.random.normal(
            4e5,
            1e5,
            self._num_points)
        # x_zero
        self._points[:, 1] = np.random.uniform(
            self._position_range[0][0],
            self._position_range[0][1],
            self._num_points)
        # y_zero
        self._points[:, 2] = np.random.uniform(
            self._position_range[1][0],
            self._position_range[1][1],
            self._num_points)
        # sigma_x
        self._points[:, 3] = np.random.normal(
            0.7e-6,
            0.1e-6,
            self._num_points)
        # sigma_y
        self._points[:, 4] = np.random.normal(
            0.7e-6,
            0.1e-6,
            self._num_points)
        # theta
        self._points[:, 5] = 10
        # offset
        self._points[:, 6] = 0

        # now also the z-position
        #       gaussian_function(self,x_data=None,amplitude=None, x_zero=None, sigma=None, offset=None):

        self._points_z = np.empty([self._num_points, 4])
        # amplitude
        self._points_z[:, 0] = np.random.normal(
            1,
            0.05,
            self._num_points)

        # x_zero
        self._points_z[:, 1] = np.random.uniform(
            45e-6,
            55e-6,
            self._num_points)

        # sigma
        self._points_z[:, 2] = np.random.normal(
            0.5e-6,
            0.1e-6,
            self._num_points)

        # offset
        self._points_z[:, 3] = 0

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
        pass

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

    def get_scanner_count_channels(self):
        """ Returns the list of channels that are recorded while scanning an image.

        @return list(str): channel names

        Most methods calling this might just care about the number of channels.
        """
        pass

    def set_up_scanner_clock(self, clock_frequency=None, clock_channel=None):
        """ Configures the hardware clock of the NiDAQ card to give the timing.

        @param float clock_frequency: if defined, this sets the frequency of the
                                      clock
        @param str clock_channel: if defined, this is the physical channel of
                                  the clock

        @return int: error code (0:OK, -1:error)
        """
        pass

    def set_up_scanner(self,
                       counter_channels=None,
                       sources=None,
                       clock_channel=None,
                       scanner_ao_channels=None):
        """ Configures the actual scanner with a given clock.

        @param str counter_channels: if defined, these are the physical conting devices
        @param str sources: if defined, these are the physical channels where
                                  the photons are to count from
        @param str clock_channel: if defined, this specifies the clock for the
                                  counter
        @param str scanner_ao_channels: if defined, this specifies the analoque
                                        output channels

        @return int: error code (0:OK, -1:error)
        """
        pass


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


    def scan_line(self, line_path=None, pixel_clock=False):
        """ Scans a line and returns the counts on that line.

        @param float[k][n] line_path: array k of n-part tuples defining the pixel positions
        @param bool pixel_clock: whether we need to output a pixel clock for this line

        @return float[k][m]: the photon counts per second for k pixels with m channels
        """
        pass


    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        pass

    def close_scanner_clock(self, power=0):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        pass

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
        pass

    def disable_outputs(self):
        pass

    def set_target_range(self, axis, range):
        pass

    def set_target_position(self,axis,position):
        print('targetposition', axis ,position)
        pass

    def auto_move(self,axis,enable):
        pass

    def getAxisStatus_target(self,axis):
        return 1

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