from qtpy import QtCore
import numpy as np

from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
import matplotlib.pyplot as plt
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
    screenshotDataUpdated = QtCore.Signal()

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
        self.sigRunSingle.connect(self._scope.single_acquisition)
        self.sigStop.connect(self.stop_acquisition)
        self.scopetime = np.arange(0,1,0.1)
        self.scopedata = [np.zeros([10]) for i in range(4)]
        self.active_channels = []
        self.acquisition_mode = self.get_acquire_mode()

    def on_deactivate(self):
        """ Perform required deactivation. """

    def get_displayed_channels(self):
        displayed_channels = []
        n=1
        while n <= 4 :
            if self._scope.get_display_status(n) == '1':
                displayed_channels.append(n)
                n += 1
            else :
                n += 1
        return displayed_channels

    # General functions

    def run_continuous(self):
        self._scope.run_continuous()

    def stop_acquisition(self):
        self._scope.stop_acquisition()

    def single_acquisition(self):
        self._scope.single_acquisition()

    def auto_scale(self):
        self._scope.auto_scale()




    # Channel 1 functions

    def set_channel1_DC_couling(self):
        self._scope.set_channel1_DC_couling()

    def set_channel1_AC_couling(self):
        self._scope.set_channel1_AC_couling()

    def set_channel1_vscale(self, value):
        self._scope.set_channel1_vscale(value)

    def set_channel1_impedance_input_50(self):
        self._scope.set_channel1_impedance_input_50()

    def set_channel1_impedance_input_1M(self):
        self._scope.set_channel1_impedance_input_1M()



    # Channel 2 functions

    def set_channel2_DC_couling(self):
        self._scope.set_channel2_DC_couling()

    def set_channel2_AC_couling(self):
        self._scope.set_channel2_AC_couling()

    def set_channel2_vscale(self, value):
        self._scope.set_channel2_vscale(value)

    def set_channel2_impedance_input_50(self):
        self._scope.set_channel2_impedance_input_50()

    def set_channel2_impedance_input_1M(self):
        self._scope.set_channel2_impedance_input_1M()




    # Channel 3 functions

    def set_channel3_DC_couling(self):
        self._scope.set_channel3_DC_couling()

    def set_channel3_AC_couling(self):
        self._scope.set_channel3_AC_couling()

    def set_channel3_vscale(self, value):
        self._scope.set_channel3_vscale(value)

    def set_channel3_impedance_input_50(self):
        self._scope.set_channel3_impedance_input_50()

    def set_channel3_impedance_input_1M(self):
        self._scope.set_channel3_impedance_input_1M()




    # Channel 4 functions

    def set_channel4_DC_couling(self):
        self._scope.set_channel4_DC_couling()

    def set_channel4_AC_couling(self):
        self._scope.set_channel4_AC_couling()

    def set_channel4_vscale(self, value):
        self._scope.set_channel4_vscale(value)

    def set_channel4_impedance_input_50(self):
        self._scope.set_channel4_impedance_input_50()

    def set_channel4_impedance_input_1M(self):
        self._scope.set_channel4_impedance_input_1M()



    # Trigger functions

    def set_trigger_source(self, mode, channel):
        self._scope.set_trigger_source(mode, channel)

    def set_trigger_mode(self, mode):
        self._scope.set_trigger_mode(mode)

    def set_trigger_50(self):
        self._scope.set_trigger_50()

    def set_trigger_level(self, mode, value):
        self._scope.set_trigger_level(mode, value)

    # Acquire functions

    def get_acquire_mode(self):
        return self._scope.get_acquire_mode()

    def set_acquire_mode_normal(self):
        self._scope.acquire_mode_normal()

    def set_aqcuire_mode_highres(self):
        self._scope.aqcuire_mode_highres()

    def set_aqcuire_mode_peak(self):
        self._scope.aqcuire_mode_peak()

    def set_aqcuire_mode_average(self):
        self._scope.aqcuire_mode_average()

    def get_data(self):
        t, y = self._scope.aquire_data(self.active_channels)
        self.scopetime = np.array(t)
        self.scopedata = np.array(y)
    #    self.sigDataUpdated.emit()

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
        if state is 'ON':
            self._scope.turn_on_channel(channel)
            self.active_channels.append(channel)
        else:
            self._scope.turn_off_channel(channel)
            self.active_channels.remove(channel)

    def set_time_scale(self, value):
        self._scope.set_time_scale(value)

    def set_time_delay(self, value):
        self._scope.set_time_delay(value)

    def set_channel1_offset(self, value):
        self._scope.set_channel1_offset(value)

    def set_channel2_offset(self, value):
        self._scope.set_channel2_offset(value)

    def set_channel3_offset(self, value):
        self._scope.set_channel3_offset(value)

    def set_channel4_offset(self, value):
        self._scope.set_channel4_offset(value)

    def get_screenshot_data(self):
        data_screenshot = self._scope.get_screenshot_data()
        newfile=open('screenshot.png','wb')
        newfile.write(bytearray(data_screenshot))
        newfile.close()
        self.screenshotDataUpdated.emit()

    def get_channel_vscale(self, channel):
        return self._scope.get_channel_vscale(channel)

    def get_channel_coupling(self, channel):
        return self._scope.get_channel_coupling(channel)

    def get_display_status(self, channel):
        return self._scope.get_display_status(channel)

    def get_impedance_input(self, channel):
        return self._scope.get_impedance_input(channel)

    def get_channel_offset(self, channel):
        return self._scope.get_channel_offset(channel)

    def get_time_scale(self):
        return self._scope.get_time_scale()

    def get_time_delay(self):
        return self._scope.get_time_delay()

    def get_trigger_mode(self):
        return self._scope.get_trigger_mode()

    def get_trigger_source(self):
        return self._scope.get_trigger_source()

    def get_trigger_level(self):
        return self._scope.get_trigger_level()



    def get_save_data_points_number(self):
        return self._scope.get_save_data_points_number()

    def _convert_y_data(self, data, preamble):
        return (data - preamble[9]) * preamble[7] + preamble[8]

    def _convert_t_data(self, data, preamble):
        t = np.linspace(0, len(data) - 1, len(data))
        return (t - preamble[6]) * preamble[4] + preamble[5]

    def get_data(self):
        '''Get data from all the channels of the scope (displayed or not)
        Data format : [time (s), Channel 1 (V), Channel 2 (V), Channel 3 (V), Channel 4 (V),]
        '''
        self._scope.set_saved_data_format('BYTE')
        self._scope.set_save_data_unsigned_mode(1)
        self._scope.set_save_data_point_maximum_mode()
        self._scope.set_save_data_points_number(8000000)
        n=1
        while n<=4:
            self._scope.set_saved_data_source(n)
            data_channel = self._scope.get_channels_data()
            preamble_channel = self._scope.get_preamble()
            data_channel = self._convert_y_data(data_channel, preamble_channel)
            data_time = self._convert_t_data(data_channel, preamble_channel)
            if n == 1:
                data = [data_time, data_channel]
            else:
                data.append(data_channel)
            n += 1
        return data

    def save_data(self):
        self.time = time.gmtime()
        filename = 'scope_trace' + '_' + str(self.time[0]) + '_' + str(self.time[1])+ '_' + str(self.time[2])+ '_' + str(self.time[3]+2)+ '_' + str(self.time[4])+ '_' + str(self.time[5]) + '.txt'
        data_to_save = self.get_data()
        print(type(data_to_save))
        filepath = self._save_logic.get_path_for_module(module_name='scope')
        np.savetxt(filepath + filename, data_to_save, fmt='%.18e', delimiter=' ', newline='\n', header='', footer='', comments='# ')
        self.log.info('Scope Trace saved to:{0}'.format(filepath))
        return 0
