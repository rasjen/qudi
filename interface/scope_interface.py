import abc
from core.util.interfaces import InterfaceMetaclass

class ScopeInterface(metaclass=InterfaceMetaclass):
    _modtype = 'ScopeInterface'
    _modclass = 'interface'

    @abc.abstractmethod
    def run_continuous(self):
        pass

    @abc.abstractmethod
    def run_single(self):
        pass

    @abc.abstractmethod
    def stop_acquisition(self):
        pass

    @abc.abstractmethod
    def get_channels(self):
        pass

    @abc.abstractmethod
    def turn_on_channel(self, channel):
        pass

    @abc.abstractmethod
    def turn_off_channel(self, channel):
        pass

