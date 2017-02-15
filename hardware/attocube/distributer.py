from hardware.attocube.attocube import Attocube
from hardware.attocube.nicard_digital import NIcard
from interface.confocal_scanner_atto_interface import ConfocalScannerInterfaceAtto
from core.base import Base

class Distributer(Base,ConfocalScannerInterfaceAtto):

    _modtype = 'distributer'
    _modclass = 'hardware'

    _out = {
            'confocalscanner': 'ConfocalScannerInterfaceAtto'
            }

    def on_activate(self, e):
        Attocube.on_activate(self)
        NIcard.on_activate(self)


    def on_deactivate(self, e):
        Attocube.on_deactivate(self)
        NIcard.on_deactivate(self)
        pass

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
        Attocube.get_position_range(self)

    def set_position_range(self, myrange=None):
        """ Sets the physical range of the scanner.

        @param float [4][2] myrange: array of 4 ranges with an array containing
                                     lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        Attocube.get_position_range(self)


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
        Attocube.get_scanner_axes(self)


    def get_scanner_count_channels(self):
        """ Returns the list of channels that are recorded while scanning an image.

        @return list(str): channel names

        Most methods calling this might just care about the number of channels.
        """
        NIcard.get_scanner_count_channels(self)


    def set_up_scanner_clock(self, clock_frequency=None, clock_channel=None):
        """ Configures the hardware clock of the NiDAQ card to give the timing.

        @param float clock_frequency: if defined, this sets the frequency of the
                                      clock
        @param str clock_channel: if defined, this is the physical channel of
                                  the clock

        @return int: error code (0:OK, -1:error)
        """
        pass


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
        pass

    def scanner_set_position(self, x=None, y=None, z=None, a=None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)
        @param float a: postion in a-direction (volts)

        @return int: error code (0:OK, -1:error)
        """
        pass

    def get_scanner_position(self):
        """ Get the current position of the scanner hardware.

        @return float[n]: current position in (x, y, z, a).
        """
        pass

    def set_up_line(self, length=100):
        """ Sets up the analoque output for scanning a line.

        @param int length: length of the line in pixel

        @return int: error code (0:OK, -1:error)
        """
        pass

    def scan_line(self, line_path=None):
        """ Scans a line and returns the counts on that line.

        @param float[k][n] line_path: array k of n-part tuples defining the pixel positions

        @return float[k][m]: the photon counts per second for k pixels with m channels
        """
        pass

    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        pass

    def close_scanner_clock(self, power=0):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        pass

    def single_step(self, axis='x', direction='forward'):
        '''

        :param axis:
        :param direction:
        :return:
        '''
        Attocube.enable_outputs(self)
        Attocube.single_step(self, axis, direction)
        Attocube.disable_outputs(self)
