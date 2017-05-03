# -*- coding: utf-8 -*-
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

from core.base import Base
from interface.confocal_scanner_atto_interface import ConfocalScannerInterfaceAtto


class AttocubeScannerInterfuse(Base, ConfocalScannerInterfaceAtto):

    """This is the Interface class to define the controls for the simple
    microwave hardware.
    """
    _modclass = 'AttocubeScannerInterfuse'
    _modtype = 'interfuse'
    # connectors
    _connectors = {
        'confocalscanner1': 'ConfocalScannerInterfaceAtto',
        'counter1': 'SlowCounterInterface'
    }

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.info('The following configuration was found.')

        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key, config[key]))

        if 'clock_frequency' in config.keys():
            self._clock_frequency = config['clock_frequency']
        else:
            self._clock_frequency = 100
            self.log.warning('No clock_frequency configured taking 100 Hz '
                    'instead.')

        # Internal parameters
        self.integration_time = 100  # ms
        self.log.warning('integration time is set to 100 ms')

        self._XY_fine_scan = False
        self._set_stepscan = False
        self.stop_scan = False
        self.current_position = None

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """

        self._atto_scanner_hw = self.get_connector('confocalscanner1')
        self._counter = self.get_connector('counter1')


    def on_deactivate(self):
        self.reset_hardware()

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs can access it.

        @return int: error code (0:OK, -1:error)
        """
        self.log.warning('Scanning Devices will be reset.')
        self._atto_scanner_hw.reset_hardware()
        self._counter.reset_hardware()
        return 0

    def get_position_range(self):
        """ Returns the physical range of the scanner.
        This is a direct pass-through to the scanner HW.

        @return float [4][2]: array of 4 ranges with an array containing lower and upper limit
        """

        return self._atto_scanner_hw.get_position_range()

    def set_position_range(self, myrange=None):
        """ Sets the physical range of the scanner.
        This is a direct pass-through to the scanner HW

        @param float [4][2] myrange: array of 4 ranges with an array containing lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        if myrange is None:
            myrange = [[0,1],[0,1],[0,1],[0,1]]

        self._atto_scanner_hw.set_position_range(myrange=myrange)

        return 0

    def set_up_scanner_clock(self, clock_frequency = None, clock_channel = None):
        """ Configures the hardware clock of the NiDAQ card to give the timing.
        This is a direct pass-through to the scanner HW

        @param float clock_frequency: if defined, this sets the frequency of the clock
        @param string clock_channel: if defined, this is the physical channel of the clock

        @return int: error code (0:OK, -1:error)
        """

        return self._counter.set_up_clock(clock_frequency=clock_frequency, clock_channel=clock_channel)

    def set_up_scanner(self, counter_channel = None, photon_source = None, clock_channel = None, scanner_ao_channels = None):
        """ Configures the actual scanner with a given clock.

        TODO this is not technically required, because the spectrometer scanner does not need clock synchronisation.

        @param string counter_channel: if defined, this is the physical channel of the counter
        @param string photon_source: if defined, this is the physical channel where the photons are to count from
        @param string clock_channel: if defined, this specifies the clock for the counter
        @param string scanner_ao_channels: if defined, this specifies the analoque output channels

        @return int: error code (0:OK, -1:error)
        """
        try:
            self._atto_scanner_hw.enable_outputs()
            self._counter.set_up_counter()
            return 0
        except:
            return -1
        return 0

    def get_scanner_axes(self):
        """ Pass through scanner axes. """
        return self._atto_scanner_hw.get_scanner_axes()

    def get_scanner_count_channels(self):
        '''
        Pass through counter channels.
        :return:
        '''

        return self._counter.get_counter_channels()

    def set_scanner_position(self, x=None, y=None, z=None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        @param float x: postion in x-direction
        @param float y: postion in y-direction
        @param float z: postion in z-direction


        @return int: error code (0:OK, -1:error)
        """
        try:
            print('x=',x)
            print('z=', z)
            print('y=', y)
            return self._atto_scanner_hw.set_scanner_position(x=x, y=y, z=z)
        except:
            self.log.error('can not go to this position since ')

    def get_scanner_position(self):
        """ Get the current position of the scanner hardware.

        @return float[]: current position in (x, y, z, a).
        """
        [x, y, z] =self._atto_scanner_hw.get_scanner_position()

        self.current_position = [x,y,z]

        return  self.current_position

    def scan_line(self, line_path=None, pixel_clock=False):
        """ Scans a line and returns the counts on that line.

        @param float[][4] line_path: array of 4-part tuples defining the voltage points
        @param bool pixel_clock: whether we need to output a pixel clock for this line

        @return float[]: the photon counts per second
        """

        # if len(self._scanner_counter_daq_tasks) < 1:
        #     self.log.error('No counter is running, cannot scan a line without one.')
        #     return np.array([[-1.]])

        if not isinstance( line_path, (frozenset, list, set, tuple, np.ndarray, ) ):
            self.log.error('Given voltage list is no array type.')
            return np.array([-1.])

        if self.stop_scan == True:
            return -1

        self._atto_scanner_hw.set_target_range('x', 500e-9)
        self._atto_scanner_hw.set_target_range('y', 500e-9)

        self._counting_samples = int(self.integration_time/1000 * self._clock_frequency) #integration time is in ms
        x_pos = np.round(np.array(line_path[0]), 7)
        y_pos = np.round(np.array(line_path[1]), 7)

        line_counts = np.zeros_like([line_path[0],])


        if self._XY_fine_scan:
            for i in range(len(x_pos)):
                self._atto_scanner_hw.set_fine_position('x', line_path[0][i])
                self._atto_scanner_hw.set_fine_position('y', line_path[1][i])
                rawdata = self._counter.get_counter(samples=self._counting_samples)
                line_counts[0, i] = rawdata.sum() / self._counting_samples


        elif self._set_stepscan:
            self._atto_scanner_hw.set_amplitude('x', 30)
            self._atto_scanner_hw.set_amplitude('y', 30)
            self._atto_scanner_hw.set_frequency('x', 1000)
            self._atto_scanner_hw.set_frequency('y', 1000)

            for i in range(len(x_pos)):

                if i == 0:
                    rawdata = self._counter.get_counter(samples=self._counting_samples)
                elif x_pos[i] > x_pos[i - 1]:
                    self._atto_scanner_hw.single_step('x', 'forward')
                    rawdata = self._counter.get_counter(samples=self._counting_samples)
                    print('forward', x_pos[i] - x_pos[i - 1])
                else:
                    self._atto_scanner_hw.single_step('x', 'backward')
                    rawdata = self._counter.get_counter(samples=self._counting_samples)
                    print('backward', x_pos[i] - x_pos[i - 1])

                line_counts[0, i] = rawdata.sum() / self._counting_samples

            self._atto_scanner_hw.single_step('y', 'forward')

        else:


            for i in range(len(x_pos)):
                if i==0:

                    self._atto_scanner_hw.set_target_position('x',x_pos[i])
                    self._atto_scanner_hw.set_target_position('y',y_pos[i])

                    self._atto_scanner_hw.auto_move('x',1)
                    self._atto_scanner_hw.auto_move('y',1)


                    while True:
                        if self._atto_scanner_hw.getAxisStatus_target('x'):
                            break

                    rawdata = self._counter.get_counter( samples= self._counting_samples)
                else:
                    if x_pos[i] != x_pos[i-1]:
                        self._atto_scanner_hw.set_target_position('x',x_pos[i])
                    if y_pos[i] != y_pos[i-1]:
                        self._atto_scanner_hw.set_target_position('y',y_pos[i])


                    self._atto_scanner_hw.auto_move('x',1)
                    self._atto_scanner_hw.auto_move('y',1)

                    try:
                        while True:
                            if self._atto_scanner_hw.getAxisStatus_target('y') & self._atto_scanner_hw.getAxisStatus_target('x'):
                                #print('wait until taget is reached')
                                break


                        rawdata = self._counter.get_counter(samples=self._counting_samples)
                    except:
                        self.log.error('No counter running')
                        return -1
                line_counts[0, i] = rawdata.sum() / self._counting_samples

        return line_counts.transpose()

    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        self._counter.close_counter()
        self._atto_scanner_hw.disable_outputs()
        return 0

    def close_scanner_clock(self):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        self._counter.close_clock()
        return 0

    def single_step(self, axis='x', direction='forward'):
        '''

        :param axis: 'x', 'y' 'z'
        :param direction: 'forward' or 'backward'
        :return:
        '''
        self._atto_scanner_hw.single_step(axis, direction)

    def axis_output_status(self, axis, status='off'):
        self._atto_scanner_hw.axis_output_status(axis, status=status)

    def set_frequency(self, axis, freq):
        '''

        :param axis: 'x', 'y' 'z'
        :param freq: Frequency in Hz, internal resolution is 1 Hz
        :return:
        '''
        self._atto_scanner_hw.set_frequency(axis, freq)

    def set_amplitude(self, axis, amp):
        '''

        :param axis: 'x', 'y' 'z'
        :param amp: Amplitude in V, internal resolution is 1 mV
        :return:
        '''
        self._atto_scanner_hw.set_amplitude(axis, amp)

    def get_frequency(self, axis):
        '''

        :param axis: 'x', 'y' 'z'
        :param freq: Frequency in Hz, internal resolution is 1 Hz
        :return:
        '''
        return self._atto_scanner_hw.get_frequency(axis)

    def get_amplitude(self, axis):
        '''

        :param axis: 'x', 'y' 'z'
        :param amp: Amplitude in V, internal resolution is 1 mV
        :return:
        '''
        return self._atto_scanner_hw.get_amplitude(axis)




