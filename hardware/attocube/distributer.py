from hardware.attocube.attocube import Attocube
from hardware.attocube.nicard_digital import NIcard
from interface.confocal_scanner_atto_interface import ConfocalScannerInterfaceAtto
from core.base import Base

import numpy as np
import time

class Distributer(Base,ConfocalScannerInterfaceAtto):

    _modtype = 'distributer'
    _modclass = 'hardware'

    _connectors = {
            'confocalscanner': 'ConfocalScannerInterfaceAtto'
            }

    def on_activate(self, e):
        Attocube.on_activate(self)
        NIcard.on_activate(self)
        [self.x_start, self.y_start, self.z_start] = Attocube.get_scanner_position_abs(self)

    def on_deactivate(self, e):
        Attocube.on_deactivate(self)
        NIcard.on_deactivate(self)

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs
            can access it.

        @return int: error code (0:OK, -1:error)
        """
        Attocube.reset_hardware(self)
        NIcard.reset_hardware(self)

    def get_position_range(self):
        """ Returns the physical range of the scanner.

        @return float [4][2]: array of 4 ranges with an array containing lower
                              and upper limit
        """
        return Attocube.get_position_range(self)

    def set_position_range(self, myrange=None):
        """ Sets the physical range of the scanner.

        @param float [4][2] myrange: array of 4 ranges with an array containing
                                     lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        Attocube.set_position_range(self)


    def get_scanner_axes(self):
        """ Find out how many axes the scanning device is using for confocal and their names.

        @return list(str): list of axis names

        Example:
          For 3D confocal microscopy in cartesian coordinates, ['x', 'y', 'z'] is a sensible value.
          For 2D, ['x', 'y'] would be typical.
          You could build a turntable microscope with ['r', 'phi', 'z'].
          Most callers of this function will only care about the number of axes, though.

          On error, return an empty list.
        """
        return Attocube.get_scanner_axes(self)


    def get_scanner_count_channels(self):
        """ Returns the list of channels that are recorded while scanning an image.

        @return list(str): channel names

        Most methods calling this might just care about the number of channels.
        """
        return NIcard.get_scanner_count_channels(self)


    def set_up_scanner_clock(self, clock_frequency=None, clock_channel=None):
        """ Configures the hardware clock of the NiDAQ card to give the timing.

        @param float clock_frequency: if defined, this sets the frequency of the
                                      clock
        @param str clock_channel: if defined, this is the physical channel of
                                  the clock

        @return int: error code (0:OK, -1:error)
        """
        return NIcard.set_up_scanner_clock(self, clock_frequency=clock_frequency, clock_channel=clock_channel)


    def set_up_scanner(self,
                       counter_channels=None,
                       sources=None,
                       clock_channel=None,
                       scanner_ao_channels=None):
        """ Configures the actual scanner with a given clock.

        @param str counter_channels: if defined, these are the physical conting devices
        @param str sources: if defined, these are the physical channels where
                                  the photons are to count from
        @param str clock_channel: if defined, this specifies the clock for the
                                  counter
        @param str scanner_ao_channels: if defined, this specifies the analoque
                                        output channels

        @return int: error code (0:OK, -1:error)
        """
        try:
            Attocube.enable_trigger_input(self)
            [self.x_start, self.y_start, self.z_start] = Attocube.get_scanner_position_abs(self)
            Attocube.enable_outputs(self)
            return 0
        except:
            return -1
        #return NIcard.set_up_scanner(self, counter_channels=counter_channels, sources= sources, clock_channel=clock_channel, scanner_do_channels=scanner_ao_channels)

    def scanner_set_position_abs(self, x=None, y=None, z=None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)
        @param float a: postion in a-direction (volts)

        @return int: error code (0:OK, -1:error)
        """
        return Attocube.scanner_set_position_abs(self, x=x, y=y, z=z)

    def scanner_set_position(self, x=None, y=None, z=None, a=None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)
        @param float a: postion in a-direction (volts)

        @return int: error code (0:OK, -1:error)
        """
        try:
            x_abs = self.x_start + (x * 1e-6)
            y_abs = self.y_start + (y * 1e-6)
            z_abs = self.z_start# + (z * 1e-6)
            return self.scanner_set_position_abs(x=x_abs, y=y_abs, z=z_abs)
            print('hej6')
        except:
            self.log.error('can not make go to this position since ')

    def get_scanner_position(self):
        """ Get the current position of the scanner hardware.

        @return float[n]: current position in (x, y, z, a).
        """
        return NIcard.get_scanner_position(self)

    def get_scanner_position_abs(self):
        """ Get the current position of the scanner hardware.

        @return float[n]: current position in (x, y, z, a).
        """
        return Attocube.get_scanner_position_abs(self)

    def set_up_line(self, length=100):
        """ Sets up the analoque output for scanning a line.

        @param int length: length of the line in pixel

        @return int: error code (0:OK, -1:error)
        """
        return NIcard.set_up_line(self, length=length)

    def scan_line(self, line_path=None):
        """ Scans a line and returns the counts on that line.

        @param float[k][n] line_path: array k of n-part tuples defining the pixel positions

        @return float[k][m]: the photon counts per second for k pixels with m channels
        """


        Attocube.set_target_range(self,'x', 0.4e-6)
        Attocube.set_target_range(self,'y', 0.4e-6)

        self._counting_samples = 1

        [x, y, z] = Attocube.get_scanner_position_abs(self)
        x_pos = np.round(np.array(line_path[0])*1e-6+self.x_start,6)
        y_pos = np.round(np.array(line_path[1])*1e-6+self.y_start,6)
        line_counts = np.zeros_like([line_path[0],])


        rawdata = np.zeros( (len(self.get_channels()), self._counting_samples))


        for i in range(len(x_pos)):
            if i ==0 :
                rawdata = NIcard.get_counter(self, samples= self._counting_samples)
            else:
                if x_pos[i] != x_pos[i-1]:
                    Attocube.set_target_position(self,'x',x_pos[i])
                    Attocube.auto_move(self,'x',1)

                if y_pos[i] != y_pos[i-1]:
                    Attocube.set_target_position(self,'y',y_pos[i])
                    Attocube.auto_move(self,'y',1)

                try:
                    rawdata = NIcard.get_counter(self, samples= self._counting_samples)
                except:
                    self.log.error('No counter running')
                    return -1
            line_counts[0,i] = rawdata.sum()

        print(np.round(x_pos[0]*1e6,1),np.round(x_pos[-1]*1e6,1))
        print(np.round(y_pos[0]*1e6,1),np.round(y_pos[-1]*1e6,1))

        return line_counts.transpose()

     # def scan_line(self, line_path=None):
     #    """ Scans a line and returns the counts on that line.
     #
     #    @param float[k][n] line_path: array k of n-part tuples defining the pixel positions
     #
     #    @return float[k][m]: the photon counts per second for k pixels with m channels
     #    """
     #
     #    return NIcard.scan_line(self,line_path=line_path)

    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        try:
            Attocube.disable_outputs(self)
            Attocube.auto_move(self, 'x', enable=0)
            Attocube.auto_move(self, 'y', enable=0)
            return 0
        except:
            return -1

    def close_scanner_clock(self, power=0):
         """ Closes the clock and cleans up afterwards.

         @return int: error code (0:OK, -1:error)
         """
         return NIcard.close_scanner_clock(self)

    def single_step(self, axis='x', direction='forward'):
        '''

        :param axis: 'x', 'y' 'z'
        :param direction: 'forward' or 'backward'
        :return:
        '''
        Attocube.single_step(self, axis, direction)


    def set_up_clock(self, clock_frequency=None, clock_channel=None, scanner=False, idle=False):
        return NIcard.set_up_clock(self, clock_frequency=clock_frequency, clock_channel=clock_channel, scanner=scanner, idle=idle)

    def _start_digital_output(self):
        return NIcard._start_digital_output(self)

    def _stop_digital_output(self):
        return NIcard._stop_digital_output(self)

    def _write_scanner_do(self, step_data=None ,length=100, start=False):
        return NIcard._write_scanner_do(self, step_data=step_data, length=length, start=start)

    def close_clock(self, scanner=False):
        return NIcard.close_clock(self, scanner=scanner)

    def close_counter(self, scanner=False):
        return NIcard.close_counter(self, scanner=scanner)

    def get_constraints(self):
        return NIcard.get_constraints(self)

    def enable_outputs(self):
        Attocube.enable_outputs(self)

    def disable_outputs(self):
        Attocube.disable_outputs(self)

    def axis_output_status(self, axis, status='off' ):
        Attocube.axis_output_status(self, axis, status=status)


    def set_frequency(self, axis, freq):
        '''

        :param axis: 'x', 'y' 'z'
        :param freq: Frequency in Hz, internal resolution is 1 Hz
        :return:
        '''
        Attocube.set_frequency(self, axis, freq)

    def set_amplitude(self, axis, amp):
        '''

        :param axis: 'x', 'y' 'z'
        :param amp: Amplitude in V, internal resolution is 1 mV
        :return:
        '''
        Attocube.set_amplitude(self, axis, amp)

    def _scanner_position_to_step(self, line_path):
         return NIcard._scanner_position_to_step(self, line_path=line_path)


    def get_channels(self):
        """ Shortcut for hardware get_counter_channels.

            @return list(str): return list of active counter channel names
        """
        return NIcard.get_counter_channels(self)


    def get_counter_channels(self):
        """ Returns the list of counter channel names.

        @return tuple(str): channel names

        Most methods calling this might just care about the number of channels, though.
        """
        return self._counter_channels

    def set_up_counter(self):
        try:
            self.count_frequency = 100
            self._count_length = 10
            NIcard.set_up_clock(self, clock_frequency=self.count_frequency)
            NIcard.set_up_counter(self, counter_buffer=self._count_length)
            return 0
        except:
            return -1
