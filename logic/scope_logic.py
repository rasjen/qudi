
from qtpy import QtCore
import numpy as np

from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from collections import OrderedDict
import time

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
        self.active_channels = []

    def on_deactivate(self):
        """ Perform required deactivation. """

    def run_continuous(self):
        self._scope.run_continuous()

    def stop_aq(self):
        self._scope.stop_acquisition()

    def get_data(self):
        t, y = self._scope.aquire_data(self.active_channels)

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
            self.active_channels.append(channel)
        else:
            self._scope.turn_off_channel(channel)
            self.active_channels.remove(channel)


    def save_data(self, to_file=True, postfix=''):
        """ Save the counter trace data and writes it to a file.

        @param bool to_file: indicate, whether data have to be saved to file
        @param str postfix: an additional tag, which will be added to the filename upon save

        @return dict parameters: Dictionary which contains the saving parameters
        """
        # stop saving thus saving state has to be set to False

        if to_file:
            # If there is a postfix then add separating underscore
            if postfix == '':
                filelabel = 'scope_trace'
            else:
                filelabel = 'scope_trace_' + postfix

            parameters = OrderedDict()
            parameters['Scope time'] = time.strftime('%d.%m.%Y %Hh:%Mmin:%Ss', time.localtime(self._saving_start_time))

            self.data_to_save = [self.scopetime, self.scopedata]
            data = self._data_to_save
            filepath = self._save_logic.get_path_for_module(module_name='Scope')

            fig = self.draw_figure(data=np.array(self._data_to_save))
            self._save_logic.save_data(data, filepath=filepath, parameters=parameters,
                                       filelabel=filelabel, plotfig=fig, delimiter='\t')
            self.log.info('Scope Trace saved to:\n{0}'.format(filepath))

        return self._data_to_save, parameters








