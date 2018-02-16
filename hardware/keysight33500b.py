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

    def set_function(self, source, waveform):
        self.waveform_generator.write('SOURce{}:FUNCtion {}'.format(source, waveform))

    def set_offset(self, source, offset):
        self.waveform_generator.write('SOURce{}:VOLTage:OFFSet {}'.format(source, offset))

    def enable_output(self, source):
        self.waveform_generator.write('OUTPut{} 1'.format(source))

    def disable_output(self, source):
        self.waveform_generator.write('OUTPut{} 0'.format(source))

    def set_amplitude_limit(self, source, lower_limit, upper_limit):
        self.waveform_generator.write('SOURce{}:VOLT:LIMIT:LOW {}'.format(source, lower_limit))
        self.waveform_generator.write('SOURce{}:VOLT:LIMIT:HIGH {}'.format(source, upper_limit))

    def set_frequency(self, source, frequency):
        self.waveform_generator.write('SOURce{}:FREQuency {}'.format(source, frequency))

    def set_amplitude(self, source, voltage):
        self.waveform_generator.write('SOURce{}:VOLTage {}'.format(source, voltage))

    def set_output_load(self, output, load):
        self.waveform_generator.write('OUTPut{}:LOAD {}'.format(output, load))
        if load > 10000:
            print('Output load fixed at maximum : 10000 Ohms')
        if load < 1 :
            print('Output load fixed at minimum : 1 Ohms')

    def set_waveform(self, **kwargs):
        self.waveform_generator.write('SOURce{}:APPLy:{} {},{},{}'.format(kwargs['source'], kwargs['function'],kwargs['frequency'], kwargs['amplitude'], kwargs['offset']))

    def set_square_wave_duty_cycle(self, source, DCYCle):
        print('SOURce{}:FUNCtion:SQUare:DCYCle{}'.format(source, DCYCle))
        self.waveform_generator.write('SOURce{}:FUNCtion:SQUare:DCYCle {}'.format(source, DCYCle))

    def set_ramp_symmetry(self, source, symmetry):
        self.waveform_generator.write('SOURce{}:FUNCtion:RAMP:SYMMetry {}'.format(source, symmetry))

    def set_phase(self, source, phase):
        self.waveform_generator.write('SOURce{}:PHASe {}'.format(source, phase))

    def get_source_parameters(self, source):
        self.function, self.frequency, self.amplitude, self.offset = self.waveform_generator.query('SOURce{}:APPLy?'.format(source)).replace(',', ' ').replace('"', ' ').split()
        self.phase = self.waveform_generator.query('SOURce{}:PHASe?'.format(source)).rstrip()
        return self.function, float(self.frequency), float(self.amplitude), float(self.offset), float(self.phase)

    def get_output_status(self, source):
        if self.waveform_generator.query('OUTPut{}?'.format(source)).rstrip() == '1':
            return 'ON'
        else:
            return 'OFF'
