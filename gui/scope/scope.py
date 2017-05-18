from gui.guibase import GUIBase
from qtpy import QtWidgets
from qtpy import QtCore
from qtpy import uic
import numpy as np
import os

class ScopeWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'scope_gui.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class ScopeGUI(GUIBase):
    '''
    This is a simple oscilloscope gui
    '''
    _modclass = 'scopegui'
    _modtype = 'gui'

    ## declare connectors
    _connectors = {'scopelogic': 'ScopeLogic'}

    sigStart = QtCore.Signal()
    sigStop = QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.info('The following configuration was found.')

        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key, config[key]))

    def on_activate(self):
        """ Definition and initialisation of the GUI plus staring the measurement.

        """
        self._scope_logic = self.get_connector('scopelogic')

        self._mw = ScopeWindow()

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

