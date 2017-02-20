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

# from hardware.attocube.pyanc350v4 import ANC350v4lib as ANC
from hardware.attocube.pyanc350v4 import Positioner
import ctypes, math, time

import PyDAQmx as daq

from core.base import Base
from interface.confocal_scanner_atto_interface import ConfocalScannerInterfaceAtto


class NIcard(Base):

    _modtype = 'Nicard'
    _modclass = 'hardware'


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

        ''' NI card '''
        # the tasks used on that hardware device:
        self._counter_daq_tasks = []
        self._clock_daq_task = None
        self._scanner_clock_daq_task = None
        self._scanner_do_task = None
        self._scanner_counter_daq_tasks = []
        self._line_length = None
        self._odmr_length = None
        self._gated_counter_daq_task = None

        # used as a default for expected maximum counts
        self._max_counts = 3e7
        # timeout for the Read or/and write process in s
        self._RWTimeout = 10

        self._clock_frequency_default = 100  # in Hz
        self._scanner_clock_frequency_default = 100  # in Hz
        # number of readout samples, mainly used for gated counter
        self._samples_number_default = 50

        config = self.getConfiguration()

        self._scanner_do_channels = []
        self._voltage_range = []
        self._position_range = []
        self._current_position = [0, 0, 0]
        self._counter_channels = []
        self._scanner_counter_channels = []
        self._photon_sources = []

        self._scanner_do_channels.append(config['scanner_do_channels'])
        # self._scanner_do_channels.append(config['scanner_do_channels2'])
        # handle all the parameters given by the config
        if 'scanner_x_do' in config.keys():
            self._scanner_do_channels.append(config['scanner_x_do'])
            self._current_position.append(0)
            self._position_range.append([0., 100.])
            self._voltage_range.append([-10., 10.])
            if 'scanner_y_do' in config.keys():
                self._scanner_do_channels.append(config['scanner_y_do'])
                self._current_position.append(0)
                self._position_range.append([0., 100.])
                self._voltage_range.append([-10., 10.])
                if 'scanner_z_do' in config.keys():
                    self._scanner_do_channels.append(config['scanner_z_do'])
                    self._current_position.append(0)
                    self._position_range.append([0., 100.])
                    self._voltage_range.append([-10., 10.])
                    if 'scanner_a_ao' in config.keys():
                        self._scanner_do_channels.append(config['scanner_a_do'])
                        self._current_position.append(0)
                        self._position_range.append([0., 100.])
                        self._voltage_range.append([-10., 10.])

                        #        if len(self._scanner_ao_channels) < 1:
                        #            self.log.error(
                        #                'Not enough scanner channels found in the configuration!\n'
                        #                'Be sure to start with scanner_x_ao\n'
                        #                'Assign to that parameter an appropriate channel from your NI Card, '
                        #                'otherwise you cannot control the analog channels!')

        if 'odmr_trigger_channel' in config.keys():
            self._odmr_trigger_channel = config['odmr_trigger_channel']
        else:
            self.log.error(
                'No parameter "odmr_trigger_channel" found in configuration!\n'
                'Assign to that parameter an appropriate channel from your NI Card!')

        if 'clock_channel' in config.keys():
            self._clock_channel = config['clock_channel']
        else:
            self.log.error(
                'No parameter "clock_channel" configured.'
                'Assign to that parameter an appropriate channel from your NI Card!')

        if 'photon_source' in config.keys():
            self._photon_sources.append(config['photon_source'])
            n = 2
            while 'photon_source{0}'.format(n) in config.keys():
                self._photon_sources.append(config['photon_source{0}'.format(n)])
                n += 1
        else:
            self.log.error(
                'No parameter "photon_source" configured.\n'
                'Assign to that parameter an appropriated channel from your NI Card!')

        if 'counter_channel' in config.keys():
            self._counter_channels.append(config['counter_channel'])
            n = 2
            while 'counter_channel{0}'.format(n) in config.keys():
                self._counter_channels.append(config['counter_channel{0}'.format(n)])
                n += 1
        else:
            self.log.error(
                'No parameter "counter_channel" configured.\n'
                'Assign to that parameter an appropriate channel from your NI Card!')

        if 'scanner_counter_channel' in config.keys():
            self._scanner_counter_channels.append(config['scanner_counter_channel'])
            n = 2
            while 'scanner_counter_channel{0}'.format(n) in config.keys():
                self._scanner_counter_channels.append(
                    config['scanner_counter_channel{0}'.format(n)])
                n += 1
        else:
            self.log.error(
                'No parameter "scanner_counter_channel" configured.\n'
                'Assign to that parameter an appropriate channel from your NI Card!')

        if 'scanner_clock_channel' in config.keys():
            self._scanner_clock_channel = config['scanner_clock_channel']
        else:
            self.log.error(
                'No parameter "scanner_clock_channel" configured.\n'
                'Assign to that parameter an appropriate channel from your NI Card!')

        if 'clock_frequency' in config.keys():
            self._clock_frequency = config['clock_frequency']
        else:
            self._clock_frequency = self._clock_frequency_default
            self.log.warning(
                'No clock_frequency configured, taking 100 Hz instead.')

        if 'gate_in_channel' in config.keys():
            self._gate_in_channel = config['gate_in_channel']
        else:
            self.log.error(
                'No parameter "gate_in_channel" configured.\n'
                'Choose the proper channel on your NI Card and assign it to that parameter!')

        if 'counting_edge_rising' in config.keys():
            if config['counting_edge_rising']:
                self._counting_edge = daq.DAQmx_Val_Rising
            else:
                self._counting_edge = daq.DAQmx_Val_Falling
        else:
            self.log.warning(
                'No parameter "counting_edge_rising" configured.\n'
                'Set this parameter either to True (rising edge) or to False (falling edge).\n'
                'Taking the default value {0}'.format(self._counting_edge_default))
            self._counting_edge = self._counting_edge_default

        if 'scanner_clock_frequency' in config.keys():
            self._scanner_clock_frequency = config['scanner_clock_frequency']
        else:
            self._scanner_clock_frequency = self._scanner_clock_frequency_default
            self.log.warning(
                'No scanner_clock_frequency configured, taking 100 Hz instead.')

        if 'samples_number' in config.keys():
            self._samples_number = config['samples_number']
        else:
            self._samples_number = self._samples_number_default
            self.log.warning(
                'No parameter "samples_number" configured taking the default value "{0}" instead.'
                ''.format(self._samples_number_default))
            self._samples_number = self._samples_number_default

        if 'x_range' in config.keys() and len(self._position_range) > 0:
            if float(config['x_range'][0]) < float(config['x_range'][1]):
                self._position_range[0] = [float(config['x_range'][0]),
                                           float(config['x_range'][1])]
            else:
                self.log.warning(
                    'Configuration ({}) of x_range incorrect, taking [0,100] instead.'
                    ''.format(config['x_range']))
        else:
            if len(self._position_range) > 0:
                self.log.warning('No x_range configured taking [0,100] instead.')

        if 'y_range' in config.keys() and len(self._position_range) > 1:
            if float(config['y_range'][0]) < float(config['y_range'][1]):
                self._position_range[1] = [float(config['y_range'][0]),
                                           float(config['y_range'][1])]
            else:
                self.log.warning(
                    'Configuration ({}) of y_range incorrect, taking [0,100] instead.'
                    ''.format(config['y_range']))
        else:
            if len(self._position_range) > 1:
                self.log.warning('No y_range configured taking [0,100] instead.')

        if 'z_range' in config.keys() and len(self._position_range) > 2:
            if float(config['z_range'][0]) < float(config['z_range'][1]):
                self._position_range[2] = [float(config['z_range'][0]),
                                           float(config['z_range'][1])]
            else:
                self.log.warning(
                    'Configuration ({}) of z_range incorrect, taking [0,100] instead.'
                    ''.format(config['z_range']))
        else:
            if len(self._position_range) > 2:
                self.log.warning('No z_range configured taking [0,100] instead.')

        if 'a_range' in config.keys() and len(self._position_range) > 3:
            if float(config['a_range'][0]) < float(config['a_range'][1]):
                self._position_range[3] = [float(config['a_range'][0]),
                                           float(config['a_range'][1])]
            else:
                self.log.warning(
                    'Configuration ({}) of a_range incorrect, taking [0,100] instead.'
                    ''.format(config['a_range']))
        else:
            if len(self._position_range) > 3:
                self.log.warning('No a_range configured taking [0,100] instead.')

                #        if 'voltage_range' in config.keys():
                #            if float(config['voltage_range'][0]) < float(config['voltage_range'][1]):
                #                vlow = float(config['voltage_range'][0])
                #                vhigh = float(config['voltage_range'][1])
                #                self._voltage_range = [
                #                    [vlow, vhigh], [vlow, vhigh], [vlow, vhigh], [vlow, vhigh]
                #                    ][0:len(self._voltage_range)]
                #            else:
                #                self.log.warning(
                #                    'Configuration ({}) of voltage_range incorrect, taking [-10,10] instead.'
                #                    ''.format(config['voltage_range']))
                #        else:
                #            self.log.warning('No voltage_range configured, taking [-10,10] instead.')

        if 'x_voltage_range' in config.keys() and len(self._voltage_range) > 0:
            if float(config['x_voltage_range'][0]) < float(config['x_voltage_range'][1]):
                vlow = float(config['x_voltage_range'][0])
                vhigh = float(config['x_voltage_range'][1])
                self._voltage_range[0] = [vlow, vhigh]
            else:
                self.log.warning(
                    'Configuration ({0}) of x_voltage_range incorrect, taking [-10, 10] instead.'
                    ''.format(config['x_voltage_range']))
        else:
            if 'voltage_range' not in config.keys():
                self.log.warning('No x_voltage_range configured, taking [-10, 10] instead.')

        if 'y_voltage_range' in config.keys() and len(self._voltage_range) > 1:
            if float(config['y_voltage_range'][0]) < float(config['y_voltage_range'][1]):
                vlow = float(config['y_voltage_range'][0])
                vhigh = float(config['y_voltage_range'][1])
                self._voltage_range[1] = [vlow, vhigh]
            else:
                self.log.warning(
                    'Configuration ({0}) of y_voltage_range incorrect, taking [-10, 10] instead.'
                    ''.format(config['y_voltage_range']))
        else:
            if 'voltage_range' not in config.keys():
                self.log.warning('No y_voltage_range configured, taking [-10, 10] instead.')

        if 'z_voltage_range' in config.keys() and len(self._voltage_range) > 2:
            if float(config['z_voltage_range'][0]) < float(config['z_voltage_range'][1]):
                vlow = float(config['z_voltage_range'][0])
                vhigh = float(config['z_voltage_range'][1])
                self._voltage_range[2] = [vlow, vhigh]
            else:
                self.log.warning(
                    'Configuration ({0}) of z_voltage_range incorrect, taking [-10, 10] instead.'
                    ''.format(config['z_voltage_range']))
        else:
            if 'voltage_range' not in config.keys():
                self.log.warning('No z_voltage_range configured, taking [-10, 10] instead.')

        if 'a_voltage_range' in config.keys() and len(self._voltage_range) > 3:
            if float(config['a_voltage_range'][0]) < float(config['a_voltage_range'][1]):
                vlow = float(config['a_voltage_range'][0])
                vhigh = float(config['a_voltage_range'][1])
                self._voltage_range[3] = [vlow, vhigh]
            else:
                self.log.warning(
                    'Configuration ({0}) of a_voltage_range incorrect, taking [-10, 10] instead.'
                    ''.format(config['a_voltage_range']))
        else:
            if 'voltage_range' not in config.keys():
                self.log.warning('No a_voltage_range configured taking [-10, 10] instead.')

                # Analog output is always needed and it does not interfere with the
                # rest, so start it always and leave it running
                #        if self._start_analog_output() < 0:
                #            self.log.error('Failed to start analog output.')
                #            raise Exception('Failed to start NI Card module due to analog output failure.')

    def on_deactivate(self, e=None):
        """ Shut down the NI card.

        @param object e: Event class object from Fysom. A more detailed
                         explanation can be found in method activation.
        """
        self.reset_hardware()

        pass

    # ================ ConfocalScannerInterface Commands =======================

    def reset_hardware(self):
        """ Resets the NI hardware, so the connection is lost and other
            programs can access it.

        @return int: error code (0:OK, -1:error)
        """

        '''  NI card '''

        self.close_scanner_clock()
        self._stop_digital_output()

        retval = 0
        chanlist = [
            self._odmr_trigger_channel,
            self._clock_channel,
            self._scanner_clock_channel,
            self._gate_in_channel
        ]
        chanlist.extend(self._scanner_do_channels)
        chanlist.extend(self._photon_sources)
        chanlist.extend(self._counter_channels)
        chanlist.extend(self._scanner_counter_channels)

        devicelist = []
        for channel in chanlist:
            if channel is None:
                continue
            match = re.match(
                '^/(?P<dev>[0-9A-Za-z\- ]+[0-9A-Za-z\-_ ]*)/(?P<chan>[0-9A-Za-z]+)',
                channel)
            if match:
                devicelist.append(match.group('dev'))
            else:
                self.log.error('Did not find device name in {0}.'.format(channel))
        for device in set(devicelist):
            self.log.info('Reset device {0}.'.format(device))
            try:
                daq.DAQmxResetDevice(device)
            except:
                self.log.exception('Could not reset NI device {0}'.format(device))
                retval = -1
        return retval

    def get_scanner_count_channels(self):
        """ Return list of counter channels """
        return self._scanner_counter_channels

    def get_constraints(self):
        """ Get hardware limits of NI device.

        @return SlowCounterConstraints: constraints class for slow counter

        FIXME: ask hardware for limits when module is loaded
        """
        constraints = SlowCounterConstraints()
        constraints.max_detectors = 4
        constraints.min_count_frequency = 1e-3
        constraints.max_count_frequency = 10e9
        constraints.counting_mode = [CountingMode.CONTINUOUS]
        return constraints

    def set_up_clock(self, clock_frequency=None, clock_channel=None, scanner=False, idle=False):
        """ Configures the hardware clock of the NiDAQ card to give the timing.

        @param float clock_frequency: if defined, this sets the frequency of
                                      the clock in Hz
        @param string clock_channel: if defined, this is the physical channel
                                     of the clock within the NI card.
        @param bool scanner: if set to True method will set up a clock function
                             for the scanner, otherwise a clock function for a
                             counter will be set.
        @param bool idle: set whether idle situation of the counter (where
                          counter is doing nothing) is defined as
                                True  = 'Voltage High/Rising Edge'
                                False = 'Voltage Low/Falling Edge'

        @return int: error code (0:OK, -1:error)
        """
        self.log.info('runs set up clock')
        if not scanner and self._clock_daq_task is not None:
            self.log.error('Another counter clock is already running, close this one first.')
            return -1

        if scanner and self._scanner_clock_daq_task is not None:
            self.log.error('Another scanner clock is already running, close this one first.')
            return -1

        # Create handle for task, this task will generate pulse signal for
        # photon counting
        my_clock_daq_task = daq.TaskHandle()

        # assign the clock frequency, if given
        if clock_frequency is not None:
            if not scanner:
                self._clock_frequency = float(clock_frequency)
            else:
                self._scanner_clock_frequency = float(clock_frequency)

        # use the correct clock in this method
        if scanner:
            my_clock_frequency = self._scanner_clock_frequency * 2
        else:
            my_clock_frequency = self._clock_frequency

        # assign the clock channel, if given
        if clock_channel is not None:
            if not scanner:
                self._clock_channel = clock_channel
            else:
                self._scanner_clock_channel = clock_channel

        # use the correct clock channel in this method
        if scanner:
            my_clock_channel = self._scanner_clock_channel
        else:
            my_clock_channel = self._clock_channel

        # check whether only one clock pair is available, since some NI cards
        # only one clock channel pair.
        if self._scanner_clock_channel == self._clock_channel:
            if not ((self._clock_daq_task is None) and (self._scanner_clock_daq_task is None)):
                self.log.error(
                    'Only one clock channel is available!\n'
                    'Another clock is already running, close this one first '
                    'in order to use it for your purpose!')
                return -1

        # Adjust the idle state if necessary
        my_idle = daq.DAQmx_Val_High if idle else daq.DAQmx_Val_Low
        try:
            # create task for clock
            task_name = 'ScannerClock' if scanner else 'CounterClock'
            daq.DAQmxCreateTask(task_name, daq.byref(my_clock_daq_task))

            # create a digital clock channel with specific clock frequency:
            daq.DAQmxCreateCOPulseChanFreq(
                # The task to which to add the channels
                my_clock_daq_task,
                # which channel is used?
                my_clock_channel,
                # Name to assign to task (NIDAQ uses by # default the physical channel name as
                # the virtual channel name. If name is specified, then you must use the name
                # when you refer to that channel in other NIDAQ functions)
                'Clock Producer',
                # units, Hertz in our case
                daq.DAQmx_Val_Hz,
                # idle state
                my_idle,
                # initial delay
                0,
                # pulse frequency, divide by 2 such that length of semi period = count_interval
                my_clock_frequency / 2,
                # duty cycle of pulses, 0.5 such that high and low duration are both
                # equal to count_interval
                0.5)

            # Configure Implicit Timing.
            # Set timing to continuous, i.e. set only the number of samples to
            # acquire or generate without specifying timing:
            daq.DAQmxCfgImplicitTiming(
                # Define task
                my_clock_daq_task,
                # Sample Mode: set the task to generate a continuous amount of running samples
                daq.DAQmx_Val_ContSamps,
                # buffer length which stores temporarily the number of generated samples
                1000)

            if scanner:
                self._scanner_clock_daq_task = my_clock_daq_task
            else:
                # actually start the preconfigured clock task
                daq.DAQmxStartTask(my_clock_daq_task)
                self._clock_daq_task = my_clock_daq_task
        except:
            self.log.exception('Error while setting up clock.')
            return -1
        return 0

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

    def _start_digital_output(self):
        """ Starts or restarts the analog output.

        @return int: error code (0:OK, -1:error)
        """
        self.log.info('start digital output')
        try:
            # If an analog task is already running, kill that one first
            if self._scanner_do_task is not None:
                # stop the analog output task
                daq.DAQmxStopTask(self._scanner_do_task)

                # delete the configuration of the analog output
                daq.DAQmxClearTask(self._scanner_do_task)

                # set the task handle to None as a safety
                self._scanner_do_task = None

            # initialize ao channels / task for scanner, should always be active.
            # Define at first the type of the variable as a Task:
            self._scanner_do_task = daq.TaskHandle()

            # create the actual analog output task on the hardware device. Via
            # byref you pass the pointer of the object to the TaskCreation function:
            daq.DAQmxCreateTask('ScannerDigO', daq.byref(self._scanner_do_task))

            # ChannelAB = [0,0]

            for n, counter in enumerate(self._scanner_do_channels):
                # Assign and configure the created task to an analog output voltage channel.
                # daq.DAQmxCreateCOPulseChanTime(
                daq.DAQmxCreateDOChan(
                    # The AO voltage operation function is assigned to this task.
                    self._scanner_do_task,
                    # use (all) scanner ao_channels for the output
                    counter,
                    # assign a name for that channel
                    'Scanner DO Channel {0}'.format(n),
                    # TERMINAL
                    daq.DAQmx_Val_ChanForAllLines
                    # Units
                    # daq.DAQmx_Val_Seconds,
                    # idle state
                    # daq.DAQmx_Val_Low,
                    # delay
                    # ChannelAB[n], 20, 20
                    # low time
                    # 60*1e-9,
                    # high time
                    # 60*1e-9
                )


        except:
            self.log.exception('Error starting digital output task.')
            return -1
        return 0

    def _stop_digital_output(self):
        """ Stops the analog output.

        @return int: error code (0:OK, -1:error)
        """
        self.log.info('runs stop digital output')
        if self._scanner_do_task is None:
            self.log.info(self._scanner_do_task)
            return -1
        retval = 0
        try:
            # stop the analog output task
            daq.DAQmxStopTask(self._scanner_do_task)
        except:
            self.log.exception('Error stopping digital output.')
            retval = -1
        try:
            daq.DAQmxSetSampTimingType(self._scanner_do_task, daq.DAQmx_Val_OnDemand)
        except:
            self.log.exception('Error changing analog output mode.')
            retval = -1
        return retval

    def set_up_scanner(self, counter_channels=None, sources=None,
                       clock_channel=None, scanner_do_channels=None):
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
        self.log.info('sets up scanner')
        retval = 0
        if self._scanner_clock_daq_task is None and clock_channel is None:
            self.log.error('No clock running, call set_up_clock before starting the counter.')
            return -1

        if counter_channels is not None:
            my_counter_channels = counter_channels
        else:
            my_counter_channels = self._scanner_counter_channels
        if sources is not None:
            my_photon_sources = sources
        else:
            my_photon_sources = self._photon_sources

        if clock_channel is not None:
            self._my_scanner_clock_channel = clock_channel
        else:
            self._my_scanner_clock_channel = self._scanner_clock_channel

        if scanner_do_channels is not None:
            self._scanner_do_channels = scanner_do_channels
            retval = self._start_digital_output()

        if len(my_photon_sources) < len(my_counter_channels):
            self.log.error('You have given {0} sources but {1} counting channels.'
                           'Please give an equal or greater number of sources.'
                           ''.format(len(my_photon_sources), len(my_counter_channels)))
            return -1
        self._start_digital_output()

        try:
            # Set the Sample Timing Type. Task timing to use a sampling clock:
            # specify how the Data of the selected task is collected, i.e. set it
            # now to be sampled on demand for the analog output, i.e. when
            # demanded by software.
            daq.DAQmxSetSampTimingType(self._scanner_do_task, daq.DAQmx_Val_OnDemand)

            for i, ch in enumerate(my_counter_channels):
                # create handle for task, this task will do the photon counting for the
                # scanner.
                task = daq.TaskHandle()

                # actually create the scanner counting task
                daq.DAQmxCreateTask('ScannerCounter{0}'.format(i), daq.byref(task))

                # Create a Counter Input which samples with Semi Perides the Channel.
                # set up semi period width measurement in photon ticks, i.e. the width
                # of each pulse (high and low) generated by pulse_out_task is measured
                # in photon ticks.
                #   (this task creates a channel to measure the time between state
                #    transitions of a digital signal and adds the channel to the task
                #    you choose)
                daq.DAQmxCreateCISemiPeriodChan(
                    # The task to which to add the channels
                    task,
                    # use this counter channel
                    ch,
                    # name to assign to it
                    'Scanner Counter Channel {0}'.format(i),
                    # expected minimum value
                    0,
                    # Expected maximum count value
                    self._max_counts / self._scanner_clock_frequency,
                    # units of width measurement, here Timebase photon ticks
                    daq.DAQmx_Val_Ticks,
                    '')

                # Set the Counter Input to a Semi Period input Terminal.
                # Connect the pulses from the scanner clock to the scanner counter
                daq.DAQmxSetCISemiPeriodTerm(
                    # The task to which to add the counter channel.
                    task,
                    # use this counter channel
                    ch,
                    # assign a Terminal Name
                    self._my_scanner_clock_channel + 'InternalOutput')

                # Set a CounterInput Control Timebase Source.
                # Specify the terminal of the timebase which is used for the counter:
                # Define the source of ticks for the counter as self._photon_source for
                # the Scanner Task.
                daq.DAQmxSetCICtrTimebaseSrc(
                    # define to which task to# connect this function
                    task,
                    # counter channel to output the# counting results
                    ch,
                    # which channel to count
                    my_photon_sources[i])
                self._scanner_counter_daq_tasks.append(task)
        except:
            self.log.exception('Error while setting up scanner.')
            retval = -1

        return retval

    def _write_scanner_do(self, step_data, length, start=False):
        """Writes a set of voltages to the analog outputs.

        @param float[][4] voltages: array of 4-part tuples defining the voltage
                                    points
        @param int length: number of tuples to write
        @param bool start: write imediately (True)
                           or wait for start of task (False)
        """
        self.log.info('runs write scanner do')
        # Number of samples which were actually written, will be stored here.
        # The error code of this variable can be asked with .value to check
        # whether all channels have been written successfully.
        daq.DAQmxCfgOutputBuffer(self._scanner_do_task, length)

        self.log.info(step_data)
        # write the voltage instructions for the analog output to the hardware
        daq.DAQmxWriteDigitalLines(
            # write to this task
            self._scanner_do_task,
            # length of the command (points)
            length,
            # start task immediately (True), or wait for software start (False)
            start,
            # maximal timeout in seconds for# the write process
            self._RWTimeout,
            # Specify how the samples are arranged: each pixel is grouped by channel number
            daq.DAQmx_Val_GroupByChannel,
            # the voltages to be written
            step_data,
            # The actual number of samples per channel successfully written to the buffer
            # daq.byref(self._AONwritten),
            None,
            None)

        return 0

    def _scanner_position_to_step(self, line_path):
        '''
        Translate the position in a trigger array for the NI card

        :param line_path: [[x values][y values][z values]]
        :return: binary step data array for writing to NI card in uint8 type
        '''
        step_data = np.zeros((2 * np.shape(line_path)[1], len(self._scanner_do_channels)), dtype=np.uint8)

        step_size = line_path[0][1]-line_path[0][0]  # micron determined by voltage and freq of motors

        if len(self._scanner_do_channels) > 0:
            x_values = [self._current_position[0]] + line_path[0]
            index_x_forward = np.where(np.diff(x_values) == step_size)[0]
            index_x_backward = np.where(np.diff(x_values) == -step_size)[0]

        if len(self._scanner_do_channels) > 2:
            y_values = [self._current_position[1]] + line_path[1]
            index_y_forward = np.where(np.diff(y_values) == step_size)[0]
            index_y_backward = np.where(np.diff(y_values) == -step_size)[0]

        if len(self._scanner_do_channels) > 4:
            z_values = [self._current_position[2]] + line_path[2]
            index_z_forward = np.where(np.diff(z_values) == step_size)[0]
            index_z_backward = np.where(np.diff(z_values) == -step_size)[0]

        # if not len(index_x_forward) + len(index_x_backward)+ len(index_y_forward) + len(index_y_backward) + \
        #         len(index_z_forward) + len(index_z_backward) +1 == np.shape(line_path)[1]:
        #     self.log.error('Number of steps does not match the number of points in image (moving multiple axis at same time) (different step size)')

        if len(self._scanner_do_channels) > 0:
            # forward x motion
            step_data[2 * index_x_forward, 0] = 1
            # backward x motion
            step_data[2 * index_x_backward, 1] = 1
        if len(self._scanner_do_channels) > 2:
            # forward y motion
            step_data[2 * index_y_forward, 2] = 1
            # backward y motion
            step_data[2 * index_y_backward, 3] = 1
        if len(self._scanner_do_channels) > 4:
            # forward z motion
            step_data[2 * index_z_forward, 4] = 1
            # backward z motion
            step_data[2 * index_z_backward, 5] = 1

        return step_data

    def set_up_line(self, length=100):
        """ Sets up the analog output for scanning a line.

        Connect the timing of the Analog scanning task with the timing of the
        counting task.

        @param int length: length of the line in pixel

        @return int: error code (0:OK, -1:error)
        """
        self.log.info('set up line')
        if len(self._scanner_counter_daq_tasks) < 1:
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
                    self._scanner_do_task,
                    # use this channel as clock
                    self._my_scanner_clock_channel + 'InternalOutput',
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

            for i, task in enumerate(self._scanner_counter_daq_tasks):
                # Configure Implicit Timing for the scanner counting task.
                # Set timing for scanner count task to the number of pixel.
                daq.DAQmxCfgImplicitTiming(
                    # define task
                    task,
                    # only a limited number of counts
                    daq.DAQmx_Val_FiniteSamps,
                    # count twice for each voltage +1 for safety
                    2 * self._line_length + 1)

                # Set the Read point Relative To an operation.
                # Specifies the point in the buffer at which to begin a read operation,
                # here we read samples from beginning of acquisition and do not overwrite
                daq.DAQmxSetReadRelativeTo(
                    # define to which task to connect this function
                    task,
                    # Start reading samples relative to the last sample returned
                    # by the previous read
                    daq.DAQmx_Val_CurrReadPos)

                # Set the Read Offset.
                # Specifies an offset in samples per channel at which to begin a read
                # operation. This offset is relative to the location you specify with
                # RelativeTo. Here we do not read the first sample.
                daq.DAQmxSetReadOffset(
                    # connect to this task
                    task,
                    # Offset after which to read
                    1)

                # Set Read OverWrite Mode.
                # Specifies whether to overwrite samples in the buffer that you have
                # not yet read. Unread data in buffer will be overwritten:
                daq.DAQmxSetReadOverWrite(
                    task,
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
        self.log.info('runs scan line')
        if self._scanner_counter_daq_tasks is None:
            self.log.error('No counter is running, cannot scan a line without one.')
            return np.array([-1.])

        if not isinstance(line_path, (frozenset, list, set, tuple, np.ndarray,)):
            self.log.error('Given line_path list is not array type.')
            return np.array([-1.])
        try:
            self.log.info(self._scanner_do_task)
            # set task timing to use a sampling clock:
            # specify how the Data of the selected task is collected, i.e. set it
            # now to be sampled by a hardware (clock) signal.
            daq.DAQmxSetSampTimingType(self._scanner_do_task, daq.DAQmx_Val_SampClk)

            self.set_up_line(np.shape(line_path)[1])
            step_data = self._scanner_position_to_step(line_path)

            # write the positions to the analog output
            self._write_scanner_do(step_data=step_data,
                length=self._line_length,
                start=False)

            # start the timed analog output task
            daq.DAQmxStartTask(self._scanner_do_task)

            for i, task in enumerate(self._scanner_counter_daq_tasks):
                daq.DAQmxStopTask(task)

            daq.DAQmxStopTask(self._scanner_clock_daq_task)

            # start the scanner counting task that acquires counts synchroneously
            for i, task in enumerate(self._scanner_counter_daq_tasks):
                daq.DAQmxStartTask(task)

            daq.DAQmxStartTask(self._scanner_clock_daq_task)

            for i, task in enumerate(self._scanner_counter_daq_tasks):
                # wait for the scanner counter to finish
                daq.DAQmxWaitUntilTaskDone(
                    # define task
                    task,
                    # Maximum timeout for the counter times the positions. Unit is seconds.
                    self._RWTimeout * 2 * self._line_length)

            # wait for the scanner clock to finish
            daq.DAQmxWaitUntilTaskDone(
                # define task
                self._scanner_clock_daq_task,
                # maximal timeout for the counter times the positions
                self._RWTimeout * 2 * self._line_length)

            # count data will be written here
            self._scan_data = np.empty(
                (len(self.get_scanner_count_channels()), 2 * self._line_length),
                dtype=np.uint32)

            # number of samples which were read will be stored here
            n_read_samples = daq.int32()
            for i, task in enumerate(self._scanner_counter_daq_tasks):
                # actually read the counted photons
                daq.DAQmxReadCounterU32(
                    # read from this task
                    task,
                    # read number of double the # number of samples
                    2 * self._line_length,
                    # maximal timeout for the read# process
                    self._RWTimeout,
                    # write into this array
                    self._scan_data[i],
                    # length of array to write into
                    2 * self._line_length,
                    # number of samples which were actually read
                    daq.byref(n_read_samples),
                    # Reserved for future use. Pass NULL(here None) to this parameter.
                    None)

                # stop the counter task
                daq.DAQmxStopTask(task)

            # stop the clock task
            daq.DAQmxStopTask(self._scanner_clock_daq_task)

            # stop the analog output task
            self._stop_digital_output()
            self.log.info('do i get to this point?')
            # create a new array for the final data (this time of the length
            # number of samples):
            self._real_data = np.empty(
                (len(self.get_scanner_count_channels()), self._line_length),
                dtype=np.uint32)

            # add up adjoint pixels to also get the counts from the low time of
            # the clock:
            self._real_data = self._scan_data[:, ::2]
            self._real_data += self._scan_data[:, 1::2]

            # update the scanner position instance variable
            self._current_position = list(line_path[:, -1])
        except:
            self.log.exception('Error while scanning line.')
            return np.array([[-1.]])
        # return values is a rate of counts/s
        return (self._real_data * self._scanner_clock_frequency).transpose()

    def get_scanner_position(self):
        """ Get the current position of the scanner hardware.

        @return float[]: current position in (x, y, z, a).
        """
        return self._current_position

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
            self._write_scanner_do(self, step_data=self._scanner_position_to_step(my_position), length=0, start=True)
        except:
            return -1
        return 0

    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        a = self._stop_digital_output()
        c = self.close_counter(scanner=True)
        return -1 if a < 0 or c < 0 else 0

    def close_scanner_clock(self):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        return self.close_clock(scanner=True)

    def close_clock(self, scanner=False):
        """ Closes the clock and cleans up afterwards.

        @param bool scanner: specifies if the counter- or scanner- function
                             should be used to close the device.
                                True = scanner
                                False = counter

        @return int: error code (0:OK, -1:error)
        """
        if scanner:
            my_task = self._scanner_clock_daq_task
        else:
            my_task = self._clock_daq_task
        try:
            # Stop the clock task:
            daq.DAQmxStopTask(my_task)

            # After stopping delete all the configuration of the clock:
            daq.DAQmxClearTask(my_task)

            # Set the task handle to None as a safety
            if scanner:
                self._scanner_clock_daq_task = None
            else:
                self._clock_daq_task = None
        except:
            self.log.exception('Could not close clock.')
            return -1
        return 0

    def close_counter(self, scanner=False):
        """ Closes the counter or scanner and cleans up afterwards.

        @param bool scanner: specifies if the counter- or scanner- function
                             will be excecuted to close the device.
                                True = scanner
                                False = counter

        @return int: error code (0:OK, -1:error)
        """
        error = 0
        if scanner:
            for i, task in enumerate(self._scanner_counter_daq_tasks):
                try:
                    # stop the counter task
                    daq.DAQmxStopTask(task)
                    # after stopping delete all the configuration of the counter
                    daq.DAQmxClearTask(task)
                except:
                    self.log.exception('Could not close scanner counter.')
                    error = -1
            self._scanner_counter_daq_tasks = []
        else:
            for i, task in enumerate(self._counter_daq_tasks):
                try:
                    # stop the counter task
                    daq.DAQmxStopTask(task)
                    # after stopping delete all the configuration of the counter
                    daq.DAQmxClearTask(task)
                    # set the task handle to None as a safety
                except:
                    self.log.exception('Could not close counter.')
                    error = -1
            self._counter_daq_tasks = []
        return error

    # ================ End ConfocalScannerInterface Commands ===================


    def test(self, num=5):
        daq.DAQmxCfgImplicitTiming(self._scanner_do_task, daq.DAQmx_Val_FiniteSamps, num)
        # daq.DAQmxCfgImplicitTiming(self._scanner_do_task, daq.DAQmx_Val_ContSamps, 1000)
        daq.DAQmxStartTask(self._scanner_do_task)
        daq.DAQmxWaitUntilTaskDone(self._scanner_do_task, 10.00)
        daq.DAQmxStopTask(self._scanner_do_task)
        self.log.info('test')

