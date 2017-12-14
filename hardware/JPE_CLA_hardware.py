# -*- coding: utf-8 -*-

"""
This file contains the CLA class
"""


class CLA():
    '''Cryogenic Linear Actuator class '''
    
    def __init__(self, CLA_ADDR, CLA_CH, CLA_TYPE, CLA_TEMP, CLA_DIR, CLA_FREQ, CLA_REL, CLA_STEP_AMP_MAX, CLA_STEPS):
        self.CLA_ADDR = str(CLA_ADDR) # Adress of the module corresponding to the CLA
        self.CLA_CH = str(CLA_CH) # Channel on the module corresponding to the CLA
        self.CLA_TYPE = str(CLA_TYPE) # CLA type (CA1801)
        self.CLA_TEMP = str(CLA_TEMP) # Temperature (unit : Kelvin)
        self.CLA_DIR = str(CLA_DIR) # CLA direction (1 : clockwise, 0 : counter-clockwise)
        self.CLA_FREQ = str(CLA_FREQ) # Frequency of operation (unit : Hz)
        self.CLA_REL = str(CLA_REL) # (Relative) Piezo step size (unit : %)
        self.CLA_STEP_AMP_MAX = CLA_STEP_AMP_MAX # Maximum Piezo step size (unit : meter)
        self.CLA_STEPS = str(CLA_STEPS) # Number of actuation steps
        
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