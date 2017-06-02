
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
    sigDataUpdated = QtCore.Signal()



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

        self.sigRunContinuous.connect(self.run_continuous)
        self.sigRunSingle.connect(self._scope.run_single)
        self.sigStop.connect(self.stop_aq)

        self.scopetime = np.arange(0,1,0.1)
        self.scopedata = [np.zeros([10]) for i in range(4)]

    def on_deactivate(self):
        """ Perform required deactivation. """

    def run_continuous(self):
        self._scope.run_continuous()

    def stop_aq(self):
        self._scope.stop_acquisition()

    def get_data(self):
        t, y = self._scope.aquire_data(self.get_channels())

        self.scopetime = t
        self.scopedata = y

        self.sigDataUpdated.emit()

    def get_timescale(self):
        return self.scopetime

    def get_channels(self):
        return self._scope.get_channels()

    def change_channel_state(self, channel, state):
        '''

        @param channel:
        @param state:
        @return:
        '''
        if state is 'on':
            self._scope.turn_on_channel(channel)
        else:
            self._scope.turn_off_channel(channel)









