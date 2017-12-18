from qtpy import QtCore
from collections import OrderedDict
import datetime
import numpy as np
import os
from itertools import product
from time import sleep, time
import matplotlib.pyplot as plt

from scipy.optimize import curve_fit
from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from core.module import Connector, ConfigOption, StatusVar



class WLTLogic(GenericLogic):
    """
    This is the Logic class for cavity white light transmission measurement.
    """
    _modclass = 'WLTlogoc'
    _modtype = 'logic'

    # declare connectors
    nicard = Connector(interface='ConfocalScannerInterface')
    spectrometer = Connector(interface='spectrometerInterface')
    savelogic = Connector(interface='SaveLogic')

    # signals for WLT
    sigNextLine = QtCore.Signal()

    # Update signals, e.g. for GUI module
    sigParameterUpdated = QtCore.Signal(int, float, int)
    sigOutputStateUpdated = QtCore.Signal(str, bool)
    sigSpectrumPlotUpdated = QtCore.Signal(np.ndarray, np.ndarray)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        # locking for thread safet
        self.threadlock = Mutex()

        self.number_of_steps = 10
        self.spectrometer_resolution = 100

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._scanning_devices = self.get_connector('nicard')
        self._save_logic = self.get_connector('savelogic')
        self._spectrometer = self.get_connector('spectrometer')

        self.target_temperature = -999
        self.current_temperature = -999
        self.number_accumulations = 1
        self.exposure_time = 1.0

        self.get_number_accumulations()
        self.get_exposure_time()
        self.get_temperature()

        self.initialize_image()
        self.initialize_spectrum_plot()


    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._spectrometer.on_deactivate()
        self._scanning_device.on_deactivate()


    def start_wlt_measurement(self):
        '''
        Start the white light transmission measurement

        :return: 
        '''
        self.line_counter = 0

        self.lock()

        self._scanning_device.lock()
        if self.initialize_image() < 0:
            self._scanning_device.unlock()
            self.unlock()
            return -1

        clock_status = self._scanning_device.set_up_scanner_clock(
            clock_frequency=self._clock_frequency)


        if clock_status < 0:
            self._scanning_device.unlock()
            self.unlock()
            self.set_position('scanner')
            return -1

        scanner_status = self._scanning_device.set_up_scanner()

        pass

    def stop_wlt_measurement(self):
        '''
        Stops the white light transmission measurement
        :return: 
        '''
        pass

    def continue_wlt_measurement(self):
        '''
        Continues the white light transmission measurement

        :return: 
        '''
        pass

    def setup_wlt_measurement(self, scan_frequency, scan_range, measurement_frequency):
        '''

        :param scan_frequency: How fast is the cavity length swept
        :param scan_range: What is the min and max cavity position during the measurement
        :param exposure_time: Exposure time of the camera
        :param measurement_frequency: How fast are we going to measure
        :return: 
        '''
        pass


    def initialize_image(self):
        '''
        Setup an initial array for the WLT measurement

        :return: 
        '''
        self.wl = self._spectrometer.get_wavelength()

        self.WLT_image = np.zeros([self.wl.size, self.number_of_steps])
        pass

    def initialize_spectrum_plot(self):
        """
        Initialises single spectrum for gui
        
        :return: 
        """
        self.wl = self._spectrometer.get_wavelength()
        self.counts = 1e6*np.random.rand(self.wl.size)
        pass

    def get_temperature(self):
        '''
        Gets the temperature for the camera in spectrometer

        :return: the temperature of the camera in spectrometer 
        '''

        try:
            self.current_temperature = self._spectrometer.get_temperature()
        except:
            self.log.error('Could not get temperature from spectrometer')

        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations)

    def set_temperature(self, temperature=None):
        '''
        Sets the temperature for the spectrometer 

        :param temperature: in C [-75, 25]
        :return: 
        '''

        if temperature is None:
            if self.target_temperature is not None:
                temperature = self.target_temperature
            else:
                self.log.error('No target temperature')

        self._spectrometer.set_temperature(temperature)

    def set_exposure_time(self, exposure_time=None):
        '''
        Sets the exposure time for the camera in the spectrometer

        :return: 
        '''
        if exposure_time is None:
            exposure_time = self.exposure_time

        self._spectrometer.set_exposure_time(exposure_time)

        self.get_exposure_time()

    def get_exposure_time(self):
        '''
        Gets the exposure time for the camera in the spectrometer

        :return: 
        '''

        self.exposure_time = self._spectrometer.get_exposure_time()

        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations)

    def set_number_accumulations(self, number_accumulations=None):
        """
        Sets the number of accumulations that the spectrometer 

        :param number_accumulations: number of accumulations (int)
        :return: 
        """
        if number_accumulations is None:
            number_accumulations = self.number_accumulations

        self._spectrometer.set_number_accumulations(number_accumulations)

        self.get_number_accumulations()

    def get_number_accumulations(self):
        '''
        Gets the number of accumulations for the spectrometer

        :return: 
        '''
        self.number_accumulations = self._spectrometer.get_number_accumulations()
        self.sigParameterUpdated.emit(self.current_temperature, self.exposure_time, self.number_accumulations)

    def get_hw_constraints(self):
        """ Return the names of all ocnfigured fit functions.
        @return object: Hardware constraints object
        """
        # FIXME: Should be from hardware
        constraints_dict = {'min_position': 0, 'max_position': 20e-6, 'min_speed': 0, 'max_speed':  100,
                            'min_temperature': -100, 'max_temperature': 30, 'min_number_accumulations': 1,
                            'max_number_accumulations': 1000, 'min_exposure': 0, 'max_exposure': 100}

        return constraints_dict

    def take_single_spectrum(self):
        self.counts = self._spectrometer.take_single_spectrum()
        self.sigSpectrumPlotUpdated.emit(self.wl, self.counts)

