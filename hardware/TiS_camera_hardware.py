from VideoCapture import Device
from core.module import Base
from interface.empty_interface import EmptyInterface

class TiS_Camera(Base, EmptyInterface):
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

    def on_activate(self):
        """
        Initialisation performed during activation of the module.
        """
        return

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        return