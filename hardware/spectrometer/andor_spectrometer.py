from core.module import Base
from interface.spectrometer_interface2 import SpectrometerInterface

class AndorSpectrometer(Base,SpectrometerInterface):
    """
    This module is controling the Andor spectrometer
        
    
    """

    def on_activate(self):
        """
        Activates the module
        
        :return: 
        """