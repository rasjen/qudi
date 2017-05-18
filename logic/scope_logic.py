
from qtpy import QtCore
import numpy as np

from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex

class ScopeLogic(GenericLogic):
    """
    Control a process via software PID.
    """
    _modclass = 'scopelogic'
    _modtype = 'logic'
    ## declare connectors
    _connectors = {
        'scope': 'ScopeInterface',
        'savelogic': 'SaveLogic'
    }


    # General Signals, used everywhere:
    sigIdleStateChanged = QtCore.Signal(bool)
    sigPosChanged = QtCore.Signal(dict)


    sigRunContinuous = QtCore.Signal()
    sigRunSingle = QtCore.Signal()
    sigStop = QtCore.Signal()



    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.info('The following configuration was found.')

        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key,config[key]))

        # locking for thread safety
        self.threadlock = Mutex()

    def on_activate(self):
        self._scope = self.get_connector('scope')
        self._save_logic = self.get_connector('savelogic')

        self.sigRunContinuous.connect(self._scope.run_continuous)
        self.sigRunSingle.connect(self._scope.run_single)
        self.sigStop.connect(self._scope.stop)

    def on_deactivate(self):
        """ Perform required deactivation. """



