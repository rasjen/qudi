from core.module import Base, Connector
from interface.spectrometer_interface2 import SpectrometerInterface

from time import strftime, localtime, sleep

import time
import numpy as np
from qtpy import QtCore



class SpectrometerInterfaceDummy(Base,SpectrometerInterface):
    """ Dummy spectrometer module.

        Shows a silicon vacancy spectrum at liquid helium temperatures.
    """

    _modclass = 'SpectrometerDummy'
    _modtype = 'hardware'

    fitlogic = Connector(interface='FitLogic')

    sigMeasurementStarted = QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.exposure = 0.1
        self.temperature = 20
        self.averages = 1

    def on_activate(self):
        """ Activate module.
        """
        self._fitLogic = self.get_connector('fitlogic')

    def on_deactivate(self):
        """ Deactivate module.
        """
        pass

    def record_spectrum(self):
        """ Record a dummy spectrum.

            @return ndarray: 1024-value ndarray containing wavelength and intensity of simulated spectrum
        """
        length = 1024

        data = np.empty((2, length), dtype=np.double)
        data[0] = np.arange(730, 750, 20/length)
        data[1] = np.random.uniform(0, 2000, length)

        lorentz, params = self._fitLogic.make_multiplelorentzian_model(no_of_functions=4)
        sigma = 0.05
        params.add('l0_amplitude', value=2000)
        params.add('l0_center', value=736.46)
        params.add('l0_sigma', value=1.5*sigma)
        params.add('l1_amplitude', value=5800)
        params.add('l1_center', value=736.545)
        params.add('l1_sigma', value=sigma)
        params.add('l2_amplitude', value=7500)
        params.add('l2_center', value=736.923)
        params.add('l2_sigma', value=sigma)
        params.add('l3_amplitude', value=1000)
        params.add('l3_center', value=736.99)
        params.add('l3_sigma', value=1.5*sigma)
        params.add('offset', value=50000.)

        data[1] += lorentz.eval(x=data[0], params=params)

        time.sleep(self.exposure)
        return data

    def saveSpectrum(self, path, postfix = ''):
        """ Dummy save function.

            @param str path: path of saved spectrum
            @param str postfix: postfix of saved spectrum file
        """
        timestr = strftime("%Y%m%d-%H%M-%S_", localtime())
        print( 'Dummy would save to: ' + str(path) + timestr + str(postfix) + ".spe" )

    def get_exposure_time(self):
        """ Get exposure time.

            @return float: exposure time
        """
        return self.exposure

    def set_exposure_time(self, exposureTime):
        """ Set exposure time.

            @param float exposureTime: exposure time
        """
        self.exposure = exposureTime

    def set_temperature(self, temperature):
        '''
        Set the temperature.
        
        :param temperature: temperature in celcius 
        :return: 
        '''

        self.temperature = temperature

    def get_temperature(self):
        '''
        Return the temperatur of the camera
        
        :return: temperature in celcius
        '''

        return self.temperature

    def get_wavelengths(self):
        '''
        
        :return: retruns an array with the wavelengths in nm
        '''
        self.wl = np.linspace(500,900,1600)
        return self.wl

    def set_number_accumulations(self, averages):

        self.averages = averages

    def get_number_accumulations(self):

        return self.averages

    def take_single_spectrum(self):
        data = np.random.rand(self.wl.size)
        return data


    def kinetic_scan(self, exposure_time=None, cycle_time=None, number_of_cycles=None, sweep_start=False, trigger=None):
        """
        Takes a kinetic scan

        @param exposure_time: This is the time in seconds during which the CCD collects light prior to readout
        @param cycle_time: This is the period in seconds between the start of individual scans
        @param number_of_cycles: This is the number of scans (or ‘accumulated scans’) you specify to be in your series
        @return:
        """
        print(1/cycle_time* number_of_cycles)
        sleep(1/cycle_time* number_of_cycles)

        data = np.random.rand(number_of_cycles,1600)

        return data

    def set_cycle_time(self, time):
        self.cycle_time = time






