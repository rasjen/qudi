# -*- coding: utf-8 -*-
"""
This module operates a confocal microsope.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

from qtpy import QtCore
from collections import OrderedDict
from copy import copy
from datetime import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from io import BytesIO

from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex


def numpy_from_b(compressed_b):
    f = BytesIO(bytes(compressed_b))
    np_file = np.load(f)
    redict = dict()
    for name in np_file.files:
        redict.update({name: np_file[name]})
    f.close()
    return redict


class OldConfigFileError(Exception):
    def __init__(self):
        super().__init__('Old configuration file detected. Ignoring history.')


class ConfocalHistoryEntry(QtCore.QObject):
    """ This class contains all relevant parameters of a Confocal scan.
        It provides methods to extract, restore and serialize this data.
    """

    def __init__(self, confocal):
        """ Make a confocal data setting with default values. """
        super().__init__()

        self.xy_line_pos = 0


        # Reads in the maximal scanning range. The unit of that scan range is meters!
        self.x_range = confocal._scanning_device.get_position_range()[0]
        self.y_range = confocal._scanning_device.get_position_range()[1]


        # Sets the current position to the center of the maximal scanning range
        self.current_x = (self.x_range[0] + self.x_range[1]) / 2
        self.current_y = (self.y_range[0] + self.y_range[1]) / 2

        # Sets the size of the image to the maximal scanning range
        self.image_x_range = self.x_range
        self.image_y_range = self.y_range

        # Default values for the resolution of the scan
        self.xy_resolution = 100


        # Initialization of internal counter for scanning
        self.xy_line_position = 0


        # Variable to check if a scan is continuable
        self.xy_scan_continuable = False


    def restore(self, confocal):
        """ Write data back into confocal logic and pull all the necessary strings """
        confocal._current_x = self.current_x
        confocal._current_y = self.current_y
        confocal.image_x_range = np.copy(self.image_x_range)
        confocal.image_y_range = np.copy(self.image_y_range)
        confocal.xy_resolution = self.xy_resolution
        confocal._xy_line_pos = self.xy_line_position
        confocal._xyscan_continuable = self.xy_scan_continuable



        confocal.initialize_image()
        try:
            if confocal.xy_image.shape == self.xy_image.shape:
                confocal.xy_image = np.copy(self.xy_image)
        except AttributeError:
            self.xy_image = np.copy(confocal.xy_image)


    def snapshot(self, confocal):
        """ Extract all necessary data from a confocal logic and keep it for later use """
        self.current_x = confocal._current_x
        self.current_y = confocal._current_y
        self.image_x_range = np.copy(confocal.image_x_range)
        self.image_y_range = np.copy(confocal.image_y_range)
        self.xy_resolution = confocal.xy_resolution
        self.xy_line_position = confocal._xy_line_pos
        self.xy_scan_continuable = confocal._xyscan_continuable
        self.xy_image = np.copy(confocal.xy_image)


    def serialize(self):
        """ Give out a dictionary that can be saved via the usual means """
        serialized = dict()
        serialized['focus_position'] = [self.current_x, self.current_y]
        serialized['x_range'] = list(self.image_x_range)
        serialized['y_range'] = list(self.image_y_range)
        serialized['xy_resolution'] = self.xy_resolution
        serialized['xy_line_position'] = self.xy_line_position
        serialized['xy_scan_cont'] = self.xy_scan_continuable
        serialized['xy_image'] = self.xy_image
        return serialized

    def deserialize(self, serialized):
        """ Restore Confocal history object from a dict """
        if 'focus_position' in serialized and len(serialized['focus_position']) == 4:
            self.current_x = serialized['focus_position'][0]
            self.current_y = serialized['focus_position'][1]
        if 'x_range' in serialized and len(serialized['x_range']) == 2:
            self.image_x_range = serialized['x_range']
        if 'y_range' in serialized and len(serialized['y_range']) == 2:
            self.image_y_range = serialized['y_range']
        if 'xy_resolution' in serialized:
            self.xy_resolution = serialized['xy_resolution']
        if 'xy_image' in serialized:
            if isinstance(serialized['xy_image'], np.ndarray):
                self.xy_image = serialized['xy_image']
            else:
                try:
                    self.xy_image = numpy_from_b(
                            eval(serialized['xy_image']))['image']
                except:
                    raise OldConfigFileError()



class ScanLogic(GenericLogic):
    """
    This is the Logic class for confocal scanning.
    """
    _modclass = 'confocallogic'
    _modtype = 'logic'

    # declare connectors
    _in = {
        'scanner1': 'ScannerInterface',
        'counter1': 'ClockNCounterInterface'
        }
    _out = {'scannerlogic': 'ConfocalLogic'}

    # signals
    signal_start_scanning = QtCore.Signal(str)
    signal_continue_scanning = QtCore.Signal(str)
    signal_stop_scanning = QtCore.Signal()
    signal_scan_lines_next = QtCore.Signal()
    signal_xy_image_updated = QtCore.Signal()
    signal_change_position = QtCore.Signal(str)
    signal_xy_data_saved = QtCore.Signal()
    signal_draw_figure_completed = QtCore.Signal()
    signal_position_changed = QtCore.Signal()

    sigImageXYInitialized = QtCore.Signal()

    signal_history_event = QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self.log.info('The following configuration was found.')

        # checking for the right configuration
        for key in config.keys():
            self.log.info('{0}: {1}'.format(key, config[key]))

        #locking for thread safety
        self.threadlock = Mutex()

        # counter for scan_image
        self._scan_counter = 0
        self.stopRequested = False
        self.permanent_scan = False

    def on_activate(self, e):
        """ Initialisation performed during activation of the module.

        @param e: error code
        """
        self._scanning_device = self.get_in_connector('scanner1')
        self._counter_device = self.get_in_connector('counter1')
        #self._save_logic = self.get_in_connector('savelogic')

        #default values for clock frequency and slowness
        #slowness: steps during retrace line
        if 'clock_frequency' in self._statusVariables:
            self._clock_frequency = self._statusVariables['clock_frequency']
        else:
            self._clock_frequency = 500
        if 'return_slowness' in self._statusVariables:
            self.return_slowness = self._statusVariables['return_slowness']
        else:
            self.return_slowness = 50

        # Reads in the maximal scanning range. The unit of that scan range is micrometer!
        self.x_range = self._scanning_device.get_position_range()[0]
        self.y_range = self._scanning_device.get_position_range()[1]

        # restore here ...
        self.history = []
        if 'max_history_length' in self._statusVariables:
                self.max_history_length = self._statusVariables['max_history_length']
                for i in reversed(range(1, self.max_history_length)):
                    try:
                        new_history_item = ConfocalHistoryEntry(self)
                        new_history_item.deserialize(
                            self._statusVariables['history_{0}'.format(i)])
                        self.history.append(new_history_item)
                    except KeyError:
                        pass
                    except OldConfigFileError:
                        self.log.warning(
                            'Old style config file detected. History {0} ignored.'.format(i))
                    except:
                        self.log.warning(
                                'Restoring history {0} failed.'.format(i))
        else:
            self.max_history_length = 10
        try:
            new_state = ConfocalHistoryEntry(self)
            new_state.deserialize(self._statusVariables['history_0'])
            new_state.restore(self)
        except:
            new_state = ConfocalHistoryEntry(self)
            new_state.restore(self)
        finally:
            self.history.append(new_state)

        self.history_index = len(self.history) - 1

        # Sets connections between signals and functions
        self.signal_scan_lines_next.connect(self._scan_line, QtCore.Qt.QueuedConnection)
        self.signal_start_scanning.connect(self.start_scanner, QtCore.Qt.QueuedConnection)
        self.signal_continue_scanning.connect(self.continue_scanner, QtCore.Qt.QueuedConnection)
        self._change_position('activation')

    def on_deactivate(self, e):
        """ Reverse steps of activation

        @param e: error code

        @return int: error code (0:OK, -1:error)
        """
        self._statusVariables['clock_frequency'] = self._clock_frequency
        self._statusVariables['return_slowness'] = self.return_slowness
        self._statusVariables['max_history_length'] = self.max_history_length
        closing_state = ConfocalHistoryEntry(self)
        closing_state.snapshot(self)
        self.history.append(closing_state)
        histindex = 0
        for state in reversed(self.history):
            self._statusVariables['history_{0}'.format(histindex)] = state.serialize()
            histindex += 1
        return 0

    def switch_hardware(self, to_on=False):
        """ Switches the Hardware off or on.

        @param to_on: True switches on, False switched off

        @return int: error code (0:OK, -1:error)
        """
        if to_on:
            return self._scanning_device.activation()
        else:
            return self._scanning_device.reset_hardware()

    def set_clock_frequency(self, clock_frequency):
        """Sets the frequency of the clock

        @param int clock_frequency: desired frequency of the clock

        @return int: error code (0:OK, -1:error)
        """
        self._clock_frequency = int(clock_frequency)
        #checks if scanner is still running
        if self.getState() == 'locked':
            return -1
        else:
            return 0

    def start_scanning(self, tag='logic'):
        """Starts scanning

        @param bool zscan: zscan if true, xyscan if false

        @return int: error code (0:OK, -1:error)
        """
        # TODO: this is dirty, but it works for now
#        while self.getState() == 'locked':
#            time.sleep(0.01)
        self._scan_counter = 0
        
        self._xyscan_continuable = True

        self.signal_start_scanning.emit(tag)
        return 0

    def continue_scanning(self,tag='logic'):
        """Continue scanning

        @return int: error code (0:OK, -1:error)
        """
      
        self._scan_counter = self._xy_line_pos
        self.signal_continue_scanning.emit(tag)
        return 0

    def stop_scanning(self):
        """Stops the scan

        @return int: error code (0:OK, -1:error)
        """
        with self.threadlock:
            if self.getState() == 'locked':
                self.stopRequested = True
        self.signal_stop_scanning.emit()
        return 0

    def initialize_image(self):
        """Initalization of the image.

        @return int: error code (0:OK, -1:error)
        """
        # x1: x-start-value, x2: x-end-value
        x1, x2 = self.image_x_range[0], self.image_x_range[1]
        # y1: x-start-value, y2: x-end-value
        y1, y2 = self.image_y_range[0], self.image_y_range[1]

        # Checks if the x-start and x-end value are ok
        if x2 < x1:
            self.log.error(
                'x1 must be smaller than x2, but they are '
                '({0:.3f},{1:.3f}).'.format(x1, x2))
            return -1

        
        # Checks if the y-start and y-end value are ok
        if y2 < y1:
            self.log.error(
				'y1 must be smaller than y2, but they are '
				'({0:.3f},{1:.3f}).'.format(y1, y2))
            return -1

        # prevents distorion of the image
        if (x2 - x1) >= (y2 - y1):
            self._X = np.linspace(x1, x2, max(self.xy_resolution, 2))
            self._Y = np.linspace(y1, y2, max(int(self.xy_resolution*(y2-y1)/(x2-x1)), 2))
        else:
            self._Y = np.linspace(y1, y2, max(self.xy_resolution, 2))
            self._X = np.linspace(x1, x2, max(int(self.xy_resolution*(x2-x1)/(y2-y1)), 2))

        self._XL = self._X
        self._YL = self._Y
        self._AL = np.zeros(self._XL.shape)

        # Arrays for retrace line
        self._return_XL = np.linspace(self._XL[-1], self._XL[0], self.return_slowness)
        self._return_AL = np.zeros(self._return_XL.shape)


        self._image_vert_axis = self._Y
        # creats an image where each pixel will be [x,y,counts]
        self.xy_image = np.zeros(
                (len(self._image_vert_axis),
                len(self._X),
                2 + len(self.get_scanner_count_channels())))
        self.xy_image[:, :, 0] = np.full((len(self._image_vert_axis), len(self._X)), self._XL)
        y_value_matrix = np.full((len(self._X), len(self._image_vert_axis)), self._Y)
        self.xy_image[:, :, 1] = y_value_matrix.transpose()
        self.sigImageXYInitialized.emit()
        return 0

    def start_scanner(self):
        """Setting up the scanner device and starts the scanning procedure

        @return int: error code (0:OK, -1:error)
        """
        self.lock()

        self._scanning_device.lock()
        if self.initialize_image() < 0:
            self._scanning_device.unlock()
            self.unlock()
            return -1

        clock_status = self._scanning_device.set_up_scanner_clock(
            clock_frequency=self._clock_frequency)

        if clock_status < 0:
            self._scanning_device.unlock()
            self.unlock()
            self.set_position('scanner')
            return -1

        scanner_status = self._scanning_device.set_up_scanner()

        if scanner_status < 0:
            self._scanning_device.close_scanner_clock()
            self._scanning_device.unlock()
            self.unlock()
            self.set_position('scanner')
            return -1

        self.signal_scan_lines_next.emit()
        return 0

    def continue_scanner(self):
        """Continue the scanning procedure

        @return int: error code (0:OK, -1:error)
        """
        self.lock()
        self._scanning_device.lock()

        clock_status = self._scanning_device.set_up_scanner_clock(
            clock_frequency=self._clock_frequency)

        if clock_status < 0:
            self._scanning_device.unlock()
            self.unlock()
            self.set_position('scanner')
            return -1

        scanner_status = self._scanning_device.set_up_scanner()

        if scanner_status < 0:
            self._scanning_device.close_scanner_clock()
            self._scanning_device.unlock()
            self.unlock()
            self.set_position('scanner')
            return -1

        self.signal_scan_lines_next.emit()
        return 0

    def kill_scanner(self):
        """Closing the scanner device.

        @return int: error code (0:OK, -1:error)
        """
        try:
            self._scanning_device.close_scanner()
        except Exception as e:
            self.log.exception('Could not close the scanner.')
        try:
            self._scanning_device.close_scanner_clock()
        except Exception as e:
            self.log.exception('Could not close the scanner clock.')
        try:
            self._scanning_device.unlock()
        except Exception as e:
            self.log.exception('Could not unlock scanning device.')

        return 0

    def set_position(self, tag, x=None, y=None, z=None):
        """Forwarding the desired new position from the GUI to the scanning device.

        @param string tag: TODO

        @param float x: if defined, changes to postion in x-direction (microns)
        @param float y: if defined, changes to postion in y-direction (microns)
        @param float z: if defined, changes to postion in z-direction (microns)
        @param float a: if defined, changes to postion in a-direction (microns)

        @return int: error code (0:OK, -1:error)
        """
        # Changes the respective value
        if x is not None:
            self._current_x = x
        if y is not None:
            self._current_y = y
        if z is not None:
            self._current_z = z


        # Checks if the scanner is still running
        if self.getState() == 'locked' or self._scanning_device.getState() == 'locked':
            return -1
        else:
            self._change_position(tag)
            self.signal_change_position.emit(tag)
            return 0

    def _change_position(self, tag):
        """ Threaded method to change the hardware position.

        @return int: error code (0:OK, -1:error)
        """
        ch_array = ['x', 'y']
        pos_array = [self._current_x, self._current_y]
        pos_dict = {}

        #for i, ch in enumerate(self.get_scanner_axes()):
        for i in range(2):
            self.log.info(i)
            pos_dict[ch_array[i]] = pos_array[i]
 
        self._scanning_device.scanner_set_position(**pos_dict)
        return 0

    def get_position(self):
        """ Get position from scanning device.

        @return list: with three entries x, y and z denoting the current
                      position in meters
        """
        return self._scanning_device.get_scanner_position()

    def get_scanner_axes(self):
        """ Get axes from scanning device.
          @return list(str): names of scanner axes
        """
        return self._scanning_device.get_scanner_axes()

    def get_scanner_count_channels(self):
        """ Get lis of counting channels from scanning device.
          @return list(str): names of counter channels
        """
        return self._counter_device.get_scanner_count_channels()

    def _scan_line(self):
        """scanning an image xy

        """
        # stops scanning
        if self.stopRequested:
            with self.threadlock:
                self.kill_scanner()
                self.stopRequested = False
                self.unlock()
                self.signal_xy_image_updated.emit()
                self.set_position('scanner')


                self._xy_line_pos = self._scan_counter
                # add new history entry
                new_history = ConfocalHistoryEntry(self)
                new_history.snapshot(self)
                self.history.append(new_history)
                if len(self.history) > self.max_history_length:
                    self.history.pop(0)
                self.history_index = len(self.history) - 1
                return

        image = self.xy_image
        n_ch = len(self.get_scanner_axes())
        s_ch = len(self.get_scanner_count_channels())

        try:
            if self._scan_counter == 0:
                # make a line from the current cursor position to 
                # the starting position of the first scan line of the scan
                rs = self.return_slowness
                lsx = np.linspace(self._current_x, image[self._scan_counter, 0, 0], rs)
                lsy = np.linspace(self._current_y, image[self._scan_counter, 0, 1], rs)

                if n_ch <= 3:
                    start_line = np.vstack([lsx, lsy][0:n_ch])
                else:
                    start_line = np.vstack(
                        [lsx, lsy, np.ones(lsx.shape) * self._current_a])
                # move to the start position of the scan, counts are thrown away
                start_line_counts = self._scanning_device.scan_line(start_line)
                if np.any(start_line_counts == -1):
                    self.stopRequested = True
                    self.signal_scan_lines_next.emit()
                    return


            # make a line in the scan, _scan_counter says which one it is
            lsx = image[self._scan_counter, :, 0]
            lsy = image[self._scan_counter, :, 1]

            if n_ch <= 3:
                line = np.vstack([lsx, lsy][0:n_ch])


            # scan the line in the scan
            line_counts = self._scanning_device.scan_line(line)
            if np.any(line_counts == -1):
                self.stopRequested = True
                self.signal_scan_lines_next.emit()
                return

            # make a line to go to the starting position of the next scan line

            if n_ch <= 3:
                return_line = np.vstack([
                image[self._scan_counter, 0, 1] * np.ones(self._return_YL.shape),
                self._return_YL,
                        image[self._scan_counter, 0, 2] * np.ones(self._return_YL.shape)
                        ][0:n_ch])

 
            # return the scanner to the start of next line, counts are thrown away
            return_line_counts = self._scanning_device.scan_line(return_line)
            if np.any(return_line_counts == -1):
                self.stopRequested = True
                self.signal_scan_lines_next.emit()
                return

            # update image with counts from the line we just scanned
            self.xy_image[self._scan_counter, :, 3:3 + s_ch] = line_counts
            self.signal_xy_image_updated.emit()

            # next line in scan
            self._scan_counter += 1

            # stop scanning when last line scan was performed and makes scan not continuable
            if self._scan_counter >= np.size(self._image_vert_axis):
                if not self.permanent_scan:
                    self.stop_scanning()
                    self._xyscan_continuable = False
                else:
                    self._scan_counter = 0

            self.signal_scan_lines_next.emit()
        except:
            self.log.exception('The scan went wrong, killing the scanner.')
            self.stop_scanning()
            self.signal_scan_lines_next.emit()

    def save_xy_data(self, colorscale_range=None, percentile_range=None):
        """ Save the current confocal xy data to file.

        Two files are created.  The first is the imagedata, which has a text-matrix of count values
        corresponding to the pixel matrix of the image.  Only count-values are saved here.

        The second file saves the full raw data with x, y, z, and counts at every pixel.

        A figure is also saved.

        @param: list colorscale_range (optional) The range [min, max] of the display colour scale (for the figure)

        @param: list percentile_range (optional) The percentile range [min, max] of the color scale
        """
        save_time = datetime.now()

        filepath = self._save_logic.get_path_for_module(module_name='Confocal')

        # Prepare the metadata parameters (common to both saved files):
        parameters = OrderedDict()

        parameters['X image min (m)'] = self.image_x_range[0]
        parameters['X image max (m)'] = self.image_x_range[1]
        parameters['X image range (m)'] = self.image_x_range[1] - self.image_x_range[0]

        parameters['Y image min'] = self.image_y_range[0]
        parameters['Y image max'] = self.image_y_range[1]
        parameters['Y image range'] = self.image_y_range[1] - self.image_y_range[0]

        parameters['XY resolution (samples per range)'] = self.xy_resolution

        parameters['Clock frequency of scanner (Hz)'] = self._clock_frequency
        parameters['Return Slowness (Steps during retrace line)'] = self.return_slowness


        # Prepare a figure to be saved
        figure_data = self.xy_image[:, :, 3]
        image_extent = [
            self.image_x_range[0],
            self.image_x_range[1],
            self.image_y_range[0],
            self.image_y_range[1]
            ]
        axes = ['X', 'Y']
        crosshair_pos = [self.get_position()[0], self.get_position()[1]]

        figs = {
            ch: self.draw_figure(
                    data=self.xy_image[:, :, 3 + n],
                    image_extent=image_extent,
                    scan_axis=axes,
                    cbar_range=colorscale_range,
                    percentile_range=percentile_range,
                    crosshair_pos=crosshair_pos
                )
            for n, ch in enumerate(self.get_scanner_count_channels())
            }

        # Save the image data and figure
        for n, ch in enumerate(self.get_scanner_count_channels()):
            # data for the text-array "image":
            image_data = OrderedDict()
            image_data['Confocal pure XY scan image data without axis.\n'
                '# The upper left entry represents the signal at the upper left pixel position.\n'
                '# A pixel-line in the image corresponds to a row '
                'of entries where the Signal is in counts/s:'] = self.xy_image[:, :, 3 + n]

            filelabel = 'confocal_xy_image_{0}'.format(ch.replace('/', ''))
            self._save_logic.save_data(
                image_data,
                filepath,
                parameters=parameters,
                filelabel=filelabel,
                as_text=True,
                timestamp=save_time,
                precision=':.3e',
                plotfig=figs[ch]
                )
            plt.close(figs[ch])

        # prepare the full raw data in an OrderedDict:
        data = OrderedDict()
        data['x position (m)'] = self.xy_image[:, :, 0].flatten()
        data['y position (m)'] = self.xy_image[:, :, 1].flatten()

        for n, ch in enumerate(self.get_scanner_count_channels()):
            data['count rate {0} (Hz)'.format(ch)] = self.xy_image[:, :, 3 + n].flatten()

        # Save the raw data to file
        filelabel = 'confocal_xy_data'
        self._save_logic.save_data(
            data,
            filepath,
            parameters=parameters,
            filelabel=filelabel,
            as_text=True,
            precision=':.3e',
            timestamp=save_time
            )

        self.log.debug('Confocal Image saved to:\n{0}'.format(filepath))
        self.signal_xy_data_saved.emit()

    def draw_figure(self, data, image_extent, scan_axis=None, cbar_range=None, percentile_range=None,  crosshair_pos=None):
        """ Create a 2-D color map figure of the scan image.

        @param: array data: The NxM array of count values from a scan with NxM pixels.

        @param: list image_extent: The scan range in the form [hor_min, hor_max, ver_min, ver_max]

        @param: list axes: Names of the horizontal and vertical axes in the image

        @param: list cbar_range: (optional) [color_scale_min, color_scale_max].  If not supplied then a default of
                                 data_min to data_max will be used.

        @param: list percentile_range: (optional) Percentile range of the chosen cbar_range.

        @param: list crosshair_pos: (optional) crosshair position as [hor, vert] in the chosen image axes.

        @return: fig fig: a matplotlib figure object to be saved to file.
        """
        if scan_axis is None:
            scan_axis = ['X', 'Y']

        # If no colorbar range was given, take full range of data
        if cbar_range is None:
            cbar_range = [np.min(data), np.max(data)]

        # Scale color values using SI prefix
        prefix = ['', 'k', 'M', 'G']
        prefix_count = 0
        image_data = data
        draw_cb_range = np.array(cbar_range)

        while draw_cb_range[1] > 1000:
            image_data = image_data/1000
            draw_cb_range = draw_cb_range/1000
            prefix_count = prefix_count + 1

        c_prefix = prefix[prefix_count]

        # Use qudi style
        plt.style.use(self._save_logic.mpl_qd_style)

        # Create figure
        fig, ax = plt.subplots()

        # Create image plot
        cfimage = ax.imshow(image_data,
                            cmap=plt.get_cmap('inferno'), # reference the right place in qd
                            origin="lower",
                            vmin=draw_cb_range[0],
                            vmax=draw_cb_range[1],
                            interpolation='none',
                            extent=image_extent
                            )

        ax.set_aspect(1)
        ax.set_xlabel(scan_axis[0] + ' position (m)')
        ax.set_ylabel(scan_axis[1] + ' position (m)')
        ax.spines['bottom'].set_position(('outward', 10))
        ax.spines['left'].set_position(('outward', 10))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        # draw the crosshair position if defined
        if crosshair_pos is not None:
            trans_xmark = mpl.transforms.blended_transform_factory(
                ax.transData,
                ax.transAxes)

            trans_ymark = mpl.transforms.blended_transform_factory(
                ax.transAxes,
                ax.transData)

            ax.annotate('', xy=(crosshair_pos[0], 0), xytext=(crosshair_pos[0], -0.01), xycoords=trans_xmark,
                        arrowprops=dict(facecolor='#17becf', shrink=0.05),
                        )

            ax.annotate('', xy=(0, crosshair_pos[1]), xytext=(-0.01, crosshair_pos[1]), xycoords=trans_ymark,
                        arrowprops=dict(facecolor='#17becf', shrink=0.05),
                        )

        # Draw the colorbar
        cbar = plt.colorbar(cfimage, shrink=0.8)#, fraction=0.046, pad=0.08, shrink=0.75)
        cbar.set_label('Fluorescence (' + c_prefix + 'c/s)')

        # remove ticks from colorbar for cleaner image
        cbar.ax.tick_params(which=u'both', length=0)

        # If we have percentile information, draw that to the figure
        if percentile_range is not None:
            cbar.ax.annotate(str(percentile_range[0]),
                             xy=(-0.3, 0.0),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )
            cbar.ax.annotate(str(percentile_range[1]),
                             xy=(-0.3, 1.0),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )
            cbar.ax.annotate('(percentile)',
                             xy=(-0.3, 0.5),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )
        self.signal_draw_figure_completed.emit()
        return fig


    def step(self,axis,direction):
        self._scanning_device.step(axis,direction)




    def history_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.history[self.history_index].restore(self)
            self.signal_xy_image_updated.emit()
            self._change_position('history')
            self.signal_change_position.emit('history')
            self.signal_history_event.emit()

    def history_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.history[self.history_index].restore(self)
            self.signal_xy_image_updated.emit()
            self._change_position('history')
            self.signal_change_position.emit('history')
            self.signal_history_event.emit()
