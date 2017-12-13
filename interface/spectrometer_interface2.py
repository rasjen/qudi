import abc
from core.util.interfaces import InterfaceMetaclass


class SpectrometerInterface(metaclass=InterfaceMetaclass):
    """This is the Interface class to define the controls for the simple
    optical spectrometer.
    """
    @abc.abstractmethod
    def record_spectrum(self):
        pass

    @abc.abstractmethod
    def set_exposure_time(self, exposure_time):
        pass

    @abc.abstractmethod
    def get_exposure_time(self):
        pass

    @abc.abstractmethod
    def setup_spectrometer(self):
        pass

    @abc.abstractmethod
    def get_temperature(self):
        pass

    @abc.abstractmethod
    def set_temperature(self, temperature):
        pass







