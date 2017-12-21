# -*- coding: utf-8 -*-

"""
This file contains the Qudi Hardware module CPSRH3 class.
"""

import numpy as np
import subprocess
import time
from core.module import Base
from interface.empty_interface import EmptyInterface

class JPE_CPSHR3_hardware(Base, EmptyInterface):
    ''' CPSHR3_hardware class
    CPSHR : Cryo Positionning Stage High Resonnance'''
    
    _modtype = 'JPE_CPSHR3_hardware'
    _modclass = 'hardware'

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        # cacli.exe relative path
        self.cacli_path = 'cacli.exe'
        # Default CLAs parameters
        self.CLA1 = CLA(1, 1, 'CA1801', 293, 0, 600, 100, 25e-9, 0)
        self.CLA2 = CLA(2, 1, 'CA1801', 293, 0, 600, 100, 25e-9, 0)
        self.CLA3 = CLA(3, 1, 'CA1801', 293, 0, 600, 100, 25e-9, 0)
        # Default CPSHR3 parameters
        self.CLA_radius = 26e-3  # unit : meter
        self.sample_height = 55e-3  # unit : meter
        # self.sleep_time = 0.5  # unit : second

    def on_deactivate(self, e=None):
        """ Shut down the device.
        """
        self.reset_hardware()

    def reset_hardware(self):
        """ Reset
        """
        pass
  
    def do_command(self, cmd):
        '''Open the cacli.exe file provided by Jansen Precision Engeneering (JPE) 
        and execute a command line like specified in the software manual available
        on JPE website'''
        proc = subprocess.Popen('cacli.exe ' + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = proc.stdout.read().decode('utf-8')#.strip().split()
        return output

    def get_CLA_radius(self):
        ''' Get the radius of the CLAs center with respect to the center of the CPSR3 mount (unit : meter)'''
        return self.CLA_radius

    def get_sample_height(self):
        ''' Get the height of the sample with respect to CPSR3 mount (unit : meter)'''
        return self.sample_height



class CLA():
    '''Cryogenic Linear Actuator class '''

    def __init__(self, CLA_ADDR, CLA_CH, CLA_TYPE, CLA_TEMP, CLA_DIR, CLA_FREQ, CLA_REL, CLA_STEP_AMP_MAX, CLA_STEPS):
        self.CLA_ADDR = str(CLA_ADDR)  # Adress of the module corresponding to the CLA
        self.CLA_CH = str(CLA_CH)  # Channel on the module corresponding to the CLA
        self.CLA_TYPE = str(CLA_TYPE)  # CLA type (CA1801)
        self.CLA_TEMP = str(CLA_TEMP)  # Temperature (unit : Kelvin)
        self.CLA_DIR = str(CLA_DIR)  # CLA direction (1 : clockwise, 0 : counter-clockwise)
        self.CLA_FREQ = str(CLA_FREQ)  # Frequency of operation (unit : Hz)
        self.CLA_REL = str(CLA_REL)  # (Relative) Piezo step size (unit : %)
        self.CLA_STEP_AMP_MAX = CLA_STEP_AMP_MAX  # Maximum Piezo step size (unit : meter)
        self.CLA_STEPS = str(CLA_STEPS)  # Number of actuation steps

    def set_ADDR(self, ADDR):
        '''Set the adress of the module corresponding to the CLA '''
        self.CLA_ADDR = str(ADDR)

    def get_ADDR(self):
        '''Get the adress of the module corresponding to the CLA '''
        return self.CLA_ADDR

    def set_CH(self, CH):
        '''Set the channel on the module corresponding to the CLA '''
        self.CLA_CH = str(CH)

    def get_CH(self):
        '''Get the channel on the module corresponding to the CLA '''
        return self.CLA_CH

    def set_TYPE(self, TYPE):
        '''Set the CLA type'''
        self.CLA_TYPE = TYPE

    def get_TYPE(self):
        '''Get the CLA type'''
        return self.CLA_TYPE

    def set_TEMP(self, TEMP):
        '''Set the operation temperature of the CLA'''
        self.CLA_TEMP = str(TEMP)

    def get_TEMP(self):
        '''Get the operation temperature of the CLA (entered by the user, not measured!)'''
        return self.CLA_TEMP

    def set_DIR(self, DIR):
        '''Set the CLA direction (1 : clockwise, 0 : counter-clockwise) '''
        self.CLA_DIR = str(DIR)

    def get_DIR(self):
        '''Get the CLA direction (1 : clockwise, 0 : counter-clockwise) '''
        return self.CLA_DIR

    def set_FREQ(self, FREQ):
        '''Set the CLA frequency of operation (unit : Hz) from 0 to 600 Hz'''
        self.CLA_FREQ = str(FREQ)

    def get_FREQ(self):
        '''Get the CLA frequency of operation (unit : Hz) from 0 to 600 Hz'''
        return self.CLA_FREQ

    def set_REL(self, REL):
        ''' Set (Relative) Piezo step size (unit : %) '''
        self.CLA_REL = str(REL)

    def get_REL(self):
        '''Get (Relative) Piezo step size (unit : %) '''
        return self.CLA_REL

    def set_STEP_AMP_MAX(self, STEP_AMP_MAX):
        '''Set maximum Piezo step size (unit : meter) specified 5-25nm by JPE'''
        self.CLA_STEP_AMP_MAX = STEP_AMP_MAX

    def get_STEP_AMP_MAX(self):
        '''Get maximum Piezo step size (unit : meter) (specified by user, not measured!)'''
        return self.CLA_STEP_AMP_MAX

    def set_STEPS(self, STEPS):
        ''' Set the number of actuation steps'''
        self.CLA_STEPS = str(STEPS)

    def get_STEPS(self):
        ''' Get the number of actuation steps (specified by user, not measured!)'''
        return self.CLA_STEPS