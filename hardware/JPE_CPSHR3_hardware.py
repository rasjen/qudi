# -*- coding: utf-8 -*-

"""
This file contains the Qudi Hardware module CPSRH3 class.
"""

import numpy as np
import subprocess
import time
from core.module import Base
from interface.JPE_CPSHR3_interface import JPE_CPSHR3_interface
from hardware.JPE_CLA_hardware import CLA

class JPE_CPSHR3_hardware(Base, JPE_CPSHR3_interface):
    ''' CPSHR3_hardware class
    CPSHR : Cryo Positionning Stage High Resonnance'''
    
    _modtype = 'JPE_CPSHR3_hardware'
    _modclass = 'hardware'
# blabla
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

