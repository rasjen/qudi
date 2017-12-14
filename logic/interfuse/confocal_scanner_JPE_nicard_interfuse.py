# -*- coding: utf-8 -*-
"""
This module operates a confocal microsope.

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

from qtpy import QtCore
from collections import OrderedDict
from copy import copy
import time
import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from io import BytesIO

from logic.generic_logic import GenericLogic
from core.module import Connector, ConfigOption, StatusVar


class confocal_scanner_JPE_nicard_interfuse(Base):
    """
    This is the Logic class for confocal Scanner using JPE_CPSHR3 and nicard.
    """
    _modclass = 'confocalScannerJPENicardInterfuse'
    _modtype = 'interfuse'
    # connectors
    _connectors = {
        'scanner': 'JPE_CPSHR3_scanner',
        'counter': 'SlowCounterInterface'
    }
    # status vars
    # signals

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._scanner_hw = self.get_connector('confocal_interfuse_to_JPE_CPSRH3_hardware')
        self._counter_hw = self.get_connector('confocal_interfuse_to_nicard_hardware')

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self.reset_hardware()

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs can access it.

        @return int: error code (0:OK, -1:error)
        """
        self.log.warning('Scanning Devices will be reset.')
        self._scanner_hw.reset_hardware()
        self._counter_hw.reset_hardware()
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
            self._counter_hw.set_up_counter()
            return 0
        except:
            return -1
        return 0

    def get_scanner_count_channels(self):
        '''
        Pass through counter channels.
        :return:
        '''

        return self._counter_hw.get_counter_channels()

    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        self._counter_hw.close_counter()
        return 0

    def close_scanner_clock(self):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        self._counter_hw.close_clock()
        return 0
