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
import re

from hardware.attocube.pyanc350v4 import ANC350v4lib as ANC
import ctypes, math, time

import PyDAQmx as daq

from core.base import Base
from interface.slow_counter_interface import SlowCounterInterface
from interface.odmr_counter_interface import ODMRCounterInterface
from interface.confocal_scanner_interface import ConfocalScannerInterface


class Attocube(Base, ConfocalScannerInterface):
   

    _modtype = 'Attocube'
    _modclass = 'hardware'

    # connectors
    _in = {'fitlogic': 'FitLogic'}
    _out = {'confocalscanner': 'ConfocalScannerInterface',
            }

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

        self.anc = ANC.Positioner()
		

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
        retval = 0
        chanlist = (
            self._scanner_ao_channels,
            self._odmr_trigger_channel,
            self._clock_channel,
            self._counter_channel,
            self._counter_channel2,
            self._scanner_clock_channel,
            self._scanner_counter_channel,
            self._photon_source,
            self._photon_source2,
            self._gate_in_channel
            )
        devicelist = []
        for ch in chanlist:
            if ch is None:
                continue
            match = re.match('^/(?P<dev>[0-9A-Za-z\- ]+[0-9A-Za-z\-_ ]*)/(?P<chan>[0-9A-Za-z]+)', ch)
            if match:
                devicelist.append(match.group('dev'))
            else:
                self.log.error('Did not find device name in {0}.'.format(ch))
        for device in set(devicelist):
            self.log.info('Reset device {0}.'.format(device))
            try:
                daq.DAQmxResetDevice(device)
            except:
                self.log.exception('Could not reset NI device {0}'.format(device))
                retval = -1
        return retval

    def get_position_range(self):
        """ Returns the physical range of the scanner.

        @return float [4][2]: array of 4 ranges with an array containing lower
                              and upper limit. The unit of the scan range is
                              micrometer.
        """
        return self._position_range

    def set_position_range(self, myrange=None):
        """ Sets the physical range of the scanner.

        @param float [4][2] myrange: array of 4 ranges with an array containing
                                     lower and upper limit. The unit of the
                                     scan range is micrometer.

        @return int: error code (0:OK, -1:error)
        """
        if myrange is None:
            myrange = [[0, 1], [0, 1], [0, 1], [0, 1]]

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

    def set_voltage_range(self, myrange=None):
        """ Sets the voltage range of the NI Card.

        @param float [2] myrange: array containing lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        if myrange is None:
            myrange = [-10., 10.]

        if not isinstance(myrange, (frozenset, list, set, tuple, np.ndarray, ) ):
            self.log.error('Given range is no array type.')
            return -1

        if len(myrange) != 2:
            self.log.error(
                'Given range should have dimension 2, but has {0:d} instead.'
                ''.format(len(myrange)))
            return -1

        if myrange[0] > myrange[1]:
            self.log.error('Given range limit {0:d} has the wrong order.'.format(myrange))
            return -1

        self._voltage_range = myrange
        return 0

    def _start_analog_output(self):
        """ Starts or restarts the analog output.

        @return int: error code (0:OK, -1:error)
        """
        try:
            # If an analog task is already running, kill that one first
            if self._scanner_ao_task is not None:
                # stop the analog output task
                daq.DAQmxStopTask(self._scanner_ao_task)

                # delete the configuration of the analog output
                daq.DAQmxClearTask(self._scanner_ao_task)

                # set the task handle to None as a safety
                self._scanner_ao_task = None

            # initialize ao channels / task for scanner, should always be active.
            # Define at first the type of the variable as a Task:
            self._scanner_ao_task = daq.TaskHandle()

            # create the actual analog output task on the hardware device. Via
            # byref you pass the pointer of the object to the TaskCreation function:
            daq.DAQmxCreateTask('ScannerAnalogOutput', daq.byref(self._scanner_ao_task))

            # Assign and configure the created task to an analog output voltage channel.
            daq.DAQmxCreateAOVoltageChan(
                # The AO voltage operation function is assigned to this task.
                self._scanner_ao_task,
                # use (all) sanncer ao_channels for the output
                self._scanner_ao_channels,
                # assign a name for that task
                'Analog Control',
                # minimum possible voltage
                self._voltage_range[0],
                # maximum possible voltage
                self._voltage_range[1],
                # units is Volt
                daq.DAQmx_Val_Volts,
                # empty for future use
                '')
        except:
            return -1
        return 0

    def _stop_analog_output(self):
        """ Stops the analog output.

        @return int: error code (0:OK, -1:error)
        """
        if self._scanner_ao_task is None:
            return -1
        retval = 0
        try:
            # stop the analog output task
            daq.DAQmxStopTask(self._scanner_ao_task)
        except:
            self.log.exception('Error stopping analog output.')
            retval = -1
        try:
            daq.DAQmxSetSampTimingType(self._scanner_ao_task, daq.DAQmx_Val_OnDemand)
        except:
            self.log.exception('Error changing analog output mode.')
            retval = -1
        return retval


    def set_up_scanner_clock(self, clock_frequency=None, clock_channel=None):
        """ Configures the hardware clock of the NiDAQ card to give the timing.

        @param float clock_frequency: if defined, this sets the frequency of
                                      the clock
        @param string clock_channel: if defined, this is the physical channel
                                     of the clock

        @return int: error code (0:OK, -1:error)
        """
        # The clock for the scanner is created on the same principle as it is
        # for the counter. Just to keep consistency, this function is a wrapper
        # around the set_up_clock.
        return self.set_up_clock(
            clock_frequency=clock_frequency,
            clock_channel=clock_channel,
            scanner=True)

    def set_up_scanner(self, counter_channel=None, photon_source=None,
                       clock_channel=None, scanner_ao_channels=None):
        """ Configures the actual scanner with a given clock.

        The scanner works pretty much like the counter. Here you connect a
        created clock with a counting task. That can be seen as a gated
        counting, where the counts where sampled by the underlying clock.

        @param string counter_channel: optional, if defined, this is the
                                       physical channel of the counter
        @param string photon_source: optional, if defined, this is the physical
                                     channel where the photons are to count from
        @param string clock_channel: optional, if defined, this specifies the
                                     clock for the counter
        @param string scanner_ao_channels: optional, if defined, this specifies
                                           the analog output channels

        @return int: error code (0:OK, -1:error)
        """
        retval = 0
        if self._scanner_clock_daq_task is None and clock_channel is None:
            self.log.error('No clock running, call set_up_clock before starting the counter.')
            return -1

        if counter_channel is not None:
            self._scanner_counter_channel = counter_channel
        if photon_source is not None:
            self._photon_source = photon_source

        if clock_channel is not None:
            self._my_scanner_clock_channel = clock_channel
        else:
            self._my_scanner_clock_channel = self._scanner_clock_channel

        if scanner_ao_channels is not None:
            self._scanner_ao_channels = scanner_ao_channels
            retval = self._start_analog_output()

        try:
            # Set the Sample Timing Type. Task timing to use a sampling clock:
            # specify how the Data of the selected task is collected, i.e. set it
            # now to be sampled on demand for the analog output, i.e. when
            # demanded by software.
            daq.DAQmxSetSampTimingType(self._scanner_ao_task, daq.DAQmx_Val_OnDemand)

            # create handle for task, this task will do the photon counting for the
            # scanner.
            self._scanner_counter_daq_task = daq.TaskHandle()

            # actually create the scanner counting task
            daq.DAQmxCreateTask('ScannerCounter', daq.byref(self._scanner_counter_daq_task))

            # Create a Counter Input which samples with Semi Perides the Channel.
            # set up semi period width measurement in photon ticks, i.e. the width
            # of each pulse (high and low) generated by pulse_out_task is measured
            # in photon ticks.
            #   (this task creates a channel to measure the time between state
            #    transitions of a digital signal and adds the channel to the task
            #    you choose)
            daq.DAQmxCreateCISemiPeriodChan(
                # The task to which to add the channels
                self._scanner_counter_daq_task,
                # use this counter channel
                self._scanner_counter_channel,
                # name to assing to it
                'Scanner Counter',
                # expected minimum value
                0,
                # Expected maximum count value
                self._max_counts/self._scanner_clock_frequency,
                # units of width measurement, here Timebase photon ticks
                daq.DAQmx_Val_Ticks,
                '')

            # Set the Counter Input to a Semi Period input Terminal.
            # Connect the pulses from the scanner clock to the scanner counter
            daq.DAQmxSetCISemiPeriodTerm(
                # The task to which to add the counter channel.
                self._scanner_counter_daq_task,
                # use this counter channel
                self._scanner_counter_channel,
                # assign a Terminal Name
                self._my_scanner_clock_channel+'InternalOutput')

            # Set a CounterInput Control Timebase Source.
            # Specify the terminal of the timebase which is used for the counter:
            # Define the source of ticks for the counter as self._photon_source for
            # the Scanner Task.
            daq.DAQmxSetCICtrTimebaseSrc(
                # define to which task to# connect this function
                self._scanner_counter_daq_task,
                # counter channel to ouput the# counting results
                self._scanner_counter_channel,
                # which channel to count
                self._photon_source)
        except:
            self.log.exception('Error while setting up scanner.')
            retval = -1

        return retval

    def scanner_set_position(self, x=None, y=None, z=None, a=None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        #FIXME: No volts
        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)
        @param float a: postion in a-direction (volts)

        @return int: error code (0:OK, -1:error)
        """

        if self.getState() == 'locked':
            self.log.error('Another scan_line is already running, close this one first.')
            return -1

        if x is not None:
            if not(self._position_range[0][0] <= x <= self._position_range[0][1]):
                self.log.error('You want to set x out of range: {0:f}.'.format(x))
                return -1
            self._current_position[0] = np.float(x)

        if y is not None:
            if not(self._position_range[1][0] <= y <= self._position_range[1][1]):
                self.log.error('You want to set y out of range: {0:f}.'.format(y))
                return -1
            self._current_position[1] = np.float(y)

        if z is not None:
            if not(self._position_range[2][0] <= z <= self._position_range[2][1]):
                self.log.error('You want to set z out of range: {0:f}.'.format(z))
                return -1
            self._current_position[2] = np.float(z)

        if a is not None:
            if not(self._position_range[3][0] <= a <= self._position_range[3][1]):
                self.log.error('You want to set a out of range: {0:f}.'.format(a))
                return -1
            self._current_position[3] = np.float(a)

        # the position has to be a vstack
        my_position = np.vstack(self._current_position)

        # then directly write the position to the hardware
        try:
            self._write_scanner_ao(voltages=self._scanner_position_to_volt(my_position), start=True)
        except:
            return -1
        return 0

    def _write_scanner_ao(self, voltages, length=1, start=False):
        """Writes a set of voltages to the analog outputs.

        @param float[][4] voltages: array of 4-part tuples defining the voltage
                                    points
        @param int length: number of tuples to write
        @param bool start: write imediately (True)
                           or wait for start of task (False)
        """
        # Number of samples which were actually written, will be stored here.
        # The error code of this variable can be asked with .value to check
        # whether all channels have been written successfully.
        self._AONwritten = daq.int32()

        # write the voltage instructions for the analog output to the hardware
        daq.DAQmxWriteAnalogF64(
            # write to this task
            self._scanner_ao_task,
            # length of the command (points)
            length,
            # start task immediately (True), or wait for software start (False)
            start,
            # maximal timeout in seconds for# the write process
            self._RWTimeout,
            # Specify how the samples are arranged: each pixel is grouped by channel number
            daq.DAQmx_Val_GroupByChannel,
            # the voltages to be written
            voltages,
            # The actual number of samples per channel successfully written to the buffer
            daq.byref(self._AONwritten),
            # Reserved for future use. Pass NULL(here None) to this parameter
            None)
        return self._AONwritten.value

    def _scanner_position_to_volt(self, positions=None):
        """ Converts a set of position pixels to acutal voltages.

        @param float[][4] positions: array of 4-part tuples defining the pixels

        @return float[][4]: array of 4-part tuples of corresponing voltages

        The positions is actually a matrix like
            [[x_values],[y_values],[z_values],[counts]]
        where the count values will be overwritten by the scanning routine.

        """

        if not isinstance(positions, (frozenset, list, set, tuple, np.ndarray, )):
            self.log.error('Given position list is no array type.')
            return np.array([-1., -1., -1., -1.])

        # Calculate the voltages from the positions, their ranges and stack
        # them together:
        volts = np.vstack((
            (self._voltage_range[1]-self._voltage_range[0])
            / (self._position_range[0][1] - self._position_range[0][0])
            * (positions[0] - self._position_range[0][0])
            + self._voltage_range[0],
            (self._voltage_range[1] - self._voltage_range[0])
            / (self._position_range[1][1] - self._position_range[1][0])
            * (positions[1] - self._position_range[1][0])
            + self._voltage_range[0],
            (self._voltage_range[1] - self._voltage_range[0])
            / (self._position_range[2][1] - self._position_range[2][0])
            * (positions[2] - self._position_range[2][0])
            + self._voltage_range[0],
            (self._voltage_range[1] - self._voltage_range[0])
            / (self._position_range[3][1] - self._position_range[3][0])
            * (positions[3] - self._position_range[3][0])
            + self._voltage_range[0]
        ))

        if volts.min() < self._voltage_range[0] or volts.max() > self._voltage_range[1]:
            self.log.error(
                'Voltages {} exceed the limit, the positions have to '
                'be adjusted to stay in the given range.'.format((volts.min(), volts.max())))
            return np.array([-1., -1., -1., -1.])
        return volts

    def get_scanner_position(self):
        """ Get the current position of the scanner hardware.

        @return float[]: current position in (x, y, z, a).
        """
        return self._current_position

    def set_up_line(self, length=100):
        """ Sets up the analog output for scanning a line.

        Connect the timing of the Analog scanning task with the timing of the
        counting task.

        @param int length: length of the line in pixel

        @return int: error code (0:OK, -1:error)
        """
        if self._scanner_counter_daq_task is None:
            self.log.error('No counter is running, cannot scan a line without one.')
            return -1

        self._line_length = length

        try:
           # Just a formal check whether length is not a too huge number
           if length < np.inf:

               # Configure the Sample Clock Timing.
               # Set up the timing of the scanner counting while the voltages are
               # being scanned (i.e. that you go through each voltage, which
               # corresponds to a position. How fast the voltages are being
               # changed is combined with obtaining the counts per voltage peak).
               daq.DAQmxCfgSampClkTiming(
                   # add to this task
                   self._scanner_ao_task,
                   # use this channel as clock
                   self._my_scanner_clock_channel+'InternalOutput',
                   # Maximum expected clock frequency
                   self._scanner_clock_frequency,
                   # Generate sample on falling edge
                   daq.DAQmx_Val_Falling,
                   # generate finite number of samples
                   daq.DAQmx_Val_FiniteSamps,
                   # number of samples to generate
                   self._line_length)

           # Configure Implicit Timing for the clock.
           # Set timing for scanner clock task to the number of pixel.
           daq.DAQmxCfgImplicitTiming(
               # define task
               self._scanner_clock_daq_task,
               # only a limited number of# counts
               daq.DAQmx_Val_FiniteSamps,
               # count twice for each voltage +1 for safety
               self._line_length + 1)

           # Configure Implicit Timing for the scanner counting task.
           # Set timing for scanner count task to the number of pixel.
           daq.DAQmxCfgImplicitTiming(
               # define task
               self._scanner_counter_daq_task,
               # only a limited number of counts
               daq.DAQmx_Val_FiniteSamps,
               # count twice for each voltage +1 for safety
               2 * self._line_length + 1)

           # Set the Read point Relative To an operation.
           # Specifies the point in the buffer at which to begin a read operation,
           # here we read samples from beginning of acquisition and do not overwrite
           daq.DAQmxSetReadRelativeTo(
               # define to which task to connect this function
               self._scanner_counter_daq_task,
               # Start reading samples relative to the last sample returned by the previous read
               daq.DAQmx_Val_CurrReadPos)

           # Set the Read Offset.
           # Specifies an offset in samples per channel at which to begin a read
           # operation. This offset is relative to the location you specify with
           # RelativeTo. Here we do not read the first sample.
           daq.DAQmxSetReadOffset(
               # connect to this taks
               self._scanner_counter_daq_task,
               # Offset after which to read
               1)

           # Set Read OverWrite Mode.
           # Specifies whether to overwrite samples in the buffer that you have
           # not yet read. Unread data in buffer will be overwritten:
           daq.DAQmxSetReadOverWrite(
               self._scanner_counter_daq_task,
               daq.DAQmx_Val_DoNotOverwriteUnreadSamps)
        except:
            self.log.exception('Error while setting up scanner to scan a line.')
            return -1
        return 0

    def scan_line(self, line_path=None):
        """ Scans a line and return the counts on that line.

        @param float[][4] line_path: array of 4-part tuples defining the
                                    voltage points

        @return float[]: the photon counts per second

        The input array looks for a xy scan of 5x5 points at the position z=-2
        like the following:
            [ [1,2,3,4,5],[1,1,1,1,],[-2,-2,-2,-2],[0,0,0,0]]
        """
        if self._scanner_counter_daq_task is None:
            self.log.error('No counter is running, cannot scan a line without one.')
            return np.array([-1.])

        if not isinstance(line_path, (frozenset, list, set, tuple, np.ndarray, ) ):
            self.log.error('Given line_path list is not array type.')
            return np.array([-1.])
        try:
            # set task timing to use a sampling clock:
            # specify how the Data of the selected task is collected, i.e. set it
            # now to be sampled by a hardware (clock) signal.
            daq.DAQmxSetSampTimingType(self._scanner_ao_task, daq.DAQmx_Val_SampClk)

            self.set_up_line(np.shape(line_path)[1])

            # write the positions to the analog output
            written_voltages = self._write_scanner_ao(
                voltages=self._scanner_position_to_volt(line_path),
                length=self._line_length,
                start=False)

            # start the timed analog output task
            daq.DAQmxStartTask(self._scanner_ao_task)

            daq.DAQmxStopTask(self._scanner_counter_daq_task)
            daq.DAQmxStopTask(self._scanner_clock_daq_task)

            # start the scanner counting task that acquires counts synchroneously
            daq.DAQmxStartTask(self._scanner_counter_daq_task)
            daq.DAQmxStartTask(self._scanner_clock_daq_task)

            # wait for the scanner counter to finish
            daq.DAQmxWaitUntilTaskDone(
                # define task
                    self._scanner_counter_daq_task,
                # Maximum timeout for the counter times the positions. Unit is seconds.
                    self._RWTimeout * 2 * self._line_length)

            # wait for the scanner clock to finish
            daq.DAQmxWaitUntilTaskDone(
                # define task
                self._scanner_clock_daq_task,
                # maximal timeout for the counter times the positions
                self._RWTimeout * 2 * self._line_length)

            # count data will be written here
            self._scan_data = np.empty((2*self._line_length,), dtype=np.uint32)

            # number of samples which were read will be stored here
            n_read_samples = daq.int32()

            # actually read the counted photons
            daq.DAQmxReadCounterU32(
                # read from this task
                self._scanner_counter_daq_task,
                # read number of double the # number of samples
                2 * self._line_length,
                # maximal timeout for the read# process
                self._RWTimeout,
                # write into this array
                self._scan_data,
                # length of array to write into
                2 * self._line_length,
                # number of samples which were actually read
                daq.byref(n_read_samples),
                # Reserved for future use. Pass NULL(here None) to this parameter.
                None)

            # stop the counter task
            daq.DAQmxStopTask(self._scanner_counter_daq_task)
            daq.DAQmxStopTask(self._scanner_clock_daq_task)

            # stop the analog output task
            self._stop_analog_output()

            # create a new array for the final data (this time of the length
            # number of samples):
            self._real_data = np.empty((self._line_length,), dtype=np.uint32)

            # add upp adjoint pixels to also get the counts from the low time of
            # the clock:
            self._real_data = self._scan_data[::2]
            self._real_data += self._scan_data[1::2]

            # update the scanner position instance variable
            self._current_position = list(line_path[:,-1])
        except:
            self.log.exception('Error while scanning line.')
            return np.array([-1.])

        return self._real_data*(self._scanner_clock_frequency)

    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        a = self._stop_analog_output()
        c = self.close_counter(scanner=True)
        return -1 if a < 0 or c < 0 else 0

    def close_scanner_clock(self):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        return self.close_clock(scanner=True)

    # ================ End ConfocalScannerInterface Commands ===================


