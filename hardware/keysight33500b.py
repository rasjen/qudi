from core.module import Base
from interface.empty_interface import EmptyInterface
import visa
import string
import sys
import numpy as np
import matplotlib.pyplot as plt

class Keysight33500b(Base, EmptyInterface):
    """
    This is the Interface class to define the controls for the simple
    microwave hardware.
    """
    _modclass = 'EmptyInterface'
    _modtype = 'hardware'

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self.log.info('The following configuration was found.')
        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key, config[key]))
        self.rm = visa.ResourceManager()
        self.res = self.rm.list_resources()

    def on_activate(self):
        """
        Initialisation performed during activation of the module.
        """
        config = self.getConfiguration()
        self.waveform_generator = self.rm.open_resource(self.res[0])
        self.waveform_generator.read_termination = None
        self.waveform_generator.write_termination = '\n'
        print('Connected to ' + self.waveform_generator.query('*IDN?'))
        return

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        self.waveform_generator.close()
        self.rm.close()
        return

    def get_waveform(self, source):
        return self.waveform_generator.query('SOURce{}:FUNCtion?'.format(source))

    def set_waveform(self, source, waveform):
        self.waveform_generator.write('SOURce{}:FUNCtion {}'.format(source, waveform))

    def set_DC_level(self, source, DC_level):
        self.waveform_generator.write('SOURce{}:APPLy:DC {}'.format(source, DC_level))

    def enable_output(self, source):
        self.waveform_generator.write('OUTPut{} 1'.format(source))

    def disable_output(self, source):
        self.waveform_generator.write('OUTPut{} 0'.format(source))

    def set_voltage_limit(self, source, lower_limit, upper_limit):
        self.waveform_generator.write('SOURce{}:VOLT:LIMIT:LOW {}'.format(source, lower_limit))
        self.waveform_generator.write('SOURce{}:VOLT:LIMIT:HIGH {}'.format(source, upper_limit))

