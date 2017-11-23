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


class JPEStageLogic(GenericLogic):
    """
    This is the Logic class for confocal scanning.
    """
    _modclass = 'confocallogic'
    _modtype = 'logic'

    # declare connectors
    confocalscanner = Connector(interface='JPE_stage_interface')
    savelogic = Connector(interface='SaveLogic')

    # status vars

    # signals

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self._Xabs = 0
        self._Yabs = 0
        self._Zabs = 0
        self.h = 5e-3
        self.R = 4e-3

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._scanning_device = self.get_connector('confocalscanner')
        self._save_logic = self.get_connector('savelogic')

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        pass

    def get_CLI_ver(self):
        """ Get CLI version information.
        @param :
        @return :
        """
        self.COMMAND = '/ver'
        self._scanning_device.do_command(self.COMMAND)
        return 0

    def get_list_CLA_type(self):
        """ List supported cryo linear actuator (CLA) types.
        @param :
        @return :
        """
        self.COMMAND = '/type'
        self._scanning_device.do_command(self.COMMAND)
        return 0

    def get_module_info(self):
        """ Get information about installed modules.
        @param :
        @return :
        """
        self.COMMAND = 'modlist'
        self._scanning_device.do_command(self.COMMAND)
        return 0

    def get_actuator_info(self, ADDR, CH):
        '''Get information on actuator types set
        @param :
        @return :
        '''
        self.COMMAND = 'INFO'
        self.ADDR = str(ADDR)
        self.CH = str(CH)
        self._scanning_device.do_command(self.COMMAND, self.ADDR, self.CH)
        return 0

    def get_module_description(self, ADDR):
        '''Get information on installed modules
        @param :
        @return :
        '''
        self.COMMAND = 'DESC'
        self.ADDR = str(ADDR)
        self._scanning_device.do_command(self.COMMAND, self.ADDR)
        return 0

    def move(self, ADDR, CH, TYPE, TEMP, DIR, FREQ, REL, STEPS, TRQFR = []):
        '''The move command starts moving an actuator with specified parameters. If an OEM2 is installed, the
        CLA-COE position will be tracked automatically.
        @param :
        @return :
        '''
        self.COMMAND = 'MOV'
        self.ADDR = str(ADDR)
        self.CH = str(CH)
        self.TYPE = str(TYPE)
        self.TEMP = str(TEMP)
        self.DIR = str(DIR)
        self.FREQ = str(FREQ)
        self.REL = str(REL)
        self.STEPS = str(STEPS)
        self.TRQFR = str(TRQFR)4
        self._scanning_device.do_command(self.COMMAND, self.ADDR, self.CH, self.TYPE, self.TEMP, self.DIR, self.FREQ, self.REL, self.STEPS, self.TRQFR)
        return 0

    def stop(self, ADDR):
        '''Stops movement of an actuator.
        @param :
        @return :
        '''
        self.COMMAND = 'STP'
        self.ADDR = str(ADDR)
        self._scanning_device.do_command(self.COMMAND, self.ADDR)
        return 0

    def get_status_actuator(self, ADDR):
        '''Requests the amplifier status: Moving or Stop.
        @param :
        @return :
        '''
        self.COMMAND = 'STS'
        self.ADDR = str(ADDR)
        self._scanning_device.do_command(self.COMMAND, self.ADDR)
        return 0

    def set_mode_input(self, ADDR, CH, TYPE, TEMP, DIR, FREQ, REL, STEPS, TRQFR = []):
        '''Select Analog Input (CADM2 only)
        Note: command specific for CADM2 and Flexdrive mode of operation only.
        To use the CADM2 in Flexdrive mode, it is required to set the module in analog input mode prior to using
        Flexdrive. The EXT command basically works similar to the MOV command, however there are a few
        differences:
        ▪ The [FREQ] parameter now defines the step frequency at maximum (absolute) input signal. By
        default set this to 600 [Hz].
        ▪ With the [DIR] parameter it is possible to reverse the input <> direction of movement relation. By
        default this parameter is set to 1 so that a positive input voltage results in a CW movement.
        @param :
        @return :
        '''
        self.COMMAND = 'EXT'
        self.ADDR = str(ADDR)
        self.CH = str(CH)
        self.TYPE = str(TYPE)
        self.TEMP = str(TEMP)
        self.DIR = str(DIR)
        self.FREQ = str(FREQ)
        self.REL = str(REL)
        self.STEPS = str(STEPS)
        self.TRQFR = str(TRQFR)
        self._scanning_device.do_command(self.COMMAND, self.ADDR, self.CH, self.TYPE, self.TEMP, self.DIR, self.FREQ, self.REL, self.STEPS, self.TRQFR)
        return 0

    def CLA_displacement(self, deltaX, deltaY, deltaZ):
        ''' Input parameter : Displacement of the sample at a high h
        Output : Movement of the 3 Cryogenic Linear Actuators that needs to be performed'''
        input_vector = np.matrix([deltaX, deltaY, deltaZ])
        transfert_matrix = np.matrix([
            [-(self.R*np.sqrt(3))/(2*self.h), self.R/(2*self.h), 1],
            [0, -self.R/self.h, 1],
            [(self.R*np.sqrt(3))/(2*self.h), self.R/(2*self.h), 1]
            ])
        return transfert_matrix*input_vector.T

    def update_absolute_position(self, deltaX, deltaY, deltaZ):
        self._Xabs = self._Xabs + deltaX
        self._Yabs = self._Yabs + deltaY
        self._Zabs = self._Zabs + deltaZ
        return self._Xabs, self._Yabs, self._Zabs

    def set_position(self, X, Y, Z):
        self.delta_X = X - self._Xabs
        self.delta_Y = Y - self._Yabs
        self.delta_Z = Z - self._Zabs
        self.deltaZ1, self.deltaZ2, self.deltaZ3 = self.CLA_displacement(self.delta_X, self.delta_Y, self.delta_Z)
        self.update_absolute_position(self.delta_X, self.delta_Y, self.delta_Z)
        print(int(self.deltaZ1/25e-9))
        self.move(ADDR=int(1), CH=int(1), TYPE = TEMP=int(293), DIR=int(0), FREQ=int(600), REL=int(100), STEPS=int(20))
        # self.move(ADDR=1, CH=2, TEMP=293, DIR=1, FREQ=600, REL=100, STEPS=int(self.deltaZ2/25e-9))
        # self.move(ADDR=1, CH=3, TEMP=293, DIR=1, FREQ=600, REL=100, STEPS=int(self.deltaZ3/25e-9))