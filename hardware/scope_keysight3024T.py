from core.module import Base
from interface.scope_interface import ScopeInterface
import visa
import string
import sys
import numpy as np
import matplotlib.pyplot as plt

class Scope3024T(Base, ScopeInterface):
    """
    This is the Interface class to define the controls for the simple
    microwave hardware.
    """
    _modclass = 'scopeinterface'
    _modtype = 'hardware'

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self.log.info('The following configuration was found.')
        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key, config[key]))
        self.rm = visa.ResourceManager()
        self.res = self.rm.list_resources()

    def on_activate(self):
        """
        Initialisation performed during activation of the module.
        """
        config = self.getConfiguration()
        self.scope = self.rm.open_resource(self.res[0])
        self.scope.timeout = 10000
        self.scope.read_termination = None
        self.scope.write_termination = '\n'
        print('Connected to ' + self.scope.query('*IDN?'))
        return

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        self.scope.close()
        self.rm.close()
        return


    # Save functions

    def set_saved_data_format(self, data_type):
        self._do_command(':WAVeform:FORMat {}'.format(data_type))

    def set_saved_data_source(self,channel):
        self._do_command(':WAVeform:SOURce CHANnel{}'.format(int(channel)))

    def set_save_data_unsigned_mode(self, unsigned_mode):
        self._do_command(':WAVeform:UNSigned {}'.format(str(unsigned_mode)))

    def set_save_data_point_maximum_mode(self):
        self._do_command(':WAVeform:POINTs:MODE MAXimum')

    def set_save_data_points_number(self, number_of_points):
        self._do_command(':WAVeform:POINTs {}'.format(int(number_of_points)))

    def get_channels_data(self):
        return self._do_query_binary_values('WAVeform:DATA?')

    def get_preamble(self):
        return self._do_query_ascii_values(':WAVeform:PREamble?')


    # General functions

    def auto_scale(self):
        self._do_command(":AUToscale")

    def run_continuous(self):
        self._do_command(':run')

    def single_acquisition(self):
        self._do_command(':SINGle')

    def stop_acquisition(self):
        self._do_command(':stop')

    def set_time_range(self, time_range):
        self._do_command(':Timebase:RANGe ' + str(time_range))

    def get_time_range(self):
        return self._do_query_ascii_values(':Timebase:RANGe?')

    def set_voltage_range(self, channel, voltage_range):
        self._do_command(':Channel{}:RANGe '.format(channel) + str(voltage_range) + 'V')

    def get_voltage_range(self, channel):
        return self._do_query_ascii_values(':Channel{}:Range?'.format(channel))

    def get_channel_vscale(self, channel):
        return "%0.E"% float(self._do_query('CHANnel{}:SCALe?'.format(channel)))

    def get_time_delay(self):
        return float(self._do_query(':TIMebase:DELay?'))

    def get_channel_coupling(self, channel):
        return self._do_query(':CHANnel{}:COUPling?'.format(channel))

    def get_display_status(self, channel):
        return self._do_query(':CHANnel{}:DISPlay?'.format(channel)).strip()

    def get_impedance_input(self, channel):
        return self._do_query('CHANnel{}:IMPedance?'.format(channel))

    def get_channel_offset(self, channel):
        return float(self._do_query('CHANnel{}:OFFSet?'.format(channel)))

    def get_save_data_points_number(self):
        return int(self._do_query(':WAVeform:POINts?'))

    # Acquisition functions

    def get_acquire_mode(self):
        return self._do_query(':ACQuire:TYPE?').strip()

    def acquire_mode_normal(self):
        self._do_command(':ACQuire:TYPE NORMal')

    def aqcuire_mode_highres(self):
        self._do_command(':ACQuire:TYPE HRESolution')

    def aqcuire_mode_peak(self):
        self._do_command(':ACQuire:TYPE PEAK')

    def aqcuire_mode_average(self):
        self._do_command(':ACQuire:TYPE AVERage')




    # Channel 1 functions

    def set_channel1_vscale(self, value):
        self._do_command('CHANnel1:SCALe {0:.1E}'.format(value))

    def set_channel1_DC_couling(self):
        self._do_command('CHANnel1:COUPling DC')

    def set_channel1_AC_couling(self):
        self._do_command('CHANnel1:COUPling AC')

    def set_channel1_impedance_input_50(self):
        self._do_command('CHANnel1:IMPedance FIFT')

    def set_channel1_impedance_input_1M(self):
        self._do_command('CHANnel1:IMPedance ONEM')

    def set_channel1_offset(self, value):
        self._do_command('CHANnel1:OFFSet {}'.format(value))



    # Channel 2 functions

    def set_channel2_vscale(self, value):
        self._do_command('CHANnel2:SCALe {0:.1E}'.format(value))

    def set_channel2_DC_couling(self):
        self._do_command('CHANnel2:COUPling DC')

    def set_channel2_AC_couling(self):
        self._do_command('CHANnel2:COUPling AC')

    def set_channel2_impedance_input_50(self):
        self._do_command('CHANnel2:IMPedance FIFT')

    def set_channel2_impedance_input_1M(self):
        self._do_command('CHANnel2:IMPedance ONEM')

    def set_channel2_offset(self, value):
        self._do_command('CHANnel2:OFFSet {}'.format(value))



    # Channel 3 functions

    def set_channel3_vscale(self, value):
        self._do_command('CHANnel3:SCALe {0:.1E}'.format(value))

    def set_channel3_DC_couling(self):
        self._do_command('CHANnel3:COUPling DC')

    def set_channel3_AC_couling(self):
        self._do_command('CHANnel3:COUPling AC')

    def set_channel3_impedance_input_50(self):
        self._do_command('CHANnel3:IMPedance FIFT')

    def set_channel3_impedance_input_1M(self):
        self._do_command('CHANnel3:IMPedance ONEM')

    def set_channel3_offset(self, value):
        self._do_command('CHANnel3:OFFSet {}'.format(value))


    # Channel 4 functions

    def set_channel4_vscale(self, value):
        self._do_command('CHANnel4:SCALe {0:.1E}'.format(value))

    def set_channel4_DC_couling(self):
        self._do_command('CHANnel4:COUPling DC')

    def set_channel4_AC_couling(self):
        self._do_command('CHANnel4:COUPling AC')

    def set_channel4_impedance_input_50(self):
        self._do_command('CHANnel4:IMPedance FIFT')

    def set_channel4_impedance_input_1M(self):
        self._do_command('CHANnel4:IMPedance ONEM')

    def set_channel4_offset(self, value):
        self._do_command('CHANnel4:OFFSet {}'.format(value))



    # All channels functions

    def turn_on_channel(self, channel):
        self._do_command(":Channel{}:DISPlay ON".format(int(channel)))

    def turn_off_channel(self, channel):
        self._do_command(":Channel{}:DISPlay OFF".format(int(channel)))



    # Trigger functions

    def set_trigger_mode(self, mode):
        self._do_command(':TRIGger:MODE {}'.format(mode))

    def set_trigger_source(self, mode, channel):
        self._do_command(':TRIGger:{0}:SOURCe CHANnel{1}'.format(mode, channel))

    def set_trigger_50(self):
        self._do_command(':TRIGger:LEVel:ASETup')

    def set_trigger_level(self, mode, value):
        self._do_command(':TRIGger:{0}:LEVel {1}'.format(mode, value))

    def get_trigger_mode(self):
        return self._do_query(':TRIGger:MODE?').strip()

    def get_trigger_source(self):
        return self._do_query('TRIGger:{}:SOURce?'.format(self.get_trigger_mode())).strip()

    def get_trigger_level(self):
        return float(self._do_query(':TRIGger:{}:LEVel?'.format(self.get_trigger_mode())).strip())

    def force_trigger(self):
         self._do_command(':TRIGger:FORCe')

    # Time
    def set_time_scale(self, value):
        self._do_command(':TIMebase:SCALe {}'.format(value))

    def get_time_scale(self):
        return "%0.E"% float(self._do_query(':TIMebase:SCALe?'))

    def set_time_delay(self, value):
        self._do_command(':TIMebase:DELay {}'.format(value))



    def get_screenshot_data(self):
        return self._do_query_binary_values(':DISPlay:DATA? PNG, COLOR')

    # =========================================================
    # Send a command and check for errors:
    # =========================================================
    def _do_command(self, command, hide_params=False):
        if hide_params:
            (header, data) = string.split(command, " ", 1)

        self.scope.write("{}".format(command))
        if hide_params:
            self._check_instrument_errors(header)
        else:
            self._check_instrument_errors(command)

    # =========================================================
    # Send a query, check for errors, return string:
    # =========================================================
    def _do_query(self, query):

        result = self.scope.query("{}".format(query))
        self._check_instrument_errors(query)
        return result

    # =========================================================
    # Send a query, check for errors, return values:
    # =========================================================
    def _do_query_values(self, query):

        results = self.scope.ask_for_values("{}".format(query))
        self._check_instrument_errors(query)
        return results

    # =========================================================
    # Send a query, check for errors, return values:
    # =========================================================

    def _do_query_ascii_values(self, query):

        results = self.scope.query_ascii_values("{}".format(query), container=np.array)
        self._check_instrument_errors(query)
        return results

    # =========================================================
    # Send a query, check for errors, return values:
    # =========================================================

    def _do_query_binary_values(self, query):

        results = self.scope.query_binary_values("{}".format(query), datatype='B') #container=np.array, is_big_endian=False,
        self._check_instrument_errors(query)
        return results

    # =========================================================
    # Check for instrument errors:
    # =========================================================
    def _check_instrument_errors(self, command):
        while True:
            error_string = self.scope.ask(":SYSTem:ERRor?")

            if error_string:  # If there is an error string value.
                if error_string.find("+0,", 0, 3) == -1:  # Not "No error".
                    print("ERROR: {}, command: '{}'".format(error_string, command))
                    print("Exited because of error.")
                    sys.exit(1)
                else:
                    break

            else:  # :SYSTem:ERRor? should always return string.
                print("ERROR: :SYSTem:ERRor? returned nothing, command: '{}'".format(command))
                print("Exited because of error.")
                sys.exit(1)
