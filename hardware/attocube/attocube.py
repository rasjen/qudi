# -*- coding: utf-8 -*-

"""
This file contains the Qudi Hardware module NICard class.

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

import numpy as np
from hardware.attocube.pyanc350v4 import Positioner
import ctypes, math, time



from core.base import Base
from interface.confocal_scanner_interface import ConfocalScannerInterface


#class Attocube(Base, ConfocalScannerInterfrt):
class Attocube(Base):

    def on_activate(self, e=None):
        """
        @param object e: Event class object from Fysom.
                         An object created by the state machine module Fysom,
                         which is connected to a specific event (have a look in
                         the Base Class). This object contains the passed event,
                         the state before the event happened and the destination
                         of the state which should be reached after the event
                         had happened.
        """

        self.anc = Positioner()
        self.axisNo = {'y': 0, 'x': 1, 'z': 2}


    def on_deactivate(self, e=None):
        """ Shut down the NI card.

        @param object e: Event class object from Fysom. A more detailed
                         explanation can be found in method activation.
        """
        self.reset_hardware()

    # ================ ConfocalScannerInterface Commands =======================
    def reset_hardware(self):
        """ Resets the NI hardware, so the connection is lost and other
            programs can access it.

        @return int: error code (0:OK, -1:error)
        """
        self.anc.disconnect()
        self.anc.discover()
        self.anc.device = self.anc.connect()

    def axis_output_status(self, label, status):
        '''

        :param label: 'x','y','z'
        :param status: 'on' or 'off'
        :return:
        '''
        if status == 'off':
            self.anc.setAxisOutput(self.axisNo[label], enable=0, autoDisable=True)
        elif status == 'on':
            self.anc.setAxisOutput(self.axisNo[label], enable=1, autoDisable=True)
        else:
            self.log.error('Did non change status of output')

    def enable_outputs(self):
        '''
        Enables output to stages
        :return:
        '''
        for i, label in enumerate(self.get_scanner_axes()):
            self.anc.setAxisOutput(self.axisNo[label], 1, True)

    def disable_outputs(self):
        '''
        disables output to stages
        :return:
        '''
        for i, label in enumerate(self.get_scanner_axes()):
            self.anc.setAxisOutput(self.axisNo[label], 0, True)

    def get_position_range(self):
        """ Returns the physical range of the scanner.

        @return float [4][2]: array of 4 ranges with an array containing lower
                              and upper limit. The unit of the scan range is
                              micrometer.
        """
        self._position_range = [[0,5000],[0,5000],[0,5000],[0,5000]]
        return self._position_range

    def set_position_range(self, myrange=None):
        """ Sets the physical range of the scanner.

        @param float [4][2] myrange: array of 4 ranges with an array containing
                                     lower and upper limit. The unit of the
                                     scan range is micrometer.

        @return int: error code (0:OK, -1:error)
        """
        if myrange is None:
            myrange = [[0, 5000], [0, 5000], [0, 5000], [0, 1]]

        if not isinstance( myrange, (frozenset, list, set, tuple, np.ndarray, ) ):
            self.log.error('Given range is no array type.')
            return -1

        if len(myrange) != 4:
            self.log.error(
                'Given range should have dimension 4, but has {0:d} instead.'
                ''.format(len(myrange)))
            return -1

        for pos in myrange:
            if len(pos) != 2:
                self.log.error(
                    'Given range limit {1:d} should have dimension 2, but has {0:d} instead.'
                    ''.format(len(pos), pos))
                return -1
            if pos[0]>pos[1]:
                self.log.error(
                    'Given range limit {0:d} has the wrong order.'.format(pos))
                return -1

        self._position_range = myrange
        return 0

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
        try:
            for i in range(3):
                if not self.anc.getAxisStatus(i)[0] == 1:
                    break
            return ['y', 'x', 'z']
        except:
            self.log.error(
            'Axis status is wrong'
            )
            return -1

    def scanner_set_position_abs(self, x=None, y=None, z=None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        #FIXME: No volts
        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)
        @param float a: postion in a-direction (volts)

        @return int: error code (0:OK, -1:error)
        """
        self._current_position_abs = [0,0,0]
        if self.getState() == 'locked':
            self.log.error('Another scan_line is already running, close this one first.')
            return -1

        if x is not None:
            if not(self._position_range[0][0] <= x <= self._position_range[0][1]):
                self.log.error('You want to set x out of range: {0:f}.'.format(x))
                return -1
            self._current_position_abs[0] = np.float(x)

        if y is not None:
            if not(self._position_range[1][0] <= y <= self._position_range[1][1]):
                self.log.error('You want to set y out of range: {0:f}.'.format(y))
                return -1
            self._current_position_abs[1] = np.float(y)

        if z is not None:
            if not(self._position_range[2][0] <= z <= self._position_range[2][1]):
                self.log.error('You want to set z out of range: {0:f}.'.format(z))
                return -1
            self._current_position_abs[2] = np.float(z)

        try:
            for i, label in enumerate(self.get_scanner_axes()):
                self._current_position_abs[i] = self.set_target_position(self.axisNo[label], self._current_position_abs[i])
                self.auto_move(label, 1)
        except:
            return -1
        return 0

    def get_scanner_position_abs(self):
        """ Get the current position of the scanner hardware.

        @return float[]: current position in (x, y, z, a).
        """
        self._current_position_abs = [0, 0, 0]
        for i, label in enumerate(self.get_scanner_axes()):
            self._current_position_abs[i] = self.anc.getPosition(self.axisNo[label])
        return self._current_position_abs

    def single_step(self, axis, direction):
        """
        Enables outputs and makes a single scan and then en

        :param str axis: 'x', 'y' 'z'
        :param str direction: 'forward' or 'backward'
        :return:
        """
        try:
            axes = self.axisNo[axis]
        except:
            self.log.error('input should be x,y or z in string format')
        if direction == 'forward':
            dir = True
        elif direction == 'backward':
            dir = False
        else:
            self.log.error('direction must be forward or backward')

        self.anc.startSingleStep(axes, backward=dir)

    def set_frequency(self, axis, freq):
        '''

        :param axis: 'x', 'y' 'z'
        :param freq: Frequency in Hz, internal resolution is 1 Hz
        :return:
        '''

        axes = self.axisNo[axis]
        self.anc.setFrequency(axes, freq)

    def set_amplitude(self, axis, amp):
        '''

        :param axis: 'x', 'y' 'z'
        :param amp: Amplitude in V, internal resolution is 1 mV
        :return:
        '''

        axes = self.axisNo[axis]
        self.anc.setAmplitude(axes, amp)

    def set_dcvoltage(self, axis, voltage):
        '''

        :param axis: 'x', 'y' 'z'
        :param voltage: DC output voltage [V], internal resolution is 1 mV
        :return:
        '''

        axes = self.axisNo[axis]
        self.anc.setDcVoltage(axes, voltage)

    def get_frequency(self, axis, freq):
        '''

        :param axis: 'x', 'y' 'z'
        :return: Frequency in Hz
        '''

        axes = self.axisNo[axis]
        return self.anc.getFrequency(axes, freq)

    def get_amplitude(self, axis, amp):
        '''

        :param axis: 'x', 'y' 'z'
        :return: Amplitude V
        '''

        axes = self.axisNo[axis]
        return self.anc.getAmplitude(axes)

    def enable_trigger_input(self):
        '''
        Enables trigger mode for all axis
        :return:
        '''
        for i, label in enumerate(self.get_scanner_axes()):
            self.anc.configureExtTrigger(self.axisNo[label], 2)



    def set_target_position(self, axis, position):
        '''

        @param axis:
        @param position:
        @return:
        '''
        self.anc.setTargetPosition(self.axisNo[axis], position)

    def set_target_range(self, axis, range):
        '''

        @param axis:
        @param range:
        @return:
        '''
        self.anc.setTargetRange(self.axisNo[axis], range)


    def auto_move(self,axis,enable):
        '''

        :param axis: 'x','y','z'
        :param enable: 1 for move and 0 for stop
        :return:
        '''

        self.anc.startAutoMove(self.axisNo[axis],enable=enable,relative=0)


