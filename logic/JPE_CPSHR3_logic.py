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


class JPE_CPSHR3_logic(GenericLogic):
    """
    This is the Logic class for JPE_CPSHR3.
    """
    _modclass = 'JPE_CPSHR3_logic'
    _modtype = 'logic'

    # declare connectors
    JPE_CPSHR3_logic_to_JPE_CPSHR3_hardware_connector = Connector(interface='JPE_CPSHR3_interface')
    savelogic = Connector(interface='SaveLogic')

    # status vars

    # signals

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._JPE_CPSHR3_hardware = self.get_connector('JPE_CPSHR3_logic_to_JPE_CPSHR3_hardware_connector')
        self._save_logic = self.get_connector('savelogic')

        self.CLA1 = self._JPE_CPSHR3_hardware.CLA1
        self.CLA2 = self._JPE_CPSHR3_hardware.CLA2
        self.CLA3 = self._JPE_CPSHR3_hardware.CLA3

        self.CLA_radius = self._JPE_CPSHR3_hardware.get_CLA_radius()
        self.sample_height = self._JPE_CPSHR3_hardware.get_sample_height()
        self.sleep_time = 0.5

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self.stop_CLAs

    def get_CLA_STATUS(self, CLA_number):
        '''Get the status of a CLA : Moving or Stopped'''
        if self._JPE_CPSHR3_hardware.do_command('STS ' + str(CLA_number)) == 'STATUS : STOP\r\nFAILSAFE STATE: 0x0\r\n':
            status = 'Stopped'
        else:
            status = 'Moving'
        return status

    def CLA_displacement(self, delta_x, delta_y, delta_z):
        ''' Calculate the displacement of the coarse positioner in function of the
        displacement wanted '''
        input_vector = np.matrix([delta_x, delta_y, delta_z])
        M =  np.matrix([
            [-(self.CLA_radius*np.sqrt(3))/(2*self.sample_height), self.CLA_radius/(2*self.sample_height), 1],
            [0, -self.CLA_radius/self.sample_height, 1],
            [(self.CLA_radius*np.sqrt(3))/(2*self.sample_height), self.CLA_radius/(2*self.sample_height), 1]
            ])
        output_vector = M*input_vector.T
        return output_vector[0,0], output_vector[1,0],  output_vector[2,0]

    def calc_STEPS_number(self, value):
        ''' Calculate the closest number of actuation steps for a specified
        CLA displacement'''
        step_amp = self.CLA1.get_STEP_AMP_MAX()
        number_of_steps = np.around(np.divide(value, step_amp), 0)
        return number_of_steps.astype(int)

    def stop_CLAs(self):
        self._JPE_CPSHR3_hardware.do_command('STP 1')
        self._JPE_CPSHR3_hardware.do_command('STP 2')
        self._JPE_CPSHR3_hardware.do_command('STP 3')
        return 0

    def get_CLI_ver(self):
            """ Get CLI version information.
            """
            self._JPE_CPSHR3_hardware.do_command('/ver')
            return 0

    def get_list_CLA_type(self):
        """ List supported cryo linear actuator (CLA) types.
        """
        self._JPE_CPSHR3_hardware.do_command('/type')
        return 0

    def get_module_info(self):
        """ Get information about installed modules.
        """
        self._JPE_CPSHR3_hardware.do_command('modlist')
        return 0

    def get_actuator_info(self, ADDR, CH):
        '''Get information on actuator types set
        '''
        self.COMMAND = 'INFO'
        self.ADDR = str(ADDR)
        self.CH = str(CH)
        self._JPE_CPSHR3_hardware.do_command(self.COMMAND, self.ADDR, self.CH)
        return 0

    def get_module_description(self, ADDR):
        '''Get information on installed modules
        '''
        self.COMMAND = 'DESC'
        self.ADDR = str(ADDR)
        self._JPE_CPSHR3_hardware.do_command(self.COMMAND, self.ADDR)
        return 0

    def edit_cmd_line(self, *list_parameters):
        '''Convert a list of parameters into a command line sutable for cacli.exe
        software'''
        cmd_line = str(' '.join(list_parameters))
        return cmd_line

    def exec_cmd_lines(self, CLA1_cmd_line, CLA2_cmd_line, CLA3_cmd_line):
        '''This function execute the comand lines for each CLA if the steps number
        is non equal to 0 which is equivalent for cacli software to infinite motion'''
        if self.CLA1.get_STEPS() == '0':
            pass
        else:
            self._JPE_CPSHR3_hardware.do_command(CLA1_cmd_line)
        if self.CLA2.get_STEPS() == '0':
            pass
        else:
            self._JPE_CPSHR3_hardware.do_command(CLA2_cmd_line)
        if self.CLA3.get_STEPS() == '0':
            pass
        else:
            self._JPE_CPSHR3_hardware.do_command(CLA3_cmd_line)

    def move_xyz(self, delta_x, delta_y, delta_z):
        '''Move the sample using xyz coordinate system relative to the actual point
        delta_x, delta_y and delta_z in micrometers'''
        # Conversion of delta_x, delta_y and delta_z into micrometers
        delta_x= delta_x*1e-6
        delta_y= delta_y*1e-6
        delta_z= delta_z*1e-6
        # Calculation of the CLAs displacement
        CLA1_displacement, CLA2_displacement, CLA3_displacement = self.CLA_displacement(delta_x, delta_y, delta_z)
        # Set the CLA step to the closer integer number corresponding to the displacement
        self.CLA1.set_STEPS(np.abs(self.calc_STEPS_number(CLA1_displacement)))
        self.CLA2.set_STEPS(np.abs(self.calc_STEPS_number(CLA2_displacement)))
        self.CLA3.set_STEPS(np.abs(self.calc_STEPS_number(CLA3_displacement)))
        # Determination of the rotation clockwise or counter-clockwise of each CLA
        if CLA1_displacement < 0 :
            self.CLA1.set_DIR(1)
        elif CLA1_displacement > 0 :
            self.CLA1.set_DIR(0)
        if CLA2_displacement < 0 :
            self.CLA2.set_DIR(1)
        elif CLA2_displacement > 0 :
            self.CLA2.set_DIR(0)
        if CLA3_displacement < 0 :
            self.CLA3.set_DIR(1)
        elif CLA3_displacement > 0 :
            self.CLA3.set_DIR(0)
        # Creation of the command lines for each CLA
        CLA1_cmd_line = 'MOV ' + self.edit_cmd_line(self.CLA1.get_ADDR(), self.CLA1.get_CH(), self.CLA1.get_TYPE(), self.CLA1.get_TEMP(), self.CLA1.get_DIR(), self.CLA1.get_FREQ(), self.CLA1.get_REL(), self.CLA1.get_STEPS())
        CLA2_cmd_line = 'MOV ' + self.edit_cmd_line(self.CLA2.get_ADDR(), self.CLA2.get_CH(), self.CLA2.get_TYPE(), self.CLA2.get_TEMP(), self.CLA2.get_DIR(), self.CLA1.get_FREQ(), self.CLA2.get_REL(), self.CLA2.get_STEPS())
        CLA3_cmd_line = 'MOV ' + self.edit_cmd_line(self.CLA3.get_ADDR(), self.CLA3.get_CH(), self.CLA3.get_TYPE(), self.CLA3.get_TEMP(), self.CLA3.get_DIR(), self.CLA1.get_FREQ(), self.CLA3.get_REL(), self.CLA3.get_STEPS())
        # Execute the comand lines
        print(CLA1_cmd_line)
        print(CLA2_cmd_line)
        print(CLA3_cmd_line)
        # self.exec_cmd_lines(CLA1_cmd_line, CLA2_cmd_line, CLA3_cmd_line)
        while True:
            time.sleep(0.1)
            if self.get_CLA_STATUS(1) == 'Stopped' and self.get_CLA_STATUS(2) == 'Stopped' and self.get_CLA_STATUS(3) == 'Stopped':
                break

    def tilt(self, direction, alpha):
        '''Tilt the sample mount by an angle in a chosen direction
        direction = 'up', 'down', 'left' or 'right'
        alpha = angle (unit : degree)
        NOT WORKING PROPERLY : NEED TO BE MODIFIED
        '''
        alpha_rad = alpha*np.pi/180
        if direction == 'up':
            # Calculation of the CLAs displacement
            CLA1_displacement = (1/2)*(self.CLA_radius*np.tan(alpha_rad)/self.CLA1.get_STEP_AMP_MAX())
            CLA2_displacement = self.CLA_radius*np.tan(alpha_rad)/self.CLA2.get_STEP_AMP_MAX()
            CLA3_displacement = (1/2)*(self.CLA_radius*np.tan(alpha_rad)/self.CLA3.get_STEP_AMP_MAX())
            # Set rotation clockwise or counter-clockwise of each CLA
            self.CLA1.set_DIR(0)
            self.CLA2.set_DIR(1)
            self.CLA3.set_DIR(0)
        if direction == 'down':
            # Calculation of the CLAs displacement
            CLA1_displacement = (1/2)*(self.CLA_radius*np.tan(alpha_rad)/self.CLA1.get_STEP_AMP_MAX())
            CLA2_displacement = self.CLA_radius*np.tan(alpha_rad)/self.CLA2.get_STEP_AMP_MAX()
            CLA3_displacement = (1/2)*(self.CLA_radius*np.tan(alpha_rad)/self.CLA3.get_STEP_AMP_MAX())
            # Set rotation clockwise or counter-clockwise of each CLA
            self.CLA1.set_DIR(1)
            self.CLA2.set_DIR(0)
            self.CLA3.set_DIR(1)
        if direction == 'right':
            # Calculation of the CLAs displacement
            CLA1_displacement = (self.CLA_radius*np.sqrt(3)/2)*np.tan(alpha_rad)/self.CLA1.get_STEP_AMP_MAX()
            CLA2_displacement = 0
            CLA3_displacement = (self.CLA_radius*np.sqrt(3)/2)*np.tan(alpha_rad)/self.CLA3.get_STEP_AMP_MAX()
            # Set rotation clockwise or counter-clockwise of each CLA
            self.CLA1.set_DIR(0)
            self.CLA3.set_DIR(1)
        if direction == 'left':
            # Calculation of the CLAs displacement
            CLA1_displacement = (self.CLA_radius*np.sqrt(3)/2)*np.tan(alpha_rad)/self.CLA1.get_STEP_AMP_MAX()
            CLA2_displacement = 0
            CLA3_displacement = (self.CLA_radius*np.sqrt(3)/2)*np.tan(alpha_rad)/self.CLA3.get_STEP_AMP_MAX()
            # Set rotation clockwise or counter-clockwise of each CLA
            self.CLA1.set_DIR(1)
            self.CLA3.set_DIR(0)
        # Set the CLA step to the closer integer number corresponding to the displacement
        self.CLA1.set_STEPS(np.abs(self.calc_STEPS_number(CLA1_displacement)))
        self.CLA2.set_STEPS(np.abs(self.calc_STEPS_number(CLA2_displacement)))
        self.CLA3.set_STEPS(np.abs(self.calc_STEPS_number(CLA3_displacement)))
        # Creation of the command lines for each CLA
        CLA1_cmd_line = 'MOV ' + self.edit_cmd_line(self.CLA1.get_ADDR(), self.CLA1.get_CH(), self.CLA1.get_TYPE(), self.CLA1.get_TEMP(), self.CLA1.get_DIR(), self.CLA1.get_FREQ(), self.CLA1.get_REL() ,self.CLA1.get_STEPS())
        CLA2_cmd_line = 'MOV ' + self.edit_cmd_line(self.CLA2.get_ADDR(), self.CLA2.get_CH(), self.CLA2.get_TYPE(), self.CLA2.get_TEMP(), self.CLA2.get_DIR(), self.CLA1.get_FREQ(), self.CLA2.get_REL() ,self.CLA2.get_STEPS())
        CLA3_cmd_line = 'MOV ' + self.edit_cmd_line(self.CLA3.get_ADDR(), self.CLA3.get_CH(), self.CLA3.get_TYPE(), self.CLA3.get_TEMP(), self.CLA3.get_DIR(), self.CLA1.get_FREQ(), self.CLA3.get_REL() ,self.CLA3.get_STEPS())
        # Execute the comand lines
        print(CLA1_cmd_line)
        print(CLA2_cmd_line)
        print(CLA3_cmd_line)
        # self.exec_cmd_lines()

    def scan_line_left_to_right(self, step_x, range_x):
        ''' Scan a line from left to right'''
        n = 0
        n_points = np.around(range_x/step_x,0)
        while n <= n_points :
            print('point = ', int(n))
            self.move_xyz(step_x, 0, 0)
            while True:
                time.sleep(self.sleep_time)
                if self.get_CLA_STATUS(1) == 'Stopped' and self.get_CLA_STATUS(2) == 'Stopped' and self.get_CLA_STATUS(3) == 'Stopped':
                    break
            n += 1

    def scan_line_right_to_left(self, step_x, range_x):
        ''' Scan a line from right to left'''
        n_points = np.around(range_x/step_x,0)
        while n_points >= 0 :
            print('point = ', int(n_points))
            self.move_xyz(-step_x, 0, 0)
            while True:
                time.sleep(self.sleep_time)
                if self.get_CLA_STATUS(1) == 'Stopped' and self.get_CLA_STATUS(2) == 'Stopped' and self.get_CLA_STATUS(3) == 'Stopped':
                    break
            n_points -= 1

    def stop_CLAs(self):
        self._JPE_CPSHR3_hardware.do_command('STP 1')
        self._JPE_CPSHR3_hardware.do_command('STP 2')
        self._JPE_CPSHR3_hardware.do_command('STP 3')
        print('CLAs stopped')
