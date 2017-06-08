
from qtpy import QtCore
import numpy as np

from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from collections import OrderedDict
import time
import matplotlib.pyplot as plt

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

        self.scopetime = np.array(t)
        self.scopedata = np.array(y)

        self.sigDataUpdated.emit()

    def get_timescale(self):
        return self.scopetime

    def get_channels(self):
        return self._scope.get_channels()

    def get_time_range(self):
        return self._scope.get_time_range()

    def set_time_range(self, time_range):
        self._scope.set_time_range(time_range)

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


    def save_data(self):
        """ Save the counter trace data and writes it to a file.

        @param bool to_file: indicate, whether data have to be saved to file
        @param str postfix: an additional tag, which will be added to the filename upon save

        @return dict parameters: Dictionary which contains the saving parameters
        """



        filelabel = 'scope_trace'


        parameters = OrderedDict()
        parameters['Scope time'] = time.strftime('%d.%m.%Y %Hh:%Mmin:%Ss')

        self._data_to_save = np.vstack((self.scopetime, self.scopedata))
        header = 'Time (s)'
        for i, ch in enumerate(self.get_channels()):
            header = header + ',Channel{0} (V)'.format(i)

        data = {header: self._data_to_save.transpose()}
        filepath = self._save_logic.get_path_for_module(module_name='Scope')

        fig = self.draw_figure(data=np.array(self._data_to_save))
        self._save_logic.save_data(data, filepath=filepath, parameters=parameters,
                                       filelabel=filelabel, plotfig=fig, delimiter='\t')
        self.log.info('Scope Trace saved to:\n{0}'.format(filepath))

        return 0

    def draw_figure(self, data):
        """ Draw figure to save with data file.

        @param: nparray data: a numpy array containing counts vs time for all detectors

        @return: fig fig: a matplotlib figure object to be saved to file.
        """
        # Use qudi style
        plt.style.use(self._save_logic.mpl_qd_style)

        # Create figure
        fig, ax = plt.subplots()
        for i in range(len(data)-1):
            ax.plot(data[0], data[i+1], linestyle=':', linewidth=0.5)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Voltage (V)')
        return fig



    def _split_array(self, trigger_data, resonance_data,time_data):

        treshold = 1.5
        diff_trigger = np.diff(trigger_data ) > treshold
        indices = np.where(diff_trigger == True)

        split_time = np.split(time_data,indices[0])
        split_trigger = np.split(trigger_data,indices[0])
        split_data = np.split(resonance_data, indices[0])


        # first and last er not complete scans
        return split_time[1:-1], split_trigger[1:-1], split_data[1:-1]


    def analyse(self, trigger_channel=3, resonance_channel = 0,  cutoff = 15000):
        trigger_data = self.scopedata[trigger_channel]
        resonance_data = self.scopedata[resonance_channel]
        time_data = self.scopetime

        [split_time, split_trigger, self.split_data] = self._split_array(trigger_data, resonance_data, time_data)


        freq = 1.0 / np.abs(split_time[1][0] - split_time[1][-1])
        print('freq {}'.format(freq))

        cycles = len(self.split_data)
        t = np.linspace(0, 1/freq*cycles, cycles)
        pos1 = []
        pos2 = []
        for i in range(cycles):
            # only upward ramp
            firsthalf = self.split_data[i+1][0:int(len(split_time[0])/2)]
            firsthalf_time = self.split_time[i+1][0:int(len(split_time[0])/2)]
            #plt.figure(i+2)
            #plt.plot(firsthalf)
            #plt.show()
            # first resonance
            res1 = firsthalf[0:cutoff]
            #
            res2 = firsthalf[cutoff:]
            min_indices1 = np.argmin(res1)
            min_indices2 = np.argmin(res2)
            pos1.append(min_indices1)
            pos2.append(min_indices2)
        print(pos1, pos2)
        plt.figure(1)
        plt.plot(t*1e3,pos1-pos1[0])
        plt.plot(t*1e3,pos2-pos2[0])
        plt.xlabel('time (ms)')
        plt.ylabel('resonance position (arb)')
        plt.show()












